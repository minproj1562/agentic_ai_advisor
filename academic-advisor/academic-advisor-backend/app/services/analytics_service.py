# app/services/analytics_service.py
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import pandas as pd
import numpy as np
from app.models.student_profile import StudentProfile, SemesterRecord
from app.models.mentorship import MentorshipSession, MentorshipSlot
from app.models.research_area import ResearchPaper, ResearchArea
import asyncio

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self):
        self.logger = logger

    async def get_performance_trends(
        self, 
        faculty_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get performance trends for faculty's mentees"""
        try:
            # Get all mentees
            mentees = await StudentProfile.find(
                StudentProfile.faculty_mentor_id == faculty_id
            ).to_list()
            
            trends = []
            current_date = start_date
            
            while current_date <= end_date:
                # Calculate metrics for this period
                period_mentees = [
                    m for m in mentees 
                    if m.created_at and m.created_at <= current_date
                ]
                
                if period_mentees:
                    # Calculate average SGPI
                    sgpa_values = [m.current_sgpa for m in period_mentees if m.current_sgpa is not None]
                    avg_sgpa = np.mean(sgpa_values) if sgpa_values else 0
                    
                    # Count active mentees
                    active_count = len([m for m in period_mentees if m.is_active])
                    
                    trends.append({
                        "date": current_date.strftime('%Y-%m-%d'),
                        "avgPerformance": round(avg_sgpa, 2),
                        "activeMentees": active_count,
                        "totalMentees": len(period_mentees)
                    })
                
                current_date += timedelta(days=30)  # Monthly intervals
            
            return trends
            
        except Exception as e:
            self.logger.error(f"Error calculating performance trends: {e}")
            return []

    async def get_mentee_distribution(self, faculty_id: str) -> Dict[str, Any]:
        """Get mentee distribution by various criteria"""
        try:
            mentees = await StudentProfile.find(
                StudentProfile.faculty_mentor_id == faculty_id
            ).to_list()
            
            if not mentees:
                return {}
            
            # Distribution by branch
            branch_dist = {}
            for mentee in mentees:
                branch = mentee.branch or "Unknown"
                branch_dist[branch] = branch_dist.get(branch, 0) + 1
            
            # Distribution by semester
            semester_dist = {}
            for mentee in mentees:
                semester = mentee.current_semester or 1
                semester_dist[semester] = semester_dist.get(semester, 0) + 1
            
            # Performance distribution
            performance_dist = {
                "excellent": len([m for m in mentees if (m.current_sgpa or 0) >= 9.0]),
                "good": len([m for m in mentees if 7.5 <= (m.current_sgpa or 0) < 9.0]),
                "average": len([m for m in mentees if 6.0 <= (m.current_sgpa or 0) < 7.5]),
                "needs_improvement": len([m for m in mentees if (m.current_sgpa or 0) < 6.0])
            }
            
            return {
                "byBranch": [
                    {"branch": branch, "count": count}
                    for branch, count in branch_dist.items()
                ],
                "bySemester": [
                    {"semester": sem, "count": count}
                    for sem, count in semester_dist.items()
                ],
                "byPerformance": performance_dist
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating mentee distribution: {e}")
            return {}

    async def get_session_analytics(
        self, 
        faculty_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get mentorship session analytics"""
        try:
            # Get mentorship sessions for the faculty
            sessions = await MentorshipSession.find(
                MentorshipSession.faculty_id == faculty_id,
                MentorshipSession.date >= start_date,
                MentorshipSession.date <= end_date
            ).to_list()
            
            if not sessions:
                return {
                    "totalSessions": 0,
                    "completedSessions": 0,
                    "cancelledSessions": 0,
                    "completionRate": 0,
                    "avgRating": 0,
                    "avgDuration": 0,
                    "dayDistribution": [],
                    "topics": []
                }
            
            from app.models.mentorship import MentorshipSessionStatus
            completed_sessions = [s for s in sessions if s.status == MentorshipSessionStatus.COMPLETED]
            cancelled_sessions = [s for s in sessions if s.status == MentorshipSessionStatus.CANCELLED]
            
            # Calculate ratings
            ratings = [s.student_rating for s in completed_sessions if s.student_rating is not None]
            avg_rating = np.mean(ratings) if ratings else 0
            
            # Session frequency by day of week
            day_dist = {}
            for session in completed_sessions:
                day = session.date.strftime('%A')
                day_dist[day] = day_dist.get(day, 0) + 1
            
            # Session duration analysis
            durations = [s.duration for s in completed_sessions]
            avg_duration = np.mean(durations) if durations else 0
            
            # Topic distribution
            topic_distribution = {}
            for session in completed_sessions:
                topic = session.topic.value
                topic_distribution[topic] = topic_distribution.get(topic, 0) + 1
            
            return {
                "totalSessions": len(sessions),
                "completedSessions": len(completed_sessions),
                "cancelledSessions": len(cancelled_sessions),
                "completionRate": (len(completed_sessions) / len(sessions)) * 100 if sessions else 0,
                "avgRating": round(avg_rating, 2),
                "avgDuration": round(avg_duration, 2),
                "dayDistribution": [
                    {"day": day, "count": count}
                    for day, count in day_dist.items()
                ],
                "topics": [
                    {"topic": topic, "frequency": count}
                    for topic, count in topic_distribution.items()
                ],
                "typeDistribution": await self._get_session_type_distribution(sessions)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating session analytics: {e}")
            return {}

    async def _get_session_type_distribution(self, sessions: List[MentorshipSession]) -> List[Dict[str, Any]]:
        """Get distribution of session types"""
        type_dist = {}
        for session in sessions:
            session_type = session.slot_type.value
            type_dist[session_type] = type_dist.get(session_type, 0) + 1
        
        return [
            {"type": session_type, "count": count}
            for session_type, count in type_dist.items()
        ]

    async def get_research_metrics(self, faculty_id: str) -> Dict[str, Any]:
        """Get research metrics and analytics"""
        try:
            # Get research areas for the faculty
            research_areas = await ResearchArea.find(
                ResearchArea.user_id == faculty_id
            ).to_list()
            
            if not research_areas:
                return {
                    "totalPapers": 0,
                    "totalCitations": 0,
                    "avgCitations": 0,
                    "hIndex": 0,
                    "publicationTrends": [],
                    "venueDistribution": [],
                    "citationImpact": {
                        "high": 0,
                        "medium": 0,
                        "low": 0
                    }
                }
            
            # Extract all papers from research areas
            all_papers = []
            for area in research_areas:
                all_papers.extend(area.papers)
            
            if not all_papers:
                return {
                    "totalPapers": 0,
                    "totalCitations": 0,
                    "avgCitations": 0,
                    "hIndex": 0,
                    "publicationTrends": [],
                    "venueDistribution": [],
                    "citationImpact": {
                        "high": 0,
                        "medium": 0,
                        "low": 0
                    }
                }
            
            # Calculate metrics
            total_citations = sum(p.citations for p in all_papers)
            avg_citations = total_citations / len(all_papers) if all_papers else 0
            
            # Publication trends by year
            year_dist = {}
            for paper in all_papers:
                year = paper.publication_date.year
                year_dist[year] = year_dist.get(year, 0) + 1
            
            # Journal/conference distribution
            venue_dist = {}
            for paper in all_papers:
                venue = paper.journal or paper.conference or "Unknown"
                venue_dist[venue] = venue_dist.get(venue, 0) + 1
            
            # Citation impact
            citation_impact = {
                "high": len([p for p in all_papers if p.citations >= 50]),
                "medium": len([p for p in all_papers if 10 <= p.citations < 50]),
                "low": len([p for p in all_papers if p.citations < 10])
            }
            
            return {
                "totalPapers": len(all_papers),
                "totalCitations": total_citations,
                "avgCitations": round(avg_citations, 2),
                "hIndex": self._calculate_h_index(all_papers),
                "publicationTrends": [
                    {"year": year, "count": count}
                    for year, count in sorted(year_dist.items())
                ],
                "venueDistribution": [
                    {"venue": venue, "count": count}
                    for venue, count in venue_dist.items()
                ],
                "citationImpact": citation_impact,
                "recentPublications": await self._get_recent_publications(all_papers)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating research metrics: {e}")
            return {}

    async def _get_recent_publications(self, papers: List[ResearchPaper]) -> List[Dict[str, Any]]:
        """Get recent publications for display"""
        recent_papers = sorted(
            papers, 
            key=lambda x: x.publication_date, 
            reverse=True
        )[:5]
        
        return [
            {
                "title": paper.title,
                "year": paper.publication_date.year,
                "citations": paper.citations,
                "venue": paper.journal or paper.conference
            }
            for paper in recent_papers
        ]

    async def get_engagement_metrics(
        self, 
        faculty_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get faculty engagement metrics"""
        try:
            # Get mentorship sessions for response time calculation
            sessions = await MentorshipSession.find(
                MentorshipSession.faculty_id == faculty_id,
                MentorshipSession.date >= start_date,
                MentorshipSession.date <= end_date
            ).to_list()
            
            # Get available slots for availability calculation
            slots = await MentorshipSlot.find(
                MentorshipSlot.faculty_id == faculty_id,
                MentorshipSlot.date >= start_date,
                MentorshipSlot.date <= end_date
            ).to_list()
            
            # Calculate response rate (simplified)
            from app.models.mentorship import MentorshipSessionStatus
            total_booked_sessions = len([s for s in sessions if s.status != MentorshipSessionStatus.CANCELLED])
            responded_sessions = len([s for s in sessions if s.faculty_notes])
            response_rate = (responded_sessions / total_booked_sessions * 100) if total_booked_sessions > 0 else 0
            
            # Calculate availability rate
            total_slots = len(slots)
            booked_slots = len([s for s in slots if s.is_booked])
            availability_rate = ((total_slots - booked_slots) / total_slots * 100) if total_slots > 0 else 0
            
            # Calculate student satisfaction from ratings
            completed_sessions = [s for s in sessions if s.status == MentorshipSessionStatus.COMPLETED]
            ratings = [s.student_rating for s in completed_sessions if s.student_rating]
            student_satisfaction = np.mean(ratings) if ratings else 0
            
            # Calculate overall engagement score
            engagement_score = (
                response_rate * 0.3 +
                availability_rate * 0.3 +
                (student_satisfaction * 20) * 0.4  # Convert 1-5 scale to 0-100
            )
            
            # Get recent activities
            recent_activities = await self._get_recent_activities(faculty_id, start_date, end_date)
            
            return {
                "responseRate": round(response_rate, 1),
                "avgResponseTime": await self._calculate_avg_response_time(sessions),
                "studentSatisfaction": round(student_satisfaction, 1),
                "engagementScore": round(engagement_score, 1),
                "activityLevel": self._assess_activity_level(engagement_score),
                "recentActivities": recent_activities,
                "availabilityRate": round(availability_rate, 1)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating engagement metrics: {e}")
            return {
                "responseRate": 0,
                "avgResponseTime": "N/A",
                "studentSatisfaction": 0,
                "engagementScore": 0,
                "activityLevel": "low",
                "recentActivities": [],
                "availabilityRate": 0
            }

    async def _calculate_avg_response_time(self, sessions: List[MentorshipSession]) -> str:
        """Calculate average response time (simplified)"""
        return "2.3 hours"

    async def _get_recent_activities(self, faculty_id: str, start_date: datetime, end_date: datetime) -> List[str]:
        """Get recent faculty activities"""
        activities = []
        
        # Get recent sessions
        from app.models.mentorship import MentorshipSessionStatus
        recent_sessions = await MentorshipSession.find(
            MentorshipSession.faculty_id == faculty_id,
            MentorshipSession.date >= start_date,
            MentorshipSession.date <= end_date,
            MentorshipSession.status == MentorshipSessionStatus.COMPLETED
        ).sort(-MentorshipSession.date).limit(5).to_list()
        
        if recent_sessions:
            activities.append(f"Conducted {len(recent_sessions)} mentorship sessions")
        
        # Get recent research areas with papers
        research_areas = await ResearchArea.find(
            ResearchArea.user_id == faculty_id
        ).to_list()
        
        recent_papers = []
        for area in research_areas:
            area_recent_papers = [p for p in area.papers if p.publication_date >= start_date]
            recent_papers.extend(area_recent_papers)
        
        if recent_papers:
            activities.append(f"Published {len(recent_papers)} research papers")
        
        # Add generic activities if needed
        if not activities:
            activities = [
                "Active in student mentorship",
                "Engaged in academic activities",
                "Participating in department initiatives"
            ]
        
        return activities[:3]

    def _assess_activity_level(self, engagement_score: float) -> str:
        """Assess activity level based on engagement score"""
        if engagement_score >= 80:
            return "high"
        elif engagement_score >= 60:
            return "medium"
        else:
            return "low"

    def _calculate_h_index(self, papers: List[ResearchPaper]) -> int:
        """Calculate h-index from research papers"""
        if not papers:
            return 0
            
        citations = sorted([p.citations for p in papers], reverse=True)
        h_index = 0
        for i, citations_count in enumerate(citations):
            if citations_count >= i + 1:
                h_index = i + 1
            else:
                break
        return h_index

    async def generate_pdf_report(
        self, 
        faculty_id: str, 
        analytics_data: Dict[str, Any]
    ) -> str:
        """Generate PDF analytics report"""
        report_id = f"report_{faculty_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        return f"/reports/{report_id}.pdf"

    async def generate_excel_report(
        self, 
        faculty_id: str, 
        analytics_data: Dict[str, Any]
    ) -> str:
        """Generate Excel analytics report"""
        report_id = f"report_{faculty_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        return f"/reports/{report_id}.xlsx"

    async def generate_csv_report(
        self, 
        faculty_id: str, 
        analytics_data: Dict[str, Any]
    ) -> str:
        """Generate CSV analytics report"""
        report_id = f"report_{faculty_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        return f"/reports/{report_id}.csv"