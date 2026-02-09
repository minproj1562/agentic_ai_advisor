# app/api/v1/endpoints/faculty_profile.py
"""
Faculty Profile Management Endpoints - COMPLETE & FIXED
Handles CV upload, parsing, profile setup, editing, and student views
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import uuid

from app.core.security import get_current_user, FirebaseUser
from app.models.faculty import (
    Faculty, 
    FacultyStatus,
    ProfileUpdateRequest, 
    UniformFacultyProfile,
    PersonalInfo,
    AcademicQualifications,
    CurrentPosition,
    ResearchExpertise,
    TeachingInfo,
    FacultyAvailability,
    PublicationSummary,
    Degree,
    MeetingSlot,
    VisibilitySettings as ModelVisibilitySettings
)
from app.services.cv_parser_v2 import EnhancedCVParser
from app.services.cv_analysis_service import cv_analysis_service
from app.schemas.faculty_schemas import (
    ProfileSetupRequest,
    ProfileUpdateRequest,
    FacultyProfileResponse,
    CVUploadResponse,
    FacultyStudentView,
    ProfileCompletenessResponse,
    AvailabilityUpdateRequest,
    MeetingSlotInput,
    SetupStatusResponse,
    VisibilitySettings,
    FieldVisibility,
    CVReuploadRequest,
    FacultyBasicInfo
)
from app.core.firebase_admin import firebase_manager

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== Helper Functions ====================

def build_meeting_slots(slots: List[MeetingSlotInput]) -> List[MeetingSlot]:
    """Convert input slots to model slots"""
    return [
        MeetingSlot(
            day=slot.day,
            start_time=slot.start_time,
            end_time=slot.end_time,
            venue=slot.venue,
            is_available=True
        )
        for slot in slots
    ]


def apply_visibility_filter(
    profile_data: Dict[str, Any],
    visibility: Optional[ModelVisibilitySettings],
    requester_department: Optional[str] = None
) -> Dict[str, Any]:
    """Apply visibility settings to profile data for student view"""
    if not visibility:
        # Default: hide phone, show everything else
        profile_data.pop('phone', None)
        return profile_data
    
    # Check each field
    if visibility.phone == FieldVisibility.PRIVATE:
        profile_data.pop('phone', None)
    elif visibility.phone == FieldVisibility.DEPARTMENT:
        if not requester_department or requester_department != profile_data.get('department'):
            profile_data.pop('phone', None)
    
    if visibility.email == FieldVisibility.PRIVATE:
        profile_data.pop('email', None)
    
    if visibility.office_location == FieldVisibility.PRIVATE:
        profile_data.pop('office_location', None)
    
    return profile_data


# ==================== CV Upload & Parsing ====================

@router.post("/cv/upload", response_model=CVUploadResponse)
async def upload_and_parse_cv(
    cv: UploadFile = File(...),
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Upload CV and parse using pdfplumber + sentence-transformers.
    Returns suggested profile data for auto-fill.
    """
    try:
        # Validate file type
        if not cv.content_type == "application/pdf":
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Validate file size (10MB max)
        content = await cv.read()
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size must be less than 10MB")
        
        user_id = current_user.uid
        user_email = current_user.email
        
        # Parse CV using analysis service
        logger.info(f"Parsing CV for user {user_id}")
        parsed_result, suggested_profile = await cv_analysis_service.analyze_cv(
            content, cv.filename, user_id, user_email
        )
        
        # Upload to Firebase Storage
        cv_url = None
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            file_path = f"faculty_cvs/{user_id}/{timestamp}_{cv.filename}"
            
            cv_url = await firebase_manager.upload_file(
                file_path=file_path,
                file_data=content,
                content_type="application/pdf",
                metadata={
                    "user_id": user_id,
                    "uploaded_at": datetime.utcnow().isoformat()
                }
            )
            logger.info(f"CV uploaded to Firebase: {file_path}")
        except Exception as e:
            logger.warning(f"Firebase upload failed: {e}")
        
        # Get or create faculty document
        faculty = await Faculty.find_one(Faculty.user_id == user_id)
        
        if not faculty:
            # Extract name from CV or use email prefix
            extracted_name = parsed_result.get('personal_info', {}).get('name')
            faculty = Faculty(
                user_id=user_id,
                name=extracted_name or user_email.split('@')[0],
                email=user_email,
                department="",
                designation="Faculty",
                status=FacultyStatus.PENDING_SETUP
            )
        
        # Update faculty with CV data
        faculty = await cv_analysis_service.update_faculty_from_cv(
            faculty, parsed_result, suggested_profile, cv_url, cv.filename
        )
        
        # Get extraction warnings and confidence
        warnings = cv_analysis_service.get_extraction_warnings(parsed_result)
        confidence = cv_analysis_service.calculate_extraction_confidence(parsed_result)
        
        return CVUploadResponse(
            success=True,
            cv_url=cv_url,
            file_name=cv.filename,
            parsed_data={
                "text_length": len(parsed_result.get('text', '')),
                "word_count": parsed_result.get('word_count', 0),
                "sections_found": list(parsed_result.get('sections', {}).keys()),
                "quality_score": parsed_result.get('quality_score', 0)
            },
            suggested_profile=parsed_result.get('suggested_profile', {}),
            extraction_warnings=warnings,
            confidence=confidence,
            message="CV uploaded and analyzed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CV upload error for user {current_user.uid}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"CV processing failed: {str(e)}")


@router.post("/cv/reupload")
async def reupload_cv(
    cv: UploadFile = File(...),
    merge_mode: str = Query("smart", description="Merge mode: smart, overwrite, keep_existing"),
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Re-upload CV with merge options for existing profile.
    """
    try:
        # Validate
        if not cv.content_type == "application/pdf":
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        content = await cv.read()
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size must be less than 10MB")
        
        user_id = current_user.uid
        
        # Get existing faculty
        faculty = await Faculty.find_one(Faculty.user_id == user_id)
        if not faculty:
            raise HTTPException(status_code=404, detail="Faculty profile not found")
        
        # Parse new CV
        parsed_result, suggested_profile = await cv_analysis_service.analyze_cv(
            content, cv.filename, user_id, current_user.email
        )
        
        # Upload new CV
        cv_url = None
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            file_path = f"faculty_cvs/{user_id}/{timestamp}_{cv.filename}"
            cv_url = await firebase_manager.upload_file(
                file_path=file_path,
                file_data=content,
                content_type="application/pdf"
            )
        except Exception as e:
            logger.warning(f"Firebase upload failed: {e}")
        
        # Apply merge based on mode
        if merge_mode == "overwrite":
            # Replace entire profile
            faculty = await cv_analysis_service.update_faculty_from_cv(
                faculty, parsed_result, suggested_profile, cv_url, cv.filename
            )
        elif merge_mode == "keep_existing":
            # Only update CV metadata, don't touch profile
            faculty.cv_url = cv_url
            faculty.cv_file_name = cv.filename
            faculty.cv_uploaded_at = datetime.utcnow()
            faculty.cv_parsed_data = parsed_result
            await faculty.save()
        else:  # smart mode - fill empty fields only
            # Only update empty fields
            if faculty.uniform_profile:
                sp = parsed_result.get('suggested_profile', {})
                
                # Update empty research areas
                if not faculty.uniform_profile.research_expertise.primary_areas:
                    if sp.get('research_expertise', {}).get('primary_areas'):
                        faculty.uniform_profile.research_expertise.primary_areas = sp['research_expertise']['primary_areas']
                
                # Update empty skills/keywords
                if not faculty.uniform_profile.research_expertise.keywords:
                    if sp.get('research_expertise', {}).get('keywords'):
                        faculty.uniform_profile.research_expertise.keywords = sp['research_expertise']['keywords']
                
                # Add any new publications
                if sp.get('publications', {}).get('total_count', 0) > 0:
                    if not faculty.uniform_profile.publications:
                        faculty.uniform_profile.publications = PublicationSummary(
                            total_count=sp['publications'].get('total_count', 0),
                            journal_papers=sp['publications'].get('journal_papers', 0),
                            conference_papers=sp['publications'].get('conference_papers', 0),
                            notable_works=sp['publications'].get('notable_works', [])
                        )
            
            faculty.cv_url = cv_url
            faculty.cv_file_name = cv.filename
            faculty.cv_uploaded_at = datetime.utcnow()
            faculty.cv_parsed_data = parsed_result
            await faculty.save()
        
        return {
            "success": True,
            "cv_url": cv_url,
            "merge_mode": merge_mode,
            "message": f"CV re-uploaded successfully with '{merge_mode}' merge mode"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CV reupload error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Profile Setup ====================

@router.post("/setup")
async def complete_profile_setup(
    profile_data: ProfileSetupRequest,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Complete faculty profile setup with form data.
    Creates the UniformFacultyProfile structure.
    """
    try:
        user_id = current_user.uid
        
        # Get existing faculty or create new
        faculty = await Faculty.find_one(Faculty.user_id == user_id)
        
        if not faculty:
            faculty = Faculty(
                user_id=user_id,
                name=profile_data.name or current_user.email.split('@')[0],
                email=current_user.email,
                department=profile_data.department,
                designation=profile_data.designation
            )
        
        # Build all degrees list
        all_degrees = []
        for deg in profile_data.all_degrees:
            all_degrees.append(Degree(
                degree=deg.degree,
                field=deg.field,
                institution=deg.institution,
                year=deg.year,
                thesis_title=deg.thesis_title
            ))
        
        # Add main degree if not in list
        if not any(d.degree == profile_data.highest_degree for d in all_degrees):
            all_degrees.insert(0, Degree(
                degree=profile_data.highest_degree,
                field=profile_data.specialization,
                institution=profile_data.graduation_university,
                year=profile_data.graduation_year
            ))
        
        # Build meeting slots
        meeting_slots = build_meeting_slots(profile_data.available_slots)
        
        # Build visibility settings
        visibility = None
        if profile_data.visibility:
            visibility = ModelVisibilitySettings(
                phone=profile_data.visibility.phone,
                email=profile_data.visibility.email,
                office_location=profile_data.visibility.office_location
            )
        
        # Build UniformFacultyProfile
        uniform_profile = UniformFacultyProfile(
            personal_info=PersonalInfo(
                name=profile_data.name or faculty.name,
                email=current_user.email,
                phone=profile_data.phone,
                photo_url=profile_data.photo_url
            ),
            academic_qualifications=AcademicQualifications(
                highest_degree=profile_data.highest_degree,
                specialization=profile_data.specialization,
                university=profile_data.graduation_university,
                graduation_year=profile_data.graduation_year,
                all_degrees=all_degrees
            ),
            current_position=CurrentPosition(
                designation=profile_data.designation,
                department=profile_data.department,
                institution=profile_data.institution,
                years_of_experience=profile_data.years_of_experience,
                joining_year=profile_data.joining_year
            ),
            research_expertise=ResearchExpertise(
                primary_areas=profile_data.primary_research_areas[:5],
                secondary_interests=profile_data.secondary_interests,
                keywords=profile_data.research_keywords
            ),
            teaching=TeachingInfo(
                current_subjects=profile_data.current_subjects,
                past_subjects=profile_data.past_subjects,
                preferred_areas=profile_data.preferred_teaching_areas
            ),
            availability=FacultyAvailability(
                office_location=profile_data.office_location,
                office_hours=profile_data.office_hours,
                available_slots=meeting_slots,
                preferred_meeting_duration=profile_data.preferred_meeting_duration
            ),
            others={
                "awards": profile_data.awards,
                "patents": profile_data.patents,
                "certifications": profile_data.certifications,
                "industry_experience": profile_data.industry_experience,
                "professional_memberships": profile_data.professional_memberships,
                "languages": profile_data.languages
            },
            visibility=visibility
        )
        
        # Add publications if provided
        if profile_data.total_publications > 0:
            uniform_profile.publications = PublicationSummary(
                total_count=profile_data.total_publications,
                journal_papers=profile_data.journal_papers,
                conference_papers=profile_data.conference_papers,
                notable_works=profile_data.notable_works,
                h_index=profile_data.h_index
            )
        
        # Update faculty document - FIX: Use proper name
        faculty.name = profile_data.name or faculty.name  # FIXED: Was incorrectly using phone
        faculty.department = profile_data.department
        faculty.designation = profile_data.designation
        faculty.phone = profile_data.phone
        faculty.office_location = profile_data.office_location
        faculty.years_of_experience = profile_data.years_of_experience
        faculty.teaching_subjects = profile_data.current_subjects
        faculty.specializations = profile_data.primary_research_areas
        faculty.skills = profile_data.research_keywords
        faculty.available_slots = meeting_slots
        
        faculty.uniform_profile = uniform_profile
        faculty.profile_setup_complete = True
        faculty.status = FacultyStatus.ACTIVE
        faculty.updated_at = datetime.utcnow()
        
        # Calculate profile completeness
        faculty.uniform_profile.profile_completeness = faculty.calculate_profile_completeness()
        
        await faculty.save()
        
        logger.info(f"Profile setup completed for faculty {user_id}")
        
        return {
            "success": True,
            "message": "Profile setup completed successfully",
            "profile_completeness": faculty.uniform_profile.profile_completeness,
            "status": faculty.status.value
        }
        
    except Exception as e:
        logger.error(f"Profile setup error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Profile setup failed: {str(e)}")


# ==================== Profile Update (Edit) ====================

@router.put("/update")
async def update_profile(
    updates: ProfileUpdateRequest,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Update faculty profile. Only provided fields are updated.
    """
    try:
        user_id = current_user.uid
        faculty = await Faculty.find_one(Faculty.user_id == user_id)
        
        if not faculty:
            raise HTTPException(status_code=404, detail="Faculty profile not found")
        
        if not faculty.profile_setup_complete:
            raise HTTPException(
                status_code=400, 
                detail="Please complete initial profile setup first"
            )
        
        # Track if major changes (for approval workflow)
        major_changes = []
        updates_made = []
        
        # Update personal info
        if faculty.uniform_profile:
            profile = faculty.uniform_profile
            
            # Personal info updates
            if updates.name and updates.name != profile.personal_info.name:
                profile.personal_info.name = updates.name
                faculty.name = updates.name
                updates_made.append("name")
            if updates.phone is not None:
                profile.personal_info.phone = updates.phone
                faculty.phone = updates.phone
                updates_made.append("phone")
            if updates.photo_url is not None:
                profile.personal_info.photo_url = updates.photo_url
                updates_made.append("photo")
            
            # Academic updates
            if updates.highest_degree and updates.highest_degree != profile.academic_qualifications.highest_degree:
                profile.academic_qualifications.highest_degree = updates.highest_degree
                updates_made.append("degree")
            if updates.specialization:
                profile.academic_qualifications.specialization = updates.specialization
                updates_made.append("specialization")
            if updates.graduation_university:
                profile.academic_qualifications.university = updates.graduation_university
            if updates.graduation_year:
                profile.academic_qualifications.graduation_year = updates.graduation_year
            if updates.all_degrees is not None:
                profile.academic_qualifications.all_degrees = [
                    Degree(
                        degree=d.degree,
                        field=d.field,
                        institution=d.institution,
                        year=d.year,
                        thesis_title=d.thesis_title
                    ) for d in updates.all_degrees
                ]
                updates_made.append("degrees")
            
            # Position updates (major changes)
            if updates.designation and updates.designation != profile.current_position.designation:
                major_changes.append("designation")
                profile.current_position.designation = updates.designation
                faculty.designation = updates.designation
                updates_made.append("designation")
            if updates.department and updates.department != profile.current_position.department:
                major_changes.append("department")
                profile.current_position.department = updates.department
                faculty.department = updates.department
                updates_made.append("department")
            if updates.institution:
                profile.current_position.institution = updates.institution
            if updates.years_of_experience is not None:
                profile.current_position.years_of_experience = updates.years_of_experience
                faculty.years_of_experience = updates.years_of_experience
            if updates.joining_year is not None:
                profile.current_position.joining_year = updates.joining_year
            
            # Research updates
            if updates.primary_research_areas is not None:
                profile.research_expertise.primary_areas = updates.primary_research_areas[:5]
                faculty.specializations = updates.primary_research_areas
                updates_made.append("research_areas")
            if updates.secondary_interests is not None:
                profile.research_expertise.secondary_interests = updates.secondary_interests
            if updates.research_keywords is not None:
                profile.research_expertise.keywords = updates.research_keywords
                faculty.skills = updates.research_keywords
                updates_made.append("keywords")
            
            # Teaching updates
            if updates.current_subjects is not None:
                profile.teaching.current_subjects = updates.current_subjects
                faculty.teaching_subjects = updates.current_subjects
                updates_made.append("subjects")
            if updates.past_subjects is not None:
                profile.teaching.past_subjects = updates.past_subjects
            if updates.preferred_teaching_areas is not None:
                profile.teaching.preferred_areas = updates.preferred_teaching_areas
            
            # Availability updates
            if updates.office_location:
                profile.availability.office_location = updates.office_location
                faculty.office_location = updates.office_location
                updates_made.append("office_location")
            if updates.office_hours:
                profile.availability.office_hours = updates.office_hours
                updates_made.append("office_hours")
            if updates.preferred_meeting_duration:
                profile.availability.preferred_meeting_duration = updates.preferred_meeting_duration
            
            # Publications updates
            if any([updates.total_publications, updates.journal_papers, 
                    updates.conference_papers, updates.notable_works, updates.h_index]):
                if not profile.publications:
                    profile.publications = PublicationSummary()
                if updates.total_publications is not None:
                    profile.publications.total_count = updates.total_publications
                if updates.journal_papers is not None:
                    profile.publications.journal_papers = updates.journal_papers
                if updates.conference_papers is not None:
                    profile.publications.conference_papers = updates.conference_papers
                if updates.notable_works is not None:
                    profile.publications.notable_works = updates.notable_works
                if updates.h_index is not None:
                    profile.publications.h_index = updates.h_index
                updates_made.append("publications")
            
            # Others updates
            if updates.awards is not None:
                profile.others["awards"] = updates.awards
                updates_made.append("awards")
            if updates.patents is not None:
                profile.others["patents"] = updates.patents
            if updates.certifications is not None:
                profile.others["certifications"] = updates.certifications
            if updates.industry_experience is not None:
                profile.others["industry_experience"] = updates.industry_experience
            if updates.professional_memberships is not None:
                profile.others["professional_memberships"] = updates.professional_memberships
            if updates.languages is not None:
                profile.others["languages"] = updates.languages
            
            # Visibility updates
            if updates.visibility:
                if not profile.visibility:
                    profile.visibility = ModelVisibilitySettings()
                profile.visibility = ModelVisibilitySettings(
                    phone=updates.visibility.phone,
                    email=updates.visibility.email,
                    office_location=updates.visibility.office_location
                )
                updates_made.append("visibility")
            
            # Update timestamps and completeness
            profile.last_updated = datetime.utcnow()
            profile.profile_completeness = faculty.calculate_profile_completeness()
            
            faculty.uniform_profile = profile
            faculty.updated_at = datetime.utcnow()
            
            # If major changes, mark for review (optional approval workflow)
            if major_changes:
                faculty.status = FacultyStatus.ACTIVE  # Keep active, but log changes
                logger.info(f"Faculty {user_id} profile has major changes: {major_changes}")
            
            await faculty.save()
            
            logger.info(f"Profile updated for {user_id}: {updates_made}")
            
            return {
                "success": True,
                "message": f"Profile updated successfully. Updated fields: {', '.join(updates_made)}" if updates_made else "No changes made",
                "profile_completeness": profile.profile_completeness,
                "major_changes": major_changes,
                "status": faculty.status.value,
                "updates_made": updates_made
            }
        
        raise HTTPException(status_code=400, detail="Profile not properly initialized")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile update error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Availability Management ====================

@router.put("/availability")
async def update_availability(
    availability: AvailabilityUpdateRequest,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Update meeting availability slots.
    """
    try:
        user_id = current_user.uid
        faculty = await Faculty.find_one(Faculty.user_id == user_id)
        
        if not faculty:
            raise HTTPException(status_code=404, detail="Faculty profile not found")
        
        if not faculty.uniform_profile:
            raise HTTPException(status_code=400, detail="Please complete profile setup first")
        
        # Update availability
        if availability.office_location:
            faculty.uniform_profile.availability.office_location = availability.office_location
            faculty.office_location = availability.office_location
        
        if availability.office_hours:
            faculty.uniform_profile.availability.office_hours = availability.office_hours
        
        if availability.preferred_meeting_duration:
            faculty.uniform_profile.availability.preferred_meeting_duration = availability.preferred_meeting_duration
        
        if availability.available_slots:
            slots = build_meeting_slots(availability.available_slots)
            faculty.uniform_profile.availability.available_slots = slots
            faculty.available_slots = slots
        
        faculty.updated_at = datetime.utcnow()
        await faculty.save()
        
        return {
            "success": True,
            "message": "Availability updated successfully",
            "slots_count": len(faculty.available_slots)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Availability update error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/availability/slots")
async def add_availability_slot(
    slot: MeetingSlotInput,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Add a single availability slot.
    """
    try:
        user_id = current_user.uid
        faculty = await Faculty.find_one(Faculty.user_id == user_id)
        
        if not faculty or not faculty.uniform_profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Check for conflicts
        for existing in faculty.uniform_profile.availability.available_slots:
            if (existing.day == slot.day and 
                existing.start_time == slot.start_time):
                raise HTTPException(
                    status_code=400, 
                    detail=f"Slot conflict: Already have a slot on {slot.day} at {slot.start_time}"
                )
        
        new_slot = MeetingSlot(
            day=slot.day,
            start_time=slot.start_time,
            end_time=slot.end_time,
            venue=slot.venue,
            is_available=True
        )
        
        faculty.uniform_profile.availability.available_slots.append(new_slot)
        faculty.available_slots.append(new_slot)
        faculty.updated_at = datetime.utcnow()
        
        await faculty.save()
        
        return {
            "success": True,
            "message": "Slot added successfully",
            "slot": {
                "day": new_slot.day,
                "start_time": new_slot.start_time,
                "end_time": new_slot.end_time,
                "venue": new_slot.venue
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Add slot error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/availability/slots/{day}/{start_time}")
async def remove_availability_slot(
    day: str,
    start_time: str,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Remove an availability slot.
    """
    try:
        user_id = current_user.uid
        faculty = await Faculty.find_one(Faculty.user_id == user_id)
        
        if not faculty or not faculty.uniform_profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Find and remove slot
        original_count = len(faculty.uniform_profile.availability.available_slots)
        faculty.uniform_profile.availability.available_slots = [
            s for s in faculty.uniform_profile.availability.available_slots
            if not (s.day == day and s.start_time == start_time)
        ]
        faculty.available_slots = faculty.uniform_profile.availability.available_slots
        
        if len(faculty.uniform_profile.availability.available_slots) == original_count:
            raise HTTPException(status_code=404, detail="Slot not found")
        
        faculty.updated_at = datetime.utcnow()
        await faculty.save()
        
        return {
            "success": True,
            "message": "Slot removed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Remove slot error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Profile Retrieval ====================

@router.get("/me", response_model=Dict[str, Any])
async def get_my_profile(
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Get current faculty's full profile.
    """
    try:
        user_id = current_user.uid
        faculty = await Faculty.find_one(Faculty.user_id == user_id)
        
        if not faculty:
            return {
                "user_id": user_id,
                "name": current_user.email.split('@')[0],
                "email": current_user.email,
                "department": "",
                "designation": "",
                "status": "pending_setup",
                "profile_setup_complete": False,
                "profile_completeness": 0,
                "uniform_profile": None,
                "cv_url": None,
                "cv_file_name": None,
                "cv_uploaded_at": None,
                "mentee_count": 0,
                "available_slots_count": 0,
                "needs_setup": True,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
        
        return {
            "user_id": faculty.user_id,
            "name": faculty.name,
            "email": faculty.email,
            "department": faculty.department,
            "designation": faculty.designation,
            "status": faculty.status.value,
            "profile_setup_complete": faculty.profile_setup_complete,
            "profile_completeness": faculty.calculate_profile_completeness(),
            "uniform_profile": faculty.uniform_profile.dict() if faculty.uniform_profile else None,
            "cv_url": faculty.cv_url,
            "cv_file_name": faculty.cv_file_name,
            "cv_uploaded_at": faculty.cv_uploaded_at.isoformat() if faculty.cv_uploaded_at else None,
            "mentee_count": len(faculty.mentee_ids),
            "available_slots_count": len(faculty.available_slots),
            "needs_setup": not faculty.profile_setup_complete,
            "created_at": faculty.created_at.isoformat(),
            "updated_at": faculty.updated_at.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting profile: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch profile: {str(e)}")


@router.get("/check-setup-status", response_model=SetupStatusResponse)
async def check_setup_status(
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Check if faculty has completed profile setup.
    Used to redirect to setup page if incomplete.
    """
    try:
        user_id = current_user.uid
        faculty = await Faculty.find_one(Faculty.user_id == user_id)
        
        if not faculty:
            return SetupStatusResponse(
                profile_exists=False,
                setup_complete=False,
                needs_setup=True,
                status="not_found",
                cv_uploaded=False,
                profile_completeness=0,
                missing_required=["department", "designation", "highest_degree", "office_location"]
            )
        
        # Check what's missing
        missing = []
        if not faculty.department:
            missing.append("department")
        if not faculty.designation:
            missing.append("designation")
        if faculty.uniform_profile:
            if not faculty.uniform_profile.academic_qualifications.highest_degree:
                missing.append("highest_degree")
            if not faculty.uniform_profile.availability.office_location:
                missing.append("office_location")
            if len(faculty.uniform_profile.research_expertise.primary_areas) == 0:
                missing.append("research_areas")
        else:
            missing.extend(["highest_degree", "office_location", "research_areas"])
        
        return SetupStatusResponse(
            profile_exists=True,
            setup_complete=faculty.profile_setup_complete,
            needs_setup=not faculty.profile_setup_complete,
            status=faculty.status.value,
            cv_uploaded=faculty.cv_url is not None,
            profile_completeness=faculty.calculate_profile_completeness(),
            missing_required=missing
        )
        
    except Exception as e:
        logger.error(f"Error checking setup status: {str(e)}")
        return SetupStatusResponse(
            profile_exists=False,
            setup_complete=False,
            needs_setup=True,
            status="error",
            cv_uploaded=False,
            profile_completeness=0
        )


@router.get("/completeness", response_model=ProfileCompletenessResponse)
async def get_profile_completeness(
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Get detailed profile completeness breakdown.
    """
    try:
        user_id = current_user.uid
        faculty = await Faculty.find_one(Faculty.user_id == user_id)
        
        if not faculty or not faculty.uniform_profile:
            return ProfileCompletenessResponse(
                overall=0,
                sections={},
                missing_fields=["Complete profile setup first"],
                recommendations=["Upload your CV to get started"]
            )
        
        # Calculate section-wise completeness
        sections = {}
        missing = []
        recommendations = []
        
        # Personal (20%)
        pi = faculty.uniform_profile.personal_info
        pi_score = 0
        if pi.name:
            pi_score += 40
        if pi.email:
            pi_score += 30
        if pi.phone:
            pi_score += 20
        else:
            missing.append("phone")
        if pi.photo_url:
            pi_score += 10
        else:
            recommendations.append("Add a profile photo for better visibility")
        sections["personal_info"] = pi_score
        
        # Academic (20%)
        aq = faculty.uniform_profile.academic_qualifications
        aq_score = 0
        if aq.highest_degree and aq.highest_degree != "Unknown":
            aq_score += 30
        else:
            missing.append("highest_degree")
        if aq.specialization:
            aq_score += 30
        if aq.university:
            aq_score += 20
        if len(aq.all_degrees) > 0:
            aq_score += 20
        sections["academic"] = aq_score
        
        # Position (15%)
        cp = faculty.uniform_profile.current_position
        cp_score = 0
        if cp.designation and cp.designation != "Faculty":
            cp_score += 40
        if cp.department:
            cp_score += 30
        if cp.years_of_experience > 0:
            cp_score += 30
        sections["position"] = cp_score
        
        # Research (20%)
        re = faculty.uniform_profile.research_expertise
        re_score = 0
        if len(re.primary_areas) > 0:
            re_score += 50
        else:
            missing.append("research_areas")
            recommendations.append("Add your primary research areas")
        if len(re.keywords) > 0:
            re_score += 30
        if len(re.secondary_interests) > 0:
            re_score += 20
        sections["research"] = re_score
        
        # Teaching (10%)
        ti = faculty.uniform_profile.teaching
        ti_score = 0
        if len(ti.current_subjects) > 0:
            ti_score += 60
        else:
            missing.append("current_subjects")
        if len(ti.past_subjects) > 0:
            ti_score += 40
        sections["teaching"] = ti_score
        
        # Availability (15%)
        av = faculty.uniform_profile.availability
        av_score = 0
        if av.office_location:
            av_score += 40
        else:
            missing.append("office_location")
        if av.office_hours:
            av_score += 30
        if len(av.available_slots) > 0:
            av_score += 30
        else:
            recommendations.append("Add meeting slots to allow student consultations")
        sections["availability"] = av_score
        
        # Calculate overall with weights
        overall = (
            sections["personal_info"] * 0.15 +
            sections["academic"] * 0.20 +
            sections["position"] * 0.15 +
            sections["research"] * 0.20 +
            sections["teaching"] * 0.15 +
            sections["availability"] * 0.15
        )
        
        return ProfileCompletenessResponse(
            overall=round(overall, 1),
            sections=sections,
            missing_fields=missing,
            recommendations=recommendations
        )
        
    except Exception as e:
        logger.error(f"Completeness check error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Student View (Public) ====================

@router.get("/{faculty_id}/student-view", response_model=FacultyStudentView)
async def get_faculty_student_view(
    faculty_id: str,
    current_user: Optional[FirebaseUser] = Depends(get_current_user)
):
    """
    Get faculty profile as seen by students.
    Applies visibility settings.
    """
    try:
        faculty = await Faculty.find_one(Faculty.user_id == faculty_id)
        
        if not faculty:
            raise HTTPException(status_code=404, detail="Faculty not found")
        
        if not faculty.profile_setup_complete or faculty.status != FacultyStatus.ACTIVE:
            raise HTTPException(status_code=404, detail="Faculty profile not available")
        
        if not faculty.uniform_profile:
            raise HTTPException(status_code=404, detail="Faculty profile incomplete")
        
        profile = faculty.uniform_profile
        
        # Get requester's department for visibility filtering
        requester_dept = None
        if current_user:
            # Could look up student's department here
            pass
        
        # Build student view with visibility applied
        visibility = profile.visibility
        
        # Determine what to show based on visibility
        show_phone = True
        show_email = True
        show_office = True
        
        if visibility:
            show_phone = visibility.phone == FieldVisibility.PUBLIC or (
                visibility.phone == FieldVisibility.DEPARTMENT and 
                requester_dept == profile.current_position.department
            )
            show_email = visibility.email != FieldVisibility.PRIVATE
            show_office = visibility.office_location != FieldVisibility.PRIVATE
        
        return FacultyStudentView(
            user_id=faculty.user_id,
            name=profile.personal_info.name,
            email=profile.personal_info.email if show_email else None,
            phone=profile.personal_info.phone if show_phone else None,
            photo_url=profile.personal_info.photo_url,
            highest_degree=profile.academic_qualifications.highest_degree,
            specialization=profile.academic_qualifications.specialization,
            university=profile.academic_qualifications.university,
            designation=profile.current_position.designation,
            department=profile.current_position.department,
            institution=profile.current_position.institution,
            years_of_experience=profile.current_position.years_of_experience,
            primary_research_areas=profile.research_expertise.primary_areas,
            secondary_interests=profile.research_expertise.secondary_interests,
            research_keywords=profile.research_expertise.keywords,
            current_subjects=profile.teaching.current_subjects,
            preferred_teaching_areas=profile.teaching.preferred_areas,
            office_location=profile.availability.office_location if show_office else None,
            office_hours=profile.availability.office_hours,
            available_slots=[
                {
                    "day": s.day,
                    "start_time": s.start_time,
                    "end_time": s.end_time,
                    "venue": s.venue if show_office else "Office",
                    "is_available": s.is_available
                }
                for s in profile.availability.available_slots if s.is_available
            ],
            preferred_meeting_duration=profile.availability.preferred_meeting_duration,
            publication_count=profile.publications.total_count if profile.publications else 0,
            notable_works=profile.publications.notable_works if profile.publications else [],
            h_index=profile.publications.h_index if profile.publications else None,
            awards=profile.others.get("awards", []),
            certifications=profile.others.get("certifications", []),
            languages=profile.others.get("languages", []),
            profile_completeness=profile.profile_completeness,
            is_available_for_meetings=len([s for s in profile.availability.available_slots if s.is_available]) > 0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Student view error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Faculty List ====================

@router.get("/list")
async def get_faculty_list(
    department: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    Get list of faculty for student browsing.
    """
    try:
        skip = (page - 1) * page_size
        
        # Build query
        query_filter = {
            "status": FacultyStatus.ACTIVE,
            "profile_setup_complete": True
        }
        
        if department:
            query_filter["department"] = department
        
        # Get faculty
        faculty_query = Faculty.find(query_filter)
        
        if search:
            # Simple search in name and specializations
            faculty_query = Faculty.find({
                **query_filter,
                "$or": [
                    {"name": {"$regex": search, "$options": "i"}},
                    {"specializations": {"$regex": search, "$options": "i"}},
                    {"teaching_subjects": {"$regex": search, "$options": "i"}}
                ]
            })
        
        total = await faculty_query.count()
        faculty_list = await faculty_query.skip(skip).limit(page_size).to_list()
        
        return {
            "faculty": [
                FacultyBasicInfo(
                    user_id=f.user_id,
                    name=f.name,
                    email=f.email,
                    department=f.department,
                    designation=f.designation,
                    photo_url=f.uniform_profile.personal_info.photo_url if f.uniform_profile else None,
                    specializations=f.specializations[:3],
                    profile_completeness=f.calculate_profile_completeness()
                )
                for f in faculty_list
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "has_more": (skip + page_size) < total
        }
        
    except Exception as e:
        logger.error(f"Faculty list error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch faculty")


@router.get("/departments")
async def get_departments():
    """
    Get list of all departments with faculty count.
    """
    try:
        faculties = await Faculty.find({
            "status": FacultyStatus.ACTIVE,
            "profile_setup_complete": True
        }).to_list()
        
        departments = {}
        for f in faculties:
            dept = f.department
            if dept:
                if dept not in departments:
                    departments[dept] = 0
                departments[dept] += 1
        
        return {
            "departments": [
                {"name": dept, "faculty_count": count}
                for dept, count in sorted(departments.items())
            ]
        }
        
    except Exception as e:
        logger.error(f"Departments error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch departments")

@router.get("/{faculty_id}/student-view", response_model=Dict[str, Any])
async def get_faculty_for_students(faculty_id: str):
    """
    Get faculty profile as students see it (respects visibility settings)
    """
    try:
        faculty = await Faculty.find_one(Faculty.user_id == faculty_id)
        
        if not faculty:
            raise HTTPException(status_code=404, detail="Faculty not found")
        
        if not faculty.profile_setup_complete:
            raise HTTPException(status_code=404, detail="Faculty profile not available")
        
        if faculty.status != FacultyStatus.ACTIVE:
            raise HTTPException(status_code=404, detail="Faculty is not currently available")
        
        # Get the student view with visibility applied
        student_view = faculty.get_student_view()
        
        # Apply visibility settings
        if faculty.uniform_profile and faculty.uniform_profile.visibility:
            vis = faculty.uniform_profile.visibility
            
            # Phone visibility
            if vis.phone == "private":
                if "personal_info" in student_view:
                    student_view["personal_info"].pop("phone", None)
            
            # Office visibility  
            if vis.office_location == "private":
                if "availability" in student_view:
                    student_view["availability"]["office_location"] = "Contact for location"
        
        return student_view
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting faculty view: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch faculty profile")


@router.put("/availability/slots")
async def update_availability_slots(
    slots_data: AvailabilityUpdateRequest,
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Update faculty meeting availability slots
    """
    try:
        user_id = current_user.uid
        faculty = await Faculty.find_one(Faculty.user_id == user_id)
        
        if not faculty:
            raise HTTPException(status_code=404, detail="Faculty not found")
        
        # Convert input slots to MeetingSlot objects
        new_slots = []
        for slot in slots_data.available_slots:
            new_slots.append(MeetingSlot(
                day=slot.day,
                start_time=slot.start_time,
                end_time=slot.end_time,
                venue=slot.venue,
                is_available=True
            ))
        
        # Update
        if slots_data.office_location:
            faculty.office_location = slots_data.office_location
            if faculty.uniform_profile:
                faculty.uniform_profile.availability.office_location = slots_data.office_location
        
        if slots_data.office_hours:
            if faculty.uniform_profile:
                faculty.uniform_profile.availability.office_hours = slots_data.office_hours
        
        faculty.available_slots = new_slots
        if faculty.uniform_profile:
            faculty.uniform_profile.availability.available_slots = new_slots
        
        faculty.updated_at = datetime.utcnow()
        await faculty.save()
        
        return {
            "success": True,
            "message": "Availability updated successfully",
            "slots_count": len(new_slots)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating availability: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update availability")


@router.get("/completeness")
async def get_profile_completeness(
    current_user: FirebaseUser = Depends(get_current_user)
):
    """
    Get detailed profile completeness breakdown
    """
    try:
        faculty = await Faculty.find_one(Faculty.user_id == current_user.uid)
        
        if not faculty:
            return ProfileCompletenessResponse(
                overall=0,
                sections={},
                missing_fields=["Profile not created"],
                recommendations=["Complete profile setup first"]
            )
        
        # Calculate section-wise completeness
        sections = {}
        missing = []
        recommendations = []
        
        if faculty.uniform_profile:
            up = faculty.uniform_profile
            
            # Personal (20%)
            pi_score = 0
            if up.personal_info.name: pi_score += 40
            if up.personal_info.email: pi_score += 30
            if up.personal_info.phone: pi_score += 20
            else: missing.append("Phone number")
            if up.personal_info.photo_url: pi_score += 10
            else: recommendations.append("Add a profile photo for better visibility")
            sections["personal_info"] = pi_score
            
            # Academic (20%)
            aq_score = 0
            if up.academic_qualifications.highest_degree and up.academic_qualifications.highest_degree != "Unknown":
                aq_score += 30
            else: missing.append("Highest degree")
            if up.academic_qualifications.specialization: aq_score += 30
            if up.academic_qualifications.university: aq_score += 20
            if up.academic_qualifications.graduation_year: aq_score += 20
            sections["academic"] = aq_score
            
            # Position (15%)
            cp_score = 0
            if up.current_position.designation and up.current_position.designation != "Faculty":
                cp_score += 40
            if up.current_position.department: cp_score += 30
            if up.current_position.years_of_experience > 0: cp_score += 30
            sections["position"] = cp_score
            
            # Research (20%)
            re_score = 0
            if len(up.research_expertise.primary_areas) > 0: re_score += 50
            else: missing.append("Primary research areas")
            if len(up.research_expertise.keywords) > 0: re_score += 30
            if len(up.research_expertise.secondary_interests) > 0: re_score += 20
            sections["research"] = re_score
            
            # Teaching (10%)
            ti_score = 0
            if len(up.teaching.current_subjects) > 0: ti_score += 60
            else: missing.append("Current teaching subjects")
            if len(up.teaching.past_subjects) > 0: ti_score += 40
            sections["teaching"] = ti_score
            
            # Availability (15%)
            av_score = 0
            if up.availability.office_location: av_score += 40
            else: missing.append("Office location")
            if up.availability.office_hours: av_score += 30
            else: missing.append("Office hours")
            if len(up.availability.available_slots) > 0: av_score += 30
            else: recommendations.append("Add meeting slots for students to book appointments")
            sections["availability"] = av_score
            
            # Publications (bonus)
            if up.publications and up.publications.total_count > 0:
                sections["publications"] = 100
            else:
                sections["publications"] = 0
                recommendations.append("Add publication information to showcase your research")
        
        overall = faculty.calculate_profile_completeness()
        
        return {
            "overall": overall,
            "sections": sections,
            "missing_fields": missing,
            "recommendations": recommendations
        }
        
    except Exception as e:
        logger.error(f"Error getting completeness: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to calculate completeness")