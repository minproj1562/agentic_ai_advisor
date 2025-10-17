# app/services/achievement_service.py
from typing import List, Optional
import csv
import io
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.achievement import Achievement
from app.core.ml import ImpactScorePredictor

class AchievementService:
    def __init__(self):
        self.impact_predictor = ImpactScorePredictor()
    
    async def calculate_impact_score(self, achievement: Achievement) -> float:
        """
        Calculate impact score using ML model
        """
        features = {
            'category': achievement.category,
            'organization_prestige': await self.get_organization_prestige(achievement.organization),
            'collaborators_count': len(achievement.collaborators) if achievement.collaborators else 0,
            'has_certificate': bool(achievement.url),
            'year': achievement.date.year
        }
        
        score = self.impact_predictor.predict(features)
        return min(max(score, 0), 100)  # Clamp between 0-100
    
    async def get_organization_prestige(self, organization: str) -> float:
        """
        Get prestige score for organization (simplified)
        """
        # In production, this would query a database of organization rankings
        prestigious_orgs = {
            'IEEE': 90,
            'ACM': 90,
            'Nature': 95,
            'Science': 95,
            'MIT': 95,
            'Stanford': 95
        }
        
        for org, score in prestigious_orgs.items():
            if org.lower() in organization.lower():
                return score
        
        return 50  # Default score
    
    async def request_verification(self, achievement: Achievement):
        """
        Submit achievement for verification
        """
        # In production, this would:
        # 1. Send to admin panel for review
        # 2. Use ML to auto-verify if confidence is high
        # 3. Send email notifications
        pass
    
    async def export_to_csv(self, achievements: List[Achievement]) -> str:
        """
        Export achievements to CSV format
        """
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'Title', 'Category', 'Organization', 'Date', 
            'Impact Score', 'Verified', 'Tags', 'URL'
        ])
        
        # Data
        for achievement in achievements:
            writer.writerow([
                achievement.title,
                achievement.category,
                achievement.organization,
                achievement.date.strftime('%Y-%m-%d'),
                achievement.impact_score or 0,
                'Yes' if achievement.verified else 'No',
                ','.join(achievement.tags) if achievement.tags else '',
                achievement.url or ''
            ])
        
        return output.getvalue()
    
    async def export_to_pdf(self, achievements: List[Achievement]) -> bytes:
        """
        Export achievements to PDF format
        """
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        styles = getSampleStyleSheet()
        
        # Title
        title = Paragraph("Achievement Portfolio", styles['Title'])
        elements.append(title)
        
        # Table data
        data = [['Title', 'Category', 'Organization', 'Date', 'Impact']]
        for achievement in achievements:
            data.append([
                achievement.title[:40],
                achievement.category,
                achievement.organization[:30],
                achievement.date.strftime('%Y-%m-%d'),
                str(achievement.impact_score or 0)
            ])
        
        # Create table
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        doc.build(elements)
        
        return buffer.getvalue()
    
    async def log_activity(self, faculty_id: str, action: str, achievement_id: str):
        """
        Log achievement-related activity
        """
        # In production, this would log to activity tracking system
        pass