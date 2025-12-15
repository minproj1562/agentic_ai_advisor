"""
Student Analysis API Endpoints with Firebase Integration
Real-time student performance analysis and ML predictions
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import (
    APIRouter, BackgroundTasks, Depends, HTTPException, Query, WebSocket, 
    Request, status
)
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.firebase_admin import firebase_manager
from app.dependencies import get_current_user, get_websocket_manager
from app.schemas.student_schemas import (
    StudentAnalysisResponse, 
    StudentDetailResponse,
    StudentListResponse
)
from app.services.ml_performance_analysis import MLPerformanceAnalyzer
from app.services.student_analysis_service import StudentAnalysisService
from app.utils.helpers import generate_csv, generate_excel, get_logger

logger = get_logger(__name__)
router = APIRouter()

# Initialize services
student_service = StudentAnalysisService()
ml_analyzer = MLPerformanceAnalyzer()


# Pydantic models for request validation
class StudentFilters(BaseModel):
    department: Optional[str] = None
    cgpa_min: Optional[float] = Field(None, ge=0, le=10)
    cgpa_max: Optional[float] = Field(None, ge=0, le=10)
    risk_level: Optional[str] = Field(None, regex="^(low|medium|high)$")
    semester: Optional[int] = Field(None, ge=1, le=10)

class BulkAnalysisRequest(BaseModel):
    department: Optional[str] = None
    semester: Optional[int] = Field(None, ge=1, le=10)
    analysis_types: List[str] = Field(default=["risk", "weaknesses"])


@router.get("/list", response_model=StudentListResponse)
async def get_students_analysis(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    department: Optional[str] = None,
    cgpa_min: Optional[float] = Query(None, ge=0, le=10),
    cgpa_max: Optional[float] = Query(None, ge=0, le=10),
    risk_level: Optional[str] = Query(None, regex="^(low|medium|high)$"),
    semester: Optional[int] = Query(None, ge=1, le=10),
    sort_by: str = Query("cgpa", regex="^(cgpa|name|risk_score|attendance)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get comprehensive student analysis list with real-time Firebase data
    """
    try:
        # Build filters for Firebase query
        filters = []
        
        if department:
            filters.append({"field": "department", "operator": "==", "value": department})
        
        if cgpa_min is not None:
            filters.append({"field": "cgpa", "operator": ">=", "value": cgpa_min})
        
        if cgpa_max is not None:
            filters.append({"field": "cgpa", "operator": "<=", "value": cgpa_max})
        
        if risk_level:
            filters.append({"field": "risk_level", "operator": "==", "value": risk_level})
        
        if semester:
            filters.append({"field": "current_semester", "operator": "==", "value": semester})
        
        # Fetch from Firebase
        students_data = await firebase_manager.get_collection(
            collection="students",
            filters=filters,
            order_by=sort_by,
            order_direction=sort_order,
            limit=limit,
            offset=skip
        )
        
        # Get total count for pagination
        total_count = await firebase_manager.get_collection_count(
            collection="students",
            filters=filters
        )
        
        # Process each student with ML analysis
        analyzed_students = []
        
        for student in students_data:
            try:
                # Get performance data from subcollection
                performance_data = await firebase_manager.get_collection(
                    collection=f"students/{student['id']}/performance",
                    order_by="semester",
                    order_direction="asc"
                )
                
                # Get weaknesses
                weaknesses = await firebase_manager.get_collection(
                    collection=f"students/{student['id']}/weaknesses",
                    filters=[{"field": "status", "operator": "==", "value": "active"}],
                    limit=5
                )
                
                # Run ML predictions
                ml_predictions = await ml_analyzer.predict_performance(
                    student_data=student,
                    performance_history=performance_data
                )
                
                # Combine data
                analysis = {
                    **student,
                    "sgpa_trend": [p["sgpa"] for p in performance_data] if performance_data else [],
                    "latest_sgpa": performance_data[-1]["sgpa"] if performance_data else 0.0,
                    "weaknesses": weaknesses,
                    "weakness_count": len(weaknesses),
                    "risk_score": ml_predictions.get("risk_score", 0),
                    "improvement_trend": ml_predictions.get("trend", "stable"),
                    "predictions": ml_predictions
                }
                
                analyzed_students.append(analysis)
            except Exception as student_error:
                logger.error(f"Error processing student {student.get('id', 'unknown')}: {str(student_error)}")
                continue
        
        logger.info(f"Fetched analysis for {len(analyzed_students)} students")
        
        return StudentListResponse(
            students=analyzed_students,
            pagination={
                "skip": skip,
                "limit": limit,
                "total": total_count,
                "has_more": (skip + limit) < total_count
            }
        )
        
    except Exception as e:
        logger.error(f"Error fetching student analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Internal server error while fetching student analysis"
        )


