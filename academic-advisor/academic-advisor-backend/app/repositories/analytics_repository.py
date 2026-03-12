# app/repositories/analytics_repository.py
"""
Chatbot analytics data access layer - Enhanced
"""

import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from app.models.chatbot import ChatbotAnalyticsDoc

logger = logging.getLogger(__name__)


class AnalyticsRepository:
    """Repository for chatbot analytics operations."""

    async def get_or_create_today(self) -> ChatbotAnalyticsDoc:
        """Get or create today's analytics document."""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        doc = await ChatbotAnalyticsDoc.find_one(ChatbotAnalyticsDoc.date == today)
        if not doc:
            doc = ChatbotAnalyticsDoc(date=today)
            await doc.insert()
        return doc

    async def record_query(
        self,
        intent: str,
        response_time_ms: int,
        confidence: str,
        success: bool,
        user_id: str,
        response_type: str = None,
    ):
        """Record a single query's metrics."""
        try:
            doc = await self.get_or_create_today()
            
            doc.total_queries += 1
            
            if success:
                doc.successful_responses += 1
            else:
                doc.failed_responses += 1
            
            if intent == "OUT_OF_SCOPE":
                doc.out_of_scope_queries += 1

            # Update intent distribution
            doc.intent_distribution[intent] = doc.intent_distribution.get(intent, 0) + 1

            # Update response type distribution
            if response_type:
                doc.response_type_distribution[response_type] = \
                    doc.response_type_distribution.get(response_type, 0) + 1

            # Update response time metrics (running average)
            n = doc.total_queries
            doc.avg_response_time_ms = (
                (doc.avg_response_time_ms * (n - 1) + response_time_ms) / n
            )
            
            # Update min/max
            if doc.min_response_time_ms == 0 or response_time_ms < doc.min_response_time_ms:
                doc.min_response_time_ms = response_time_ms
            if response_time_ms > doc.max_response_time_ms:
                doc.max_response_time_ms = response_time_ms

            # Update confidence (running average)
            conf_val = {"High": 1.0, "Medium": 0.6, "Low": 0.3}.get(confidence, 0.5)
            doc.avg_confidence = (doc.avg_confidence * (n - 1) + conf_val) / n

            # Track unique users
            if user_id and user_id not in doc.user_ids:
                doc.user_ids.append(user_id)
                doc.unique_users = len(doc.user_ids)

            doc.updated_at = datetime.utcnow()
            await doc.save()
            
        except Exception as e:
            logger.error(f"Error recording query analytics: {e}")

    async def record_error(self, error_type: str = "general"):
        """Record an error occurrence."""
        try:
            doc = await self.get_or_create_today()
            doc.error_count += 1
            doc.error_types[error_type] = doc.error_types.get(error_type, 0) + 1
            doc.updated_at = datetime.utcnow()
            await doc.save()
        except Exception as e:
            logger.error(f"Error recording error analytics: {e}")

    async def record_feedback(self, rating: int, was_helpful: bool = None):
        """Record user feedback."""
        try:
            doc = await self.get_or_create_today()
            doc.feedback_count += 1
            
            # Update average rating
            n = doc.feedback_count
            doc.user_satisfaction_avg = (
                (doc.user_satisfaction_avg * (n - 1) + rating) / n
            )
            
            # Count positive/negative
            if rating >= 4:
                doc.positive_feedback_count += 1
            elif rating <= 2:
                doc.negative_feedback_count += 1
            
            doc.updated_at = datetime.utcnow()
            await doc.save()
        except Exception as e:
            logger.error(f"Error recording feedback analytics: {e}")

    async def get_analytics(self, days: int = 30) -> List[ChatbotAnalyticsDoc]:
        """Get analytics documents for the specified period."""
        since = datetime.utcnow() - timedelta(days=days)
        return await ChatbotAnalyticsDoc.find(
            ChatbotAnalyticsDoc.date >= since
        ).sort(ChatbotAnalyticsDoc.date).to_list()

    async def get_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get aggregated summary for the specified period."""
        rows = await self.get_analytics(days)
        
        if not rows:
            return {
                "period_days": days,
                "total_queries": 0,
                "successful_responses": 0,
                "failed_responses": 0,
                "success_rate": 0,
                "avg_response_time_ms": 0,
                "top_intents": {},
                "unique_users": 0,
                "feedback_summary": {
                    "total": 0,
                    "avg_rating": 0,
                    "positive_rate": 0
                }
            }

        # Aggregate metrics
        total_queries = sum(r.total_queries for r in rows)
        successful = sum(r.successful_responses for r in rows)
        failed = sum(r.failed_responses for r in rows)
        errors = sum(r.error_count for r in rows)
        out_of_scope = sum(r.out_of_scope_queries for r in rows)

        # Merge intent distributions
        intent_dist: Dict[str, int] = {}
        for r in rows:
            for intent, count in r.intent_distribution.items():
                intent_dist[intent] = intent_dist.get(intent, 0) + count

        # Merge response type distributions
        response_type_dist: Dict[str, int] = {}
        for r in rows:
            for rt, count in r.response_type_distribution.items():
                response_type_dist[rt] = response_type_dist.get(rt, 0) + count

        # Calculate weighted average response time
        avg_response_time = 0
        if total_queries > 0:
            weighted_sum = sum(r.avg_response_time_ms * r.total_queries for r in rows)
            avg_response_time = weighted_sum / total_queries

        # Unique users (approximate - may have duplicates across days)
        all_users = set()
        for r in rows:
            all_users.update(r.user_ids)
        unique_users = len(all_users)

        # Feedback summary
        total_feedback = sum(r.feedback_count for r in rows)
        positive_feedback = sum(r.positive_feedback_count for r in rows)
        avg_satisfaction = 0
        if total_feedback > 0:
            weighted_satisfaction = sum(r.user_satisfaction_avg * r.feedback_count for r in rows)
            avg_satisfaction = weighted_satisfaction / total_feedback

        return {
            "period_days": days,
            "total_queries": total_queries,
            "successful_responses": successful,
            "failed_responses": failed,
            "errors": errors,
            "out_of_scope": out_of_scope,
            "success_rate": round(successful / total_queries * 100, 1) if total_queries else 0,
            "avg_response_time_ms": round(avg_response_time, 1),
            "unique_users": unique_users,
            "top_intents": dict(
                sorted(intent_dist.items(), key=lambda x: x[1], reverse=True)[:10]
            ),
            "response_types": dict(
                sorted(response_type_dist.items(), key=lambda x: x[1], reverse=True)
            ),
            "feedback_summary": {
                "total": total_feedback,
                "avg_rating": round(avg_satisfaction, 2),
                "positive_count": positive_feedback,
                "positive_rate": round(positive_feedback / total_feedback * 100, 1) if total_feedback else 0
            },
            "daily_breakdown": [
                {
                    "date": r.date.isoformat(),
                    "queries": r.total_queries,
                    "success_rate": round(r.successful_responses / r.total_queries * 100, 1) if r.total_queries else 0,
                    "avg_response_ms": round(r.avg_response_time_ms, 1),
                }
                for r in rows
            ]
        }