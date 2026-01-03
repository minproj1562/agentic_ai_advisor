#academic-advisor-backend/app/services/achievement_service.py
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from app.models.achievement import Achievement, AchievementAnalytics, AchievementCategory
from app.core.cache import cache_key_wrapper

logger = logging.getLogger(__name__)

class AchievementService:
    def __init__(self):
        self.logger = logger

    async def calculate_impact_score(self, achievement: Achievement) -> float:
        """Calculate impact score for an achievement"""
        base_score = 5.0
        
        # Category weights
        category_weights = {
            AchievementCategory.RESEARCH: 1.2,
            AchievementCategory.PUBLICATION: 1.5,
            AchievementCategory.GRANT: 1.8,
            AchievementCategory.PATENT: 2.0,
            AchievementCategory.AWARD: 1.5,
            AchievementCategory.TEACHING: 1.0,
            AchievementCategory.SERVICE: 0.8,
            AchievementCategory.CONFERENCE: 1.2,
            AchievementCategory.STUDENT_SUPERVISION: 1.1,
            AchievementCategory.OTHER: 0.5
        }
        
        # Adjust score based on verification
        if achievement.verified:
            base_score += 2.0
        
        # Adjust based on recency (recent achievements get higher scores)
        days_old = (datetime.utcnow() - achievement.date).days
        if days_old <= 365:  # Within last year
            recency_bonus = max(0, (365 - days_old) / 365) * 2.0
            base_score += recency_bonus
        
        # Apply category weight
        category_weight = category_weights.get(achievement.category, 1.0)
        final_score = base_score * category_weight
        
        return min(10.0, final_score)  # Cap at 10

    async def calculate_analytics(self, faculty_id: str) -> AchievementAnalytics:
        """Calculate achievement analytics for a faculty member"""
        current_year = datetime.now().year
        last_year = current_year - 1
        
        # Get all achievements
        achievements = await Achievement.find(
            Achievement.faculty_id == faculty_id
        ).to_list()
        
        # Calculate metrics
        total = len(achievements)
        verified = len([a for a in achievements if a.verified])
        
        this_year = len([
            a for a in achievements 
            if a.date.year == current_year
        ])
        
        last_year_count = len([
            a for a in achievements 
            if a.date.year == last_year
        ])
        
        # Calculate growth rate
        growth_rate = 0
        if last_year_count > 0:
            growth_rate = ((this_year - last_year_count) / last_year_count) * 100
        
        # Calculate average impact score
        avg_impact = 0
        if achievements:
            avg_impact = sum(a.impact_score or 0 for a in achievements) / len(achievements)
        
        # Calculate category distribution
        category_dist = {}
        for achievement in achievements:
            category = achievement.category
            category_dist[category] = category_dist.get(category, 0) + 1
        
        category_distribution = [
            {"category": category, "count": count}
            for category, count in category_dist.items()
        ]
        
        # Create or update analytics
        analytics = await AchievementAnalytics.find_one(
            AchievementAnalytics.faculty_id == faculty_id
        )
        
        if not analytics:
            analytics = AchievementAnalytics(faculty_id=faculty_id)
        
        analytics.total_achievements = total
        analytics.verified_count = verified
        analytics.this_year_count = this_year
        analytics.avg_impact_score = round(avg_impact, 2)
        analytics.growth_rate = round(growth_rate, 1)
        analytics.category_distribution = category_distribution
        analytics.created_at = datetime.utcnow()
        
        await analytics.save()
        return analytics

    async def request_verification(self, achievement: Achievement):
        """Request verification for an achievement"""
        achievement.status = "submitted"
        achievement.updated_at = datetime.utcnow()
        await achievement.save()
        
        # In real implementation, this would send notification to admin/verification team
        self.logger.info(f"Verification requested for achievement: {achievement.id}")

    async def export_to_csv(self, achievements: List[Achievement]) -> str:
        """Export achievements to CSV format"""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Title', 'Category', 'Date', 'Impact Score', 
            'Verified', 'Description', 'Tags'
        ])
        
        # Write data
        for achievement in achievements:
            writer.writerow([
                achievement.title,
                achievement.category,
                achievement.date.strftime('%Y-%m-%d'),
                achievement.impact_score or '',
                'Yes' if achievement.verified else 'No',
                achievement.description or '',
                ', '.join(achievement.tags)
            ])
        
        return output.getvalue()

    async def export_to_pdf(self, achievements: List[Achievement]) -> str:
        """Export achievements to PDF format"""
        # This would be implemented with a PDF generation library like ReportLab
        # For now, return a placeholder
        return "PDF export functionality would be implemented here"

    async def log_activity(self, faculty_id: str, activity_type: str, achievement_id: str):
        """Log achievement-related activity"""
        # In real implementation, this would log to an activity feed or audit log
        self.logger.info(
            f"Activity: {activity_type} for achievement {achievement_id} "
            f"by faculty {faculty_id}"
        )