# app/services/analytics_service.py
from typing import List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import pandas as pd
import numpy as np
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.piecharts import Pie
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import xlsxwriter

from app.models.student import Student
from app.models.mentorship import MentorshipSession
from app.models.research import ResearchPaper

class AnalyticsService:
    
    async def get_performance_trends(
        self,
        faculty_id: str,
        start_date: datetime,
        end_date: datetime,
        db: Session
    ) -> List[Dict[str, Any]]:
        """
        Calculate performance trends over time
        """
        trends = []
        current_date = start_date
        
        while current_date <= end_date:
            next_date = current_date + timedelta(days=7)  # Weekly intervals
            
            # Get average SGPI for this period
            avg_sgpi = db.query(func.avg(Student.current_sgpi)).filter(
                and_(
                    Student.faculty_mentor_id == faculty_id,
                    Student.updated_at >= current_date,
                    Student.updated_at < next_date
                )
            ).scalar() or 0.0
            
            # Get average attendance
            avg_attendance = db.query(func.avg(Student.attendance_percentage)).filter(
                and_(
                    Student.faculty_mentor_id == faculty_id,
                    Student.updated_at >= current_date,
                    Student.updated_at < next_date
                )
            ).scalar() or 0.0
            
            # Get submission rate
            avg_submissions = db.query(func.avg(Student.assignment_completion_rate)).filter(
                and_(
                    Student.faculty_mentor_id == faculty_id,
                    Student.updated_at >= current_date,
                    Student.updated_at < next_date
                )
            ).scalar() or 0.0
            
            trends.append({
                "date": current_date.isoformat(),
                "avgSGPI": round(float(avg_sgpi), 2),
                "attendance": round(float(avg_attendance), 1),
                "submissions": round(float(avg_submissions), 1)
            })
            
            current_date = next_date
        
        return trends
    
    async def get_mentee_distribution(
        self,
        faculty_id: str,
        db: Session
    ) -> List[Dict[str, Any]]:
        """
        Get distribution of mentees by performance category
        """
        mentees = db.query(Student).filter(
            Student.faculty_mentor_id == faculty_id
        ).all()
        
        if not mentees:
            return []
        
        # Categorize students
        categories = {
            "Excellent (>8.5)": 0,
            "Good (7.5-8.5)": 0,
            "Average (6.5-7.5)": 0,
            "Below Average (<6.5)": 0,
            "At Risk": 0
        }
        
        for mentee in mentees:
            sgpi = mentee.current_sgpi
            if sgpi >= 8.5:
                categories["Excellent (>8.5)"] += 1
            elif sgpi >= 7.5:
                categories["Good (7.5-8.5)"] += 1
            elif sgpi >= 6.5:
                categories["Average (6.5-7.5)"] += 1
            else:
                categories["Below Average (<6.5)"] += 1
            
            if mentee.is_at_risk:
                categories["At Risk"] += 1
        
        total = len(mentees)
        distribution = []
        
        for category, count in categories.items():
            if count > 0:
                distribution.append({
                    "category": category,
                    "count": count,
                    "percentage": round((count / total) * 100, 1)
                })
        
        return distribution
    
    async def get_session_analytics(
        self,
        faculty_id: str,
        start_date: datetime,
        end_date: datetime,
        db: Session
    ) -> Dict[str, Any]:
        """
        Get detailed session analytics
        """
        sessions = db.query(MentorshipSession).filter(
            and_(
                MentorshipSession.faculty_id == faculty_id,
                MentorshipSession.date >= start_date,
                MentorshipSession.date <= end_date
            )
        ).all()
        
        if not sessions:
            return {
                "totalSessions": 0,
                "avgDuration": 0,
                "completionRate": 0,
                "satisfactionScore": 0,
                "topicsDiscussed": []
            }
        
        total_sessions = len(sessions)
        completed_sessions = len([s for s in sessions if s.status == 'completed'])
        
        avg_duration = np.mean([s.duration_minutes for s in sessions if s.duration_minutes])
        completion_rate = (completed_sessions / total_sessions) * 100 if total_sessions > 0 else 0
        
        # Calculate satisfaction score
        ratings = [s.rating for s in sessions if s.rating]
        satisfaction_score = (np.mean(ratings) / 5) * 100 if ratings else 0
        
        # Count topics discussed
        topic_counts = {}
        for session in sessions:
            if session.topics:
                for topic in session.topics:
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        topics_discussed = [
            {"topic": topic, "frequency": count}
            for topic, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        ][:10]
        
        return {
            "totalSessions": total_sessions,
            "avgDuration": round(avg_duration, 1),
            "completionRate": round(completion_rate, 1),
            "satisfactionScore": round(satisfaction_score, 1),
            "topicsDiscussed": topics_discussed
        }
    
    async def get_research_metrics(
        self,
        faculty_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Get research-related metrics
        """
        papers = db.query(ResearchPaper).filter(
            ResearchPaper.faculty_id == faculty_id
        ).all()
        
        if not papers:
            return {
                "papers": 0,
                "citations": 0,
                "hIndex": 0,
                "collaborations": 0,
                "impactFactor": 0,
                "trending": []
            }
        
        total_papers = len(papers)
        total_citations = sum(paper.citations for paper in papers)
        
        # Calculate h-index
        citations_sorted = sorted([paper.citations for paper in papers], reverse=True)
        h_index = 0
        for i, citations in enumerate(citations_sorted, 1):
            if citations >= i:
                h_index = i
            else:
                break
        
        # Count unique collaborators
        all_collaborators = set()
        for paper in papers:
            if paper.authors:
                all_collaborators.update(paper.authors)
        collaborations = len(all_collaborators) - 1  # Exclude self
        
        # Calculate average impact factor
        impact_factors = [paper.impact_factor for paper in papers if paper.impact_factor]
        avg_impact_factor = np.mean(impact_factors) if impact_factors else 0
        
        # Get trending papers (most viewed/cited recently)
        trending = sorted(papers, key=lambda p: p.citations + p.views, reverse=True)[:5]
        trending_list = [
            {
                "paper": paper.title,
                "views": paper.views,
                "citations": paper.citations
            }
            for paper in trending
        ]
        
        return {
            "papers": total_papers,
            "citations": total_citations,
            "hIndex": h_index,
            "collaborations": collaborations,
            "impactFactor": round(avg_impact_factor, 2),
            "trending": trending_list
        }
    
    async def get_engagement_metrics(
        self,
        faculty_id: str,
        start_date: datetime,
        end_date: datetime,
        db: Session
    ) -> Dict[str, Any]:
        """
        Get engagement-related metrics
        """
        # Get active students
        weekly_active = db.query(func.count(Student.id)).filter(
            and_(
                Student.faculty_mentor_id == faculty_id,
                Student.last_active >= datetime.utcnow() - timedelta(days=7)
            )
        ).scalar() or 0
        
        monthly_active = db.query(func.count(Student.id)).filter(
            and_(
                Student.faculty_mentor_id == faculty_id,
                Student.last_active >= datetime.utcnow() - timedelta(days=30)
            )
        ).scalar() or 0
        
        # Calculate average response time
        sessions = db.query(MentorshipSession).filter(
            and_(
                MentorshipSession.faculty_id == faculty_id,
                MentorshipSession.date >= start_date,
                MentorshipSession.date <= end_date
            )
        ).all()
        
        response_times = []
        for session in sessions:
            if session.request_time and session.response_time:
                delta = (session.response_time - session.request_time).total_seconds() / 3600
                response_times.append(delta)
        
        avg_response_time = np.mean(response_times) if response_times else 0
        
        # Count messages sent
        messages_sent = db.query(func.count(Message.id)).filter(
            and_(
                Message.sender_id == faculty_id,
                Message.timestamp >= start_date,
                Message.timestamp <= end_date
            )
        ).scalar() or 0
        
        # Calculate feedback score
        feedback_scores = [s.feedback_score for s in sessions if s.feedback_score]
        avg_feedback_score = np.mean(feedback_scores) if feedback_scores else 0
        
        return {
            "weeklyActive": weekly_active,
            "monthlyActive": monthly_active,
            "avgResponseTime": round(avg_response_time, 1),
            "messagesSent": messages_sent,
            "feedbackScore": round(avg_feedback_score, 2)
        }
    
    async def generate_pdf_report(
        self,
        faculty_id: str,
        analytics_data: Dict[str, Any],
        db: Session
    ) -> str:
        """
        Generate comprehensive PDF report
        """
        # Get faculty info
        faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
        
        # Create PDF
        filename = f"analytics_report_{faculty_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
        filepath = f"reports/{filename}"
        
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f2937'),
            spaceAfter=30,
            alignment=1  # Center
        )
        
        story.append(Paragraph(f"Analytics Report - {faculty.name}", title_style))
        story.append(Paragraph(f"Department: {faculty.department}", styles['Normal']))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
        story.append(Spacer(1, 30))
        
        # Overview Section
        story.append(Paragraph("Performance Overview", styles['Heading2']))
        overview_data = [
            ['Metric', 'Value'],
            ['Total Mentees', str(analytics_data['overview']['totalMentees'])],
            ['Active Mentees', str(analytics_data['overview']['activeMentees'])],
            ['Average Performance', f"{analytics_data['overview']['avgPerformance']} SGPI"],
            ['Performance Change', f"{analytics_data['overview']['performanceChange']}%"],
            ['Sessions Completed', str(analytics_data['overview']['sessionsCompleted'])],
            ['Average Rating', f"{analytics_data['overview']['avgSessionRating']}★"],
            ['Research Papers', str(analytics_data['overview']['researchPapers'])],
            ['Total Citations', str(analytics_data['overview']['citations'])]
        ]
        
        overview_table = Table(overview_data, colWidths=[3*inch, 2*inch])
        overview_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        
        story.append(overview_table)
        story.append(Spacer(1, 30))
        
        # Performance Trends Chart
        story.append(Paragraph("Performance Trends", styles['Heading2']))
        
        # Create matplotlib chart
        plt.figure(figsize=(10, 6))
        trends = analytics_data['performanceTrends']
        dates = [t['date'] for t in trends]
        sgpis = [t['avgSGPI'] for t in trends]
        
        plt.plot(dates[::4], sgpis[::4], marker='o', linewidth=2, markersize=8)
        plt.xlabel('Date')
        plt.ylabel('Average SGPI')
        plt.title('Performance Trend Over Time')
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Save chart to buffer
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        
        # Add chart to PDF
        img = Image(buffer, width=6*inch, height=3.5*inch)
        story.append(img)
        story.append(Spacer(1, 30))
        
        # Mentee Distribution
        story.append(Paragraph("Mentee Distribution", styles['Heading2']))
        distribution_data = [['Category', 'Count', 'Percentage']]
        for item in analytics_data['menteeDistribution']:
            distribution_data.append([
                item['category'],
                str(item['count']),
                f"{item['percentage']}%"
            ])
        
        dist_table = Table(distribution_data, colWidths=[3*inch, 1*inch, 1.5*inch])
        dist_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8b5cf6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        
        story.append(dist_table)
        
        # Build PDF
        doc.build(story)
        
        return filepath
    
    async def generate_excel_report(
        self,
        faculty_id: str,
        analytics_data: Dict[str, Any],
        db: Session
    ) -> str:
        """
        Generate Excel report with multiple sheets
        """
        filename = f"analytics_report_{faculty_id}_{datetime.now().strftime('%Y%m%d')}.xlsx"
        filepath = f"reports/{filename}"
        
        writer = pd.ExcelWriter(filepath, engine='xlsxwriter')
        workbook = writer.book
        
        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4f46e5',
            'font_color': 'white',
            'border': 1
        })
        
        # Overview Sheet
        overview_df = pd.DataFrame([analytics_data['overview']])
        overview_df.to_excel(writer, sheet_name='Overview', index=False)
        
        # Performance Trends Sheet
        trends_df = pd.DataFrame(analytics_data['performanceTrends'])
        trends_df.to_excel(writer, sheet_name='Performance Trends', index=False)
        
        # Mentee Distribution Sheet
        dist_df = pd.DataFrame(analytics_data['menteeDistribution'])
        dist_df.to_excel(writer, sheet_name='Mentee Distribution', index=False)
        
        # Session Analytics Sheet
        session_df = pd.DataFrame([analytics_data['sessionAnalytics']])
        session_df.to_excel(writer, sheet_name='Session Analytics', index=False)
        
        # Research Metrics Sheet
        research_df = pd.DataFrame([analytics_data['researchMetrics']])
        research_df.to_excel(writer, sheet_name='Research Metrics', index=False)
        
        # Apply formatting to all sheets
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            worksheet.set_column('A:Z', 20)
            
            # Format header row
            for col_num, value in enumerate(worksheet.table[0]):
                worksheet.write(0, col_num, value, header_format)
        
        writer.close()
        
        return filepath
    
    async def generate_csv_report(
        self,
        faculty_id: str,
        analytics_data: Dict[str, Any],
        db: Session
    ) -> str:
        """
        Generate CSV report
        """
        filename = f"analytics_report_{faculty_id}_{datetime.now().strftime('%Y%m%d')}.csv"
        filepath = f"reports/{filename}"
        
        # Combine all data into a single DataFrame
        all_data = []
        
        # Add overview
        all_data.append(["OVERVIEW"])
        for key, value in analytics_data['overview'].items():
            all_data.append([key, value])
        all_data.append([])
        
        # Add performance trends
        all_data.append(["PERFORMANCE TRENDS"])
        trends_df = pd.DataFrame(analytics_data['performanceTrends'])
        all_data.extend(trends_df.values.tolist())
        all_data.append([])
        
        # Convert to DataFrame and save
        df = pd.DataFrame(all_data)
        df.to_csv(filepath, index=False, header=False)
        
        return filepath