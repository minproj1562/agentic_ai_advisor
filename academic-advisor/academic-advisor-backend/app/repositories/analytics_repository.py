# academic-advisor/academic-advisor-backend/app/repositories/analytics_repository.py
"""
Chatbot analytics data access layer
"""

import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from app.models.chatbot import ChatbotAnalyticsDoc

logger = logging.getLogger(__name__)


class AnalyticsRepository:

    async def get_or_create_today(self) -> ChatbotAnalyticsDoc:
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
    ):
        doc = await self.get_or_create_today()
        doc.total_queries += 1
        if success:
            doc.successful_responses += 1
        if intent == "OUT_OF_SCOPE":
            doc.out_of_scope_queries += 1

        doc.intent_distribution[intent] = doc.intent_distribution.get(intent, 0) + 1

        n = doc.total_queries
        doc.avg_response_time_ms = (
            (doc.avg_response_time_ms * (n - 1) + response_time_ms) / n
        )
        conf_val = {"High": 1.0, "Medium": 0.6, "Low": 0.3}.get(confidence, 0.5)
        doc.avg_confidence = (doc.avg_confidence * (n - 1) + conf_val) / n

        await doc.save()

    async def record_error(self):
        doc = await self.get_or_create_today()
        doc.error_count += 1
        await doc.save()

    async def get_analytics(self, days: int = 30) -> List[ChatbotAnalyticsDoc]:
        since = datetime.utcnow() - timedelta(days=days)
        return await ChatbotAnalyticsDoc.find(
            ChatbotAnalyticsDoc.date >= since
        ).sort(ChatbotAnalyticsDoc.date).to_list()

    async def get_summary(self, days: int = 7) -> Dict[str, Any]:
        rows = await self.get_analytics(days)
        if not rows:
            return {
                "period_days": days, "total_queries": 0,
                "success_rate": 0, "avg_response_time_ms": 0,
                "top_intents": {},
            }

        total = sum(r.total_queries for r in rows)
        success = sum(r.successful_responses for r in rows)
        errors = sum(r.error_count for r in rows)

        merged: Dict[str, int] = {}
        for r in rows:
            for k, v in r.intent_distribution.items():
                merged[k] = merged.get(k, 0) + v

        avg_rt = (
            sum(r.avg_response_time_ms * r.total_queries for r in rows) / total
            if total else 0
        )

        return {
            "period_days": days,
            "total_queries": total,
            "successful_responses": success,
            "errors": errors,
            "success_rate": round(success / total * 100, 1) if total else 0,
            "avg_response_time_ms": round(avg_rt, 1),
            "top_intents": dict(
                sorted(merged.items(), key=lambda x: x[1], reverse=True)
            ),
        }