@router.get("/{student_id}", response_model=StudentDetailResponse)
async def get_student_detailed_analysis(
    student_id: str,
    include_predictions: bool = Query(True),
    include_recommendations: bool = Query(True),
    time_range: Optional[str] = Query("all", regex="^(all|current|last_year)$"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get detailed analysis for a specific student with ML predictions
    """
    try:
        # Fetch student data from Firebase
        student = await firebase_manager.get_document(
            collection="students",
            document_id=student_id
        )
        
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Student not found"
            )
        
        # Fetch subcollections
        performance_data = await firebase_manager.get_collection(
            collection=f"students/{student_id}/performance",
            order_by="semester",
            order_direction="asc"
        )
        
        weaknesses = await firebase_manager.get_collection(
            collection=f"students/{student_id}/weaknesses",
            filters=[{"field": "status", "operator": "==", "value": "active"}]
        )
        
        recommendations = await firebase_manager.get_collection(
            collection=f"students/{student_id}/recommendations",
            order_by="created_at",
            order_direction="desc"
        )
        
        # Filter performance data based on time range
        filtered_performance_data = performance_data
        
        if time_range == "current":
            filtered_performance_data = [
                p for p in performance_data 
                if p.get("semester") == student.get("current_semester")
            ]
        elif time_range == "last_year":
            one_year_ago = datetime.utcnow() - timedelta(days=365)
            filtered_performance_data = [
                p for p in performance_data 
                if p.get("created_at") and 
                datetime.fromisoformat(p["created_at"].replace('Z', '+00:00')) > one_year_ago
            ]
        
        # ML predictions if requested
        predictions = {}
        if include_predictions:
            predictions = await ml_analyzer.deep_analysis(
                student_data=student,
                performance_history=filtered_performance_data,
                weaknesses=weaknesses
            )
        
        # Generate recommendations if requested and none exist
        final_recommendations = recommendations
        if include_recommendations and not final_recommendations:
            final_recommendations = await student_service.generate_recommendations(
                student=student,
                performance_data=filtered_performance_data,
                predictions=predictions
            )
            
            # Save recommendations to Firebase
            for rec in final_recommendations:
                await firebase_manager.create_document(
                    collection=f"students/{student_id}/recommendations",
                    data={
                        **rec,
                        "created_at": datetime.utcnow().isoformat(),
                        "status": "pending"
                    }
                )
        
        # Calculate statistics
        statistics = await student_service.calculate_statistics(filtered_performance_data)
        
        # Prepare response
        response_data = {
            **student,
            "performance_data": {
                "sgpa_trend": [
                    {"semester": p.get("semester", 0), "sgpa": p.get("sgpa", 0.0)} 
                    for p in filtered_performance_data
                ],
                "attendance_trend": [
                    {"semester": p.get("semester", 0), "attendance": p.get("attendance", 0)} 
                    for p in filtered_performance_data
                ],
                "statistics": statistics
            },
            "predictions": predictions,
            "recommendations": final_recommendations,
            "analysis_metadata": {
                "version": "2.0",
                "timestamp": datetime.utcnow().isoformat(),
                "confidence": predictions.get("confidence", 0)
            }
        }
        
        return StudentDetailResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in detailed analysis for {student_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during student analysis"
        )


@router.post("/{student_id}/weakness-analysis")
async def trigger_weakness_analysis(
    student_id: str,
    background_tasks: BackgroundTasks,
    force_refresh: bool = Query(False),
    current_user: dict = Depends(get_current_user),
):
    """
    Trigger deep weakness analysis using ML models
    """
    try:
        # Verify student exists
        student = await firebase_manager.get_document(
            collection="students",
            document_id=student_id
        )
        
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        
        # Check if analysis is already running
        analysis_status = await firebase_manager.get_document(
            collection="analysis_jobs",
            document_id=f"{student_id}_weakness"
        )
        
        if analysis_status and analysis_status.get("status") == "running":
            return {
                "status": "already_running",
                "job_id": analysis_status.get("job_id"),
                "message": "Analysis already in progress"
            }
        
        # Create job record
        job_id = f"weakness_{student_id}_{int(datetime.utcnow().timestamp())}"
        
        await firebase_manager.create_document(
            collection="analysis_jobs",
            document_id=f"{student_id}_weakness",
            data={
                "job_id": job_id,
                "student_id": student_id,
                "type": "weakness_analysis",
                "status": "running",
                "progress": 0,
                "created_by": current_user.get("uid", "unknown"),
                "force_refresh": force_refresh,
                "created_at": datetime.utcnow().isoformat()
            }
        )
        
        # Add to background tasks
        background_tasks.add_task(
            run_weakness_analysis_task,
            student_id,
            job_id,
            force_refresh
        )
        
        return {
            "status": "initiated",
            "job_id": job_id,
            "estimated_time": "2-3 minutes",
            "check_status_url": f"/api/v1/student-analysis/{student_id}/analysis-status"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to initiate weakness analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate weakness analysis"
        )


async def run_weakness_analysis_task(student_id: str, job_id: str, force_refresh: bool):
    """
    Background task for weakness analysis
    """
    try:
        # Update progress
        await firebase_manager.update_document(
            collection="analysis_jobs",
            document_id=f"{student_id}_weakness",
            data={"progress": 10}
        )
        
        # Fetch student data
        student = await firebase_manager.get_document(
            collection="students",
            document_id=student_id
        )
        
        performance_data = await firebase_manager.get_collection(
            collection=f"students/{student_id}/performance"
        )
        
        assessments = await firebase_manager.get_collection(
            collection=f"students/{student_id}/assessments"
        )
        
        # Update progress
        await firebase_manager.update_document(
            collection="analysis_jobs",
            document_id=f"{student_id}_weakness",
            data={"progress": 30}
        )
        
        # Run ML analysis
        weaknesses = await ml_analyzer.detect_weaknesses(
            student_data=student,
            performance_history=performance_data,
            assessments=assessments,
            force_refresh=force_refresh
        )
        
        # Update progress
        await firebase_manager.update_document(
            collection="analysis_jobs",
            document_id=f"{student_id}_weakness",
            data={"progress": 70}
        )
        
        # Clear existing active weaknesses
        existing_weaknesses = await firebase_manager.get_collection(
            collection=f"students/{student_id}/weaknesses",
            filters=[{"field": "status", "operator": "==", "value": "active"}]
        )
        
        batch_operations = []
        
        # Archive existing weaknesses
        for weakness in existing_weaknesses:
            batch_operations.append({
                "type": "update",
                "collection": f"students/{student_id}/weaknesses",
                "document_id": weakness["id"],
                "data": {"status": "archived", "archived_at": datetime.utcnow().isoformat()}
            })
        
        # Add new weaknesses
        for weakness in weaknesses:
            weakness_id = f"weakness_{int(datetime.utcnow().timestamp())}_{len(batch_operations)}"
            batch_operations.append({
                "type": "create",
                "collection": f"students/{student_id}/weaknesses",
                "document_id": weakness_id,
                "data": {
                    **weakness,
                    "id": weakness_id,
                    "status": "active",
                    "created_at": datetime.utcnow().isoformat(),
                    "analysis_job_id": job_id
                }
            })
        
        if batch_operations:
            await firebase_manager.batch_write(batch_operations)
        
        # Update progress and mark as completed
        await firebase_manager.update_document(
            collection="analysis_jobs",
            document_id=f"{student_id}_weakness",
            data={
                "progress": 100,
                "status": "completed",
                "completed_at": datetime.utcnow().isoformat(),
                "result": {
                    "weaknesses_found": len(weaknesses),
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        )
        
        # Send real-time notification
        await send_realtime_update(
            student_id,
            {
                "type": "weakness_analysis_complete",
                "weaknesses_found": len(weaknesses),
                "job_id": job_id
            }
        )
        
    except Exception as e:
        logger.error(f"Weakness analysis task failed: {str(e)}")
        
        await firebase_manager.update_document(
            collection="analysis_jobs",
            document_id=f"{student_id}_weakness",
            data={
                "status": "failed",
                "error": str(e),
                "failed_at": datetime.utcnow().isoformat()
            }
        )


@router.get("/{student_id}/analysis-status")
async def get_analysis_status(
    student_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Check the status of ongoing analysis
    """
    try:
        status_data = await firebase_manager.get_document(
            collection="analysis_jobs",
            document_id=f"{student_id}_weakness"
        )
        
        if not status_data:
            return {"status": "not_found"}
        
        return status_data
        
    except Exception as e:
        logger.error(f"Error getting analysis status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get analysis status"
        )


@router.get("/trends/department/{department}")
async def get_department_trends(
    department: str,
    semester: Optional[int] = None,
    metric: str = Query("cgpa", regex="^(cgpa|attendance|assignments)$"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get aggregated trends for a department with real-time data
    """
    try:
        # Build filters
        filters = [{"field": "department", "operator": "==", "value": department}]
        
        if semester:
            filters.append({"field": "current_semester", "operator": "==", "value": semester})
        
        # Fetch students
        students = await firebase_manager.get_collection(
            collection="students",
            filters=filters
        )
        
        if not students:
            return {
                "department": department,
                "trends": {},
                "real_time": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "student_count": 0,
                    "data_freshness": "live"
                }
            }
        
        # Calculate trends based on metric
        trends = await student_service.calculate_department_trends(
            students=students,
            metric=metric
        )
        
        # Add real-time statistics
        trends["real_time"] = {
            "timestamp": datetime.utcnow().isoformat(),
            "student_count": len(students),
            "data_freshness": "live"
        }
        
        return trends
        
    except Exception as e:
        logger.error(f"Error fetching department trends: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch department trends"
        )


@router.post("/bulk-analysis")
async def trigger_bulk_analysis(
    request: BulkAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """
    Trigger bulk analysis for multiple students
    """
    try:
        # Admin only endpoint
        if current_user.get("role") not in ["admin", "faculty"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        job_id = f"bulk_{int(datetime.utcnow().timestamp())}"
        
        # Create job record
        await firebase_manager.create_document(
            collection="bulk_jobs",
            document_id=job_id,
            data={
                "job_id": job_id,
                "request": request.dict(),
                "status": "initiated",
                "created_by": current_user.get("uid", "unknown"),
                "progress": 0,
                "created_at": datetime.utcnow().isoformat()
            }
        )
        
        # Add to background tasks
        background_tasks.add_task(
            run_bulk_analysis_task,
            job_id,
            request.dict()
        )
        
        return {
            "job_id": job_id,
            "status": "initiated",
            "check_status_url": f"/api/v1/student-analysis/bulk-status/{job_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to initiate bulk analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate bulk analysis"
        )


async def run_bulk_analysis_task(job_id: str, request: Dict[str, Any]):
    """
    Background task for bulk analysis
    """
    try:
        # Get students based on criteria
        filters = []
        
        if request.get("department"):
            filters.append({"field": "department", "operator": "==", "value": request["department"]})
        
        if request.get("semester"):
            filters.append({"field": "current_semester", "operator": "==", "value": request["semester"]})
        
        students = await firebase_manager.get_collection(
            collection="students",
            filters=filters
        )
        
        total_students = len(students)
        analyzed_count = 0
        
        for student in students:
            try:
                # Analyze each student
                performance_data = await firebase_manager.get_collection(
                    collection=f"students/{student['id']}/performance"
                )
                
                predictions = await ml_analyzer.quick_predict(
                    student_data=student,
                    performance_history=performance_data
                )
                
                # Update student record with predictions
                await firebase_manager.update_document(
                    collection="students",
                    document_id=student["id"],
                    data={
                        "risk_score": predictions.get("risk_score", 0),
                        "last_analysis": datetime.utcnow().isoformat(),
                        "improvement_trend": predictions.get("trend", "stable")
                    }
                )
                
                analyzed_count += 1
                
                # Update progress
                progress = int((analyzed_count / total_students) * 100) if total_students > 0 else 100
                await firebase_manager.update_document(
                    collection="bulk_jobs",
                    document_id=job_id,
                    data={"progress": progress}
                )
                
            except Exception as student_error:
                logger.error(f"Error analyzing student {student.get('id')}: {str(student_error)}")
                continue
        
        # Final update
        await firebase_manager.update_document(
            collection="bulk_jobs",
            document_id=job_id,
            data={
                "status": "completed",
                "progress": 100,
                "completed_at": datetime.utcnow().isoformat(),
                "result": {
                    "total_students": total_students,
                    "analyzed_count": analyzed_count,
                    "failed_count": total_students - analyzed_count,
                    "completed_at": datetime.utcnow().isoformat()
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Bulk analysis task failed: {str(e)}")
        
        await firebase_manager.update_document(
            collection="bulk_jobs",
            document_id=job_id,
            data={
                "status": "failed",
                "error": str(e),
                "failed_at": datetime.utcnow().isoformat()
            }
        )


@router.get("/bulk-status/{job_id}")
async def get_bulk_analysis_status(
    job_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Check the status of bulk analysis job
    """
    try:
        status_data = await firebase_manager.get_document(
            collection="bulk_jobs",
            document_id=job_id
        )
        
        if not status_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        return status_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting bulk analysis status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get bulk analysis status"
        )


@router.get("/export/{format}")
async def export_analysis_data(
    format: str,  # ✅ CORRECT - path parameter (no Query())
    department: Optional[str] = Query(None),  # ✅ CORRECT - query parameter
    current_user: dict = Depends(get_current_user),
):
    """
    Export analysis data in various formats
    """
    # Validate format manually since we can't use Query regex validation
    if format not in ["csv", "excel", "json"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format must be one of: csv, excel, json"
        )
    
    try:
        # Build filters
        filters = []
        if department:
            filters.append({"field": "department", "operator": "==", "value": department})
        
        # Fetch data
        students = await firebase_manager.get_collection(
            collection="students",
            filters=filters,
            limit=1000  # Limit for export
        )
        
        if not students:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No data found for export"
            )
        
        if format == "csv":
            csv_data = generate_csv(students)
            return StreamingResponse(
                csv_data,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=student_analysis_{datetime.utcnow().date()}.csv"}
            )
            
        elif format == "excel":
            excel_data = generate_excel(students)
            return StreamingResponse(
                excel_data,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename=student_analysis_{datetime.utcnow().date()}.xlsx"}
            )
            
        else:  # JSON
            return {
                "data": students,
                "exported_at": datetime.utcnow().isoformat(),
                "record_count": len(students)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Export failed"
        )     
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Export failed"
        )


@router.websocket("/ws/{student_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    student_id: str,
    ws_manager=Depends(get_websocket_manager),
):
    """
    WebSocket endpoint for real-time student updates
    """
    await ws_manager.connect(websocket, student_id)
    
    heartbeat_task = None
    
    try:
        # Authenticate WebSocket connection
        await authenticate_websocket(websocket, student_id)
        
        # Heartbeat mechanism
        async def heartbeat():
            while True:
                await asyncio.sleep(30)
                try:
                    await websocket.send_json({"type": "heartbeat", "timestamp": datetime.utcnow().isoformat()})
                except Exception:
                    break
        
        heartbeat_task = asyncio.create_task(heartbeat())
        
        # Setup Firebase listener for real-time updates
        def on_student_update(data):
            asyncio.create_task(
                ws_manager.send_personal_message(
                    json.dumps(data),
                    student_id
                )
            )
        
        # Listen to student document changes
        listener = await firebase_manager.setup_realtime_listener(
            collection="students",
            document_id=student_id,
            callback=on_student_update
        )
        
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            
            if data == "ping":
                await websocket.send_text("pong")
            elif data == "get_update":
                # Fetch latest data
                student = await firebase_manager.get_document(
                    collection="students",
                    document_id=student_id
                )
                if student:
                    await websocket.send_json({
                        "type": "student_update",
                        "data": student,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
    except Exception as e:
        logger.error(f"WebSocket error for student {student_id}: {str(e)}")
    finally:
        if heartbeat_task:
            heartbeat_task.cancel()
        ws_manager.disconnect(student_id)


async def authenticate_websocket(websocket: WebSocket, student_id: str):
    """
    Authenticate WebSocket connection
    """
    # Implement your WebSocket authentication logic here
    # This could involve checking tokens, session cookies, etc.
    try:
        # For now, accept all connections - implement proper auth in production
        return True
    except Exception as e:
        await websocket.close(code=1008)
        raise


async def send_realtime_update(student_id: str, data: Dict[str, Any]):
    """
    Send real-time update to connected clients
    """
    try:
        # Update Firebase (triggers listeners)
        await firebase_manager.create_document(
            collection="realtime_updates",
            document_id=f"{student_id}_{int(datetime.utcnow().timestamp())}",
            data={
                "student_id": student_id,
                "update": data,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Failed to send realtime update: {str(e)}")