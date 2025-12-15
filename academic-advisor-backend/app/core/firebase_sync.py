"""
Firebase real-time synchronization utilities
"""

import asyncio
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime

from app.core.firebase_admin import firebase_manager
from app.utils.helpers import get_logger

logger = get_logger(__name__)


class FirebaseSync:
    """
    Real-time synchronization with Firebase
    """
    
    def __init__(self):
        self.listeners = {}
        self.sync_tasks = []
        
    async def start_sync(
        self,
        collection: str,
        callback: Callable,
        filters: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Start real-time synchronization for a collection
        """
        try:
            # Generate unique listener ID
            listener_id = f"{collection}_{datetime.utcnow().timestamp()}"
            
            # Setup Firebase listener
            listener = firebase_manager.setup_realtime_listener(
                collection=collection,
                callback=callback,
                filters=filters
            )
            
            self.listeners[listener_id] = listener
            
            logger.info(f"Started sync for {collection} with ID {listener_id}")
            
            return listener_id
            
        except Exception as e:
            logger.error(f"Failed to start sync: {str(e)}")
            raise
    
    def stop_sync(self, listener_id: str):
        """
        Stop real-time synchronization
        """
        try:
            if listener_id in self.listeners:
                listener = self.listeners[listener_id]
                listener.unsubscribe()
                del self.listeners[listener_id]
                
                logger.info(f"Stopped sync for {listener_id}")
                
        except Exception as e:
            logger.error(f"Failed to stop sync: {str(e)}")
    
    def stop_all_syncs(self):
        """
        Stop all active synchronizations
        """
        for listener_id in list(self.listeners.keys()):
            self.stop_sync(listener_id)
    
    async def sync_collection_periodically(
        self,
        source_collection: str,
        target_collection: str,
        interval_seconds: int = 60,
        transform_func: Optional[Callable] = None
    ):
        """
        Periodically sync data between collections
        """
        while True:
            try:
                # Get source data
                source_data = await firebase_manager.get_collection(
                    collection=source_collection
                )
                
                # Transform data if function provided
                if transform_func:
                    target_data = transform_func(source_data)
                else:
                    target_data = source_data
                
                # Update target collection
                for item in target_data:
                    await firebase_manager.update_document(
                        collection=target_collection,
                        document_id=item.get('id'),
                        data=item
                    )
                
                logger.info(f"Synced {len(target_data)} items from {source_collection} to {target_collection}")
                
            except Exception as e:
                logger.error(f"Sync error: {str(e)}")
            
            await asyncio.sleep(interval_seconds)
    
    async def sync_aggregations(
        self,
        source_collection: str,
        aggregation_collection: str,
        aggregation_func: Callable,
        interval_seconds: int = 300
    ):
        """
        Sync aggregated data periodically
        """
        while True:
            try:
                # Get source data
                source_data = await firebase_manager.get_collection(
                    collection=source_collection
                )
                
                # Calculate aggregations
                aggregations = aggregation_func(source_data)
                
                # Store aggregations
                await firebase_manager.update_document(
                    collection=aggregation_collection,
                    document_id='latest',
                    data={
                        **aggregations,
                        'updated_at': datetime.utcnow().isoformat()
                    }
                )
                
                logger.info(f"Updated aggregations for {source_collection}")
                
            except Exception as e:
                logger.error(f"Aggregation sync error: {str(e)}")
            
            await asyncio.sleep(interval_seconds)
    
    async def setup_bidirectional_sync(
        self,
        collection1: str,
        collection2: str,
        sync_fields: List[str]
    ):
        """
        Setup bidirectional sync between collections
        """
        async def sync_to_collection2(data):
            """Sync changes from collection1 to collection2"""
            sync_data = {
                field: data.get(field)
                for field in sync_fields
                if field in data
            }
            
            await firebase_manager.update_document(
                collection=collection2,
                document_id=data.get('id'),
                data=sync_data
            )
        
        async def sync_to_collection1(data):
            """Sync changes from collection2 to collection1"""
            sync_data = {
                field: data.get(field)
                for field in sync_fields
                if field in data
            }
            
            await firebase_manager.update_document(
                collection=collection1,
                document_id=data.get('id'),
                data=sync_data
            )
        
        # Setup listeners for both collections
        listener1_id = await self.start_sync(
            collection=collection1,
            callback=sync_to_collection2
        )
        
        listener2_id = await self.start_sync(
            collection=collection2,
            callback=sync_to_collection1
        )
        
        return [listener1_id, listener2_id]
    
    async def replicate_to_backup(
        self,
        collection: str,
        backup_collection: str
    ):
        """
        Replicate collection to backup
        """
        try:
            # Get all documents
            documents = await firebase_manager.get_collection(
                collection=collection
            )
            
            # Batch write to backup
            operations = []
            for doc in documents:
                operations.append({
                    'type': 'create',
                    'collection': backup_collection,
                    'document_id': doc.get('id'),
                    'data': {
                        **doc,
                        'backed_up_at': datetime.utcnow().isoformat()
                    }
                })
            
            await firebase_manager.batch_write(operations)
            
            logger.info(f"Replicated {len(documents)} documents to {backup_collection}")
            
        except Exception as e:
            logger.error(f"Replication error: {str(e)}")
            raise


# Global sync instance
firebase_sync = FirebaseSync()


async def start_background_syncs():
    """
    Start all background synchronization tasks
    """
    sync = FirebaseSync()
    
    # Sync student aggregations every 5 minutes
    asyncio.create_task(
        sync.sync_aggregations(
            source_collection='students',
            aggregation_collection='analytics_cache',
            aggregation_func=calculate_student_aggregations,
            interval_seconds=300
        )
    )
    
    # Sync performance metrics every 10 minutes
    asyncio.create_task(
        sync.sync_aggregations(
            source_collection='students',
            aggregation_collection='performance_metrics',
            aggregation_func=calculate_performance_metrics,
            interval_seconds=600
        )
    )
    
    logger.info("Background sync tasks started")


def calculate_student_aggregations(students: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate aggregations for students
    """
    import numpy as np
    
    if not students:
        return {}
    
    cgpas = [s.get('cgpa', 0) for s in students]
    
    return {
        'total_students': len(students),
        'average_cgpa': np.mean(cgpas),
        'median_cgpa': np.median(cgpas),
        'top_cgpa': np.max(cgpas) if cgpas else 0,
        'at_risk_count': sum(1 for s in students if s.get('risk_level') == 'high'),
        'department_distribution': calculate_department_distribution(students)
    }


def calculate_department_distribution(students: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Calculate distribution by department
    """
    from collections import defaultdict
    
    distribution = defaultdict(int)
    for student in students:
        dept = student.get('department', 'unknown')
        distribution[dept] += 1
    
    return dict(distribution)


def calculate_performance_metrics(students: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate performance metrics
    """
    metrics = {
        'performance_categories': {
            'excellent': 0,
            'good': 0,
            'average': 0,
            'poor': 0
        },
        'attendance_distribution': {
            'above_90': 0,
            'above_75': 0,
            'below_75': 0
        }
    }
    
    for student in students:
        # Categorize by CGPA
        cgpa = student.get('cgpa', 0)
        if cgpa >= 8.5:
            metrics['performance_categories']['excellent'] += 1
        elif cgpa >= 7.0:
            metrics['performance_categories']['good'] += 1
        elif cgpa >= 5.5:
            metrics['performance_categories']['average'] += 1
        else:
            metrics['performance_categories']['poor'] += 1
        
        # Categorize by attendance
        attendance = student.get('attendance', 0)
        if attendance >= 90:
            metrics['attendance_distribution']['above_90'] += 1
        elif attendance >= 75:
            metrics['attendance_distribution']['above_75'] += 1
        else:
            metrics['attendance_distribution']['below_75'] += 1
    
    return metrics