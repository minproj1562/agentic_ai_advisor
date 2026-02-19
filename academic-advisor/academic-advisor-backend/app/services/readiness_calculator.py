# app/services/readiness_calculator.py
"""
Academic Readiness Calculator

Implements the core readiness scoring logic from the Master Prompt:
- Step 5: Calculate readiness score (0-100)
- Step 8: Generate safe recommendation

A student is considered "ready" if:
- No critical weaknesses
- Overall readiness score >= 70
- All critical prerequisites met
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging

from app.core.subject_mappings import (
    SubjectRequirement,
    AcademicTarget,
    ImportanceLevel,
    RequirementSource,
    get_subject_mapping_service
)
from app.models.weakness import SeverityLevel

logger = logging.getLogger(__name__)


class ReadinessLevel(str, Enum):
    """Overall readiness classification"""
    EXCELLENT = "excellent"      # 90-100: Ready, likely to excel
    GOOD = "good"                # 75-89: Ready, should perform well
    MODERATE = "moderate"        # 60-74: Needs some improvement
    LOW = "low"                  # 40-59: Significant gaps
    NOT_READY = "not_ready"      # 0-39: Should not proceed


class RecommendationType(str, Enum):
    """Types of recommendations"""
    PROCEED = "proceed"                    # Ready to proceed
    PROCEED_WITH_CAUTION = "proceed_with_caution"  # Can proceed but monitor
    IMPROVE_FIRST = "improve_first"        # Should improve before proceeding
    DO_NOT_PROCEED = "do_not_proceed"      # Should not proceed yet


@dataclass
class SubjectGap:
    """Gap analysis for a single subject"""
    subject_name: str
    required_score: float
    actual_score: float
    gap: float                    # required - actual
    gap_percentage: float         # gap as percentage
    importance: ImportanceLevel
    weight: float
    source: str                   # What requires this (interest/elective/honours)
    is_studied: bool             # Has the student studied this subject?
    confidence: float            # Confidence in this assessment (lower for unstudied)
    severity: SeverityLevel
    contributes_to: List[str]    # List of interests/electives this affects


@dataclass
class ReadinessResult:
    """Complete readiness analysis result"""
    student_id: str
    analysis_timestamp: str
    
    # Scores
    overall_readiness_score: float      # 0-100
    interest_readiness_score: float     # 0-100 for interests
    elective_readiness_score: float     # 0-100 for electives  
    honours_readiness_score: float      # 0-100 for honours
    
    # Classification
    readiness_level: ReadinessLevel
    recommendation_type: RecommendationType
    
    # Gap Analysis
    all_gaps: List[SubjectGap]
    critical_gaps: List[SubjectGap]
    high_gaps: List[SubjectGap]
    
    # Counts
    total_requirements: int
    met_requirements: int
    partially_met: int
    not_met: int
    not_studied: int
    
    # Flags
    has_critical_weakness: bool
    has_blockers: bool              # Subjects that completely block progress
    is_first_semester: bool
    
    # Recommendations
    primary_recommendation: str
    detailed_recommendations: List[str]
    subjects_to_focus: List[str]
    estimated_preparation_time: str
    
    # Per-target readiness
    interest_breakdown: Dict[str, float]     # Interest name -> readiness %
    elective_breakdown: Dict[str, float]     # Elective name -> readiness %
    honours_breakdown: Dict[str, float]      # Honours name -> readiness %


class ReadinessCalculator:
    """
    Calculate academic readiness based on the Master Prompt specifications.
    """
    
    # Score thresholds for classification
    READINESS_THRESHOLDS = {
        ReadinessLevel.EXCELLENT: 90,
        ReadinessLevel.GOOD: 75,
        ReadinessLevel.MODERATE: 60,
        ReadinessLevel.LOW: 40,
        ReadinessLevel.NOT_READY: 0
    }
    
    # Gap thresholds for severity classification
    GAP_SEVERITY_THRESHOLDS = {
        SeverityLevel.CRITICAL: 30,    # Gap > 30 points
        SeverityLevel.HIGH: 20,        # Gap > 20 points
        SeverityLevel.MEDIUM: 10,      # Gap > 10 points
        SeverityLevel.LOW: 0           # Any gap
    }
    
    def __init__(self):
        self.mapping_service = get_subject_mapping_service()
        self.logger = logger
    
    def calculate_readiness(
        self,
        student_id: str,
        student_scores: Dict[str, float],
        interests: List[str],
        electives: List[str],
        honours_minors: List[str],
        current_semester: int = 1,
        cgpa: float = 0.0
    ) -> ReadinessResult:
        """
        Main method to calculate overall readiness.
        
        Implements Steps 2-8 of the Master Prompt:
        - Step 2: Match student performance
        - Step 3: Find gaps (weaknesses)
        - Step 4: Assign severity
        - Step 5: Calculate readiness score
        - Step 6: Prioritize weaknesses
        - Step 7: Create study plan guidance
        - Step 8: Give safe recommendation
        """
        
        # Step 1: Build academic target profile (done via mapping service)
        target_profile = self.mapping_service.build_academic_target_profile(
            student_id=student_id,
            interests=interests,
            electives=electives,
            honours_minors=honours_minors
        )
        
        # Check if first semester student
        is_first_semester = current_semester <= 1
        
        # Step 2 & 3: Match performance and find gaps
        all_gaps = self._calculate_all_gaps(
            target_profile.merged_requirements,
            student_scores,
            is_first_semester
        )
        
        # Step 4: Assign severity (already done in _calculate_all_gaps)
        
        # Separate gaps by severity
        critical_gaps = [g for g in all_gaps if g.severity == SeverityLevel.CRITICAL]
        high_gaps = [g for g in all_gaps if g.severity == SeverityLevel.HIGH]
        
        # Step 5: Calculate readiness scores
        overall_score = self._calculate_overall_readiness(all_gaps)
        
        # Calculate per-category scores
        interest_score, interest_breakdown = self._calculate_category_readiness(
            interests, 
            student_scores, 
            RequirementSource.INTEREST,
            is_first_semester
        )
        elective_score, elective_breakdown = self._calculate_category_readiness(
            electives,
            student_scores,
            RequirementSource.ELECTIVE,
            is_first_semester
        )
        honours_score, honours_breakdown = self._calculate_category_readiness(
            honours_minors,
            student_scores,
            RequirementSource.HONOURS,
            is_first_semester
        )
        
        # Determine readiness level
        readiness_level = self._classify_readiness(overall_score)
        
        # Check for blockers
        has_critical = len(critical_gaps) > 0
        has_blockers = any(
            g.importance == ImportanceLevel.CRITICAL and g.gap > 25
            for g in all_gaps
        )
        
        # Count requirements
        total_reqs = len(all_gaps)
        met_reqs = len([g for g in all_gaps if g.gap <= 0])
        partial_reqs = len([g for g in all_gaps if 0 < g.gap <= 15])
        not_met = len([g for g in all_gaps if g.gap > 15])
        not_studied = len([g for g in all_gaps if not g.is_studied])
        
        # Step 8: Generate safe recommendation
        rec_type, primary_rec, detailed_recs = self._generate_recommendation(
            overall_score=overall_score,
            readiness_level=readiness_level,
            critical_gaps=critical_gaps,
            high_gaps=high_gaps,
            has_blockers=has_blockers,
            is_first_semester=is_first_semester,
            cgpa=cgpa,
            interests=interests,
            electives=electives,
            honours_minors=honours_minors
        )
        
        # Step 6: Prioritize weaknesses (sort subjects to focus)
        subjects_to_focus = self._prioritize_subjects(all_gaps)
        
        # Estimate preparation time
        prep_time = self._estimate_preparation_time(all_gaps)
        
        return ReadinessResult(
            student_id=student_id,
            analysis_timestamp=datetime.utcnow().isoformat(),
            overall_readiness_score=round(overall_score, 1),
            interest_readiness_score=round(interest_score, 1),
            elective_readiness_score=round(elective_score, 1),
            honours_readiness_score=round(honours_score, 1),
            readiness_level=readiness_level,
            recommendation_type=rec_type,
            all_gaps=all_gaps,
            critical_gaps=critical_gaps,
            high_gaps=high_gaps,
            total_requirements=total_reqs,
            met_requirements=met_reqs,
            partially_met=partial_reqs,
            not_met=not_met,
            not_studied=not_studied,
            has_critical_weakness=has_critical,
            has_blockers=has_blockers,
            is_first_semester=is_first_semester,
            primary_recommendation=primary_rec,
            detailed_recommendations=detailed_recs,
            subjects_to_focus=subjects_to_focus,
            estimated_preparation_time=prep_time,
            interest_breakdown=interest_breakdown,
            elective_breakdown=elective_breakdown,
            honours_breakdown=honours_breakdown
        )
    
    def _calculate_all_gaps(
        self,
        requirements: Dict[str, SubjectRequirement],
        student_scores: Dict[str, float],
        is_first_semester: bool
    ) -> List[SubjectGap]:
        """
        Calculate gaps for all requirements.
        
        Implements Step 2 & 3:
        - Match student performance
        - Handle first-semester students
        - Find gaps
        """
        gaps = []
        
        for subject_name, req in requirements.items():
            # Find student's score for this subject
            actual_score, is_studied, confidence = self._find_student_score(
                student_scores,
                subject_name,
                is_first_semester
            )
            
            # Calculate gap
            gap = req.min_score - actual_score
            gap_percentage = (gap / req.min_score * 100) if req.min_score > 0 else 0
            
            # Determine severity based on gap and importance
            severity = self._determine_severity(
                gap=gap,
                gap_percentage=gap_percentage,
                importance=req.importance,
                is_studied=is_studied
            )
            
            # Extract what this contributes to
            contributes_to = [s.strip() for s in req.source_name.split(",")]
            
            subject_gap = SubjectGap(
                subject_name=subject_name,
                required_score=req.min_score,
                actual_score=actual_score,
                gap=max(0, gap),  # Only positive gaps
                gap_percentage=max(0, gap_percentage),
                importance=req.importance,
                weight=req.weight,
                source=req.source_name,
                is_studied=is_studied,
                confidence=confidence,
                severity=severity if gap > 0 else SeverityLevel.LOW,
                contributes_to=contributes_to
            )
            
            gaps.append(subject_gap)
        
        return gaps
    
    def _find_student_score(
        self,
        student_scores: Dict[str, float],
        target_subject: str,
        is_first_semester: bool
    ) -> Tuple[float, bool, float]:
        """
        Find student's score for a subject.
        
        Returns: (score, is_studied, confidence)
        
        For first-semester students or unstudied subjects:
        - Score is 0
        - Confidence is lower
        """
        canonical = self.mapping_service.get_canonical_subject_name(target_subject)
        target_lower = canonical.lower()
        
        # Try exact match
        for subject, data in student_scores.items():
            subject_lower = subject.lower()
            
            # Direct match
            if subject_lower == target_lower:
                score = data if isinstance(data, (int, float)) else data.get('score', 0)
                return (score, True, 0.95)
            
            # Partial match
            if target_lower in subject_lower or subject_lower in target_lower:
                score = data if isinstance(data, (int, float)) else data.get('score', 0)
                return (score, True, 0.85)
        
        # Check aliases
        aliases = {
            "engineering mathematics-iii": ["math-3", "math iii", "applied math"],
            "engineering mathematics-iv": ["math-4", "math iv", "statistics"],
            "data structures and algorithms": ["dsa", "data structures", "ds"],
            "database management systems": ["dbms", "database"],
            "operating systems": ["os", "operating system"],
            "computer networks": ["cn", "networks", "networking"],
            "python programming": ["python", "py programming"],
        }
        
        for canonical_name, alias_list in aliases.items():
            if target_lower in canonical_name or any(a in target_lower for a in alias_list):
                for subject, data in student_scores.items():
                    subject_lower = subject.lower()
                    if canonical_name in subject_lower or any(a in subject_lower for a in alias_list):
                        score = data if isinstance(data, (int, float)) else data.get('score', 0)
                        return (score, True, 0.8)
        
        # Subject not found
        if is_first_semester:
            # First semester students haven't studied most subjects
            return (0, False, 0.5)
        else:
            # Later semester students should have studied core subjects
            return (0, False, 0.6)
    
    def _determine_severity(
        self,
        gap: float,
        gap_percentage: float,
        importance: ImportanceLevel,
        is_studied: bool
    ) -> SeverityLevel:
        """
        Determine severity based on gap and importance.
        
        Implements Step 4: Assign severity
        """
        if gap <= 0:
            return SeverityLevel.LOW
        
        # Base severity on gap size
        if gap >= 30:
            base_severity = SeverityLevel.CRITICAL
        elif gap >= 20:
            base_severity = SeverityLevel.HIGH
        elif gap >= 10:
            base_severity = SeverityLevel.MEDIUM
        else:
            base_severity = SeverityLevel.LOW
        
        # Adjust based on importance
        if importance == ImportanceLevel.CRITICAL:
            # Critical subjects escalate severity
            severity_order = [SeverityLevel.LOW, SeverityLevel.MEDIUM, SeverityLevel.HIGH, SeverityLevel.CRITICAL]
            current_idx = severity_order.index(base_severity)
            if current_idx < len(severity_order) - 1:
                base_severity = severity_order[min(current_idx + 1, len(severity_order) - 1)]
        elif importance == ImportanceLevel.LOW:
            # Low importance de-escalates
            severity_order = [SeverityLevel.LOW, SeverityLevel.MEDIUM, SeverityLevel.HIGH, SeverityLevel.CRITICAL]
            current_idx = severity_order.index(base_severity)
            if current_idx > 0:
                base_severity = severity_order[current_idx - 1]
        
        # If not studied, slightly reduce severity (they haven't had a chance yet)
        if not is_studied and base_severity == SeverityLevel.CRITICAL:
            base_severity = SeverityLevel.HIGH
        
        return base_severity
    
    def _calculate_overall_readiness(
        self,
        all_gaps: List[SubjectGap]
    ) -> float:
        """
        Calculate overall readiness score (0-100).
        
        Implements Step 5: Calculate readiness
        
        Formula:
        - Start with 100
        - Subtract weighted penalties for each gap
        - Critical gaps have higher penalties
        - Account for confidence
        """
        if not all_gaps:
            return 100.0
        
        total_weight = sum(g.weight for g in all_gaps)
        if total_weight == 0:
            return 100.0
        
        weighted_readiness = 0
        
        for gap in all_gaps:
            # Calculate how "ready" this subject is (0-100)
            if gap.gap <= 0:
                subject_readiness = 100
            else:
                # Higher gap = lower readiness
                # Map gap to readiness: 0 gap = 100 ready, 50+ gap = 0 ready
                subject_readiness = max(0, 100 - (gap.gap * 2))
            
            # Apply severity multiplier
            severity_multiplier = {
                SeverityLevel.CRITICAL: 0.6,  # Critical gaps hurt more
                SeverityLevel.HIGH: 0.8,
                SeverityLevel.MEDIUM: 0.9,
                SeverityLevel.LOW: 1.0
            }
            
            adjusted_readiness = subject_readiness * severity_multiplier.get(gap.severity, 1.0)
            
            # Apply confidence
            confidence_adjusted = adjusted_readiness * gap.confidence
            
            # Weight by importance
            weighted_readiness += confidence_adjusted * gap.weight
        
        # Normalize
        overall = weighted_readiness / total_weight
        
        return min(100, max(0, overall))
    
    def _calculate_category_readiness(
        self,
        items: List[str],
        student_scores: Dict[str, float],
        source_type: RequirementSource,
        is_first_semester: bool
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculate readiness for a specific category (interests/electives/honours).
        
        Returns: (average_score, breakdown_dict)
        """
        if not items:
            return (100.0, {})
        
        breakdown = {}
        
        for item in items:
            # Get requirements for this item
            if source_type == RequirementSource.INTEREST:
                reqs = self.mapping_service.get_requirements_for_interest(item)
            elif source_type == RequirementSource.ELECTIVE:
                reqs = self.mapping_service.get_requirements_for_elective(item)
            else:
                reqs = self.mapping_service.get_requirements_for_honours(item)
            
            if not reqs:
                breakdown[item] = 100.0
                continue
            
            # Calculate gaps for this item's requirements
            item_gaps = []
            for req in reqs:
                actual_score, is_studied, confidence = self._find_student_score(
                    student_scores,
                    req.subject_name,
                    is_first_semester
                )
                
                gap = max(0, req.min_score - actual_score)
                
                item_gaps.append(SubjectGap(
                    subject_name=req.subject_name,
                    required_score=req.min_score,
                    actual_score=actual_score,
                    gap=gap,
                    gap_percentage=(gap / req.min_score * 100) if req.min_score > 0 else 0,
                    importance=req.importance,
                    weight=req.weight,
                    source=item,
                    is_studied=is_studied,
                    confidence=confidence,
                    severity=self._determine_severity(gap, 0, req.importance, is_studied),
                    contributes_to=[item]
                ))
            
            # Calculate readiness for this item
            item_readiness = self._calculate_overall_readiness(item_gaps)
            breakdown[item] = round(item_readiness, 1)
        
        # Average across all items
        avg_score = sum(breakdown.values()) / len(breakdown) if breakdown else 100.0
        
        return (avg_score, breakdown)
    
    def _classify_readiness(self, score: float) -> ReadinessLevel:
        """Classify readiness score into a level."""
        if score >= 90:
            return ReadinessLevel.EXCELLENT
        elif score >= 75:
            return ReadinessLevel.GOOD
        elif score >= 60:
            return ReadinessLevel.MODERATE
        elif score >= 40:
            return ReadinessLevel.LOW
        else:
            return ReadinessLevel.NOT_READY
    
    def _generate_recommendation(
        self,
        overall_score: float,
        readiness_level: ReadinessLevel,
        critical_gaps: List[SubjectGap],
        high_gaps: List[SubjectGap],
        has_blockers: bool,
        is_first_semester: bool,
        cgpa: float,
        interests: List[str],
        electives: List[str],
        honours_minors: List[str]
    ) -> Tuple[RecommendationType, str, List[str]]:
        """
        Generate safe recommendation based on analysis.
        
        Implements Step 8: Give safe recommendation
        
        If critical weaknesses or low readiness → recommend NOT to proceed
        If good readiness → recommend to proceed
        """
        detailed_recs = []
        
        # Case 1: Critical blockers - DO NOT PROCEED
        if has_blockers and critical_gaps:
            critical_subjects = [g.subject_name for g in critical_gaps[:3]]
            
            if honours_minors:
                primary = f"⚠️ NOT RECOMMENDED to pursue {', '.join(honours_minors[:2])} at this time. " \
                         f"Critical gaps in: {', '.join(critical_subjects)}."
            elif electives:
                primary = f"⚠️ NOT RECOMMENDED to choose {', '.join(electives[:2])}. " \
                         f"Must first improve: {', '.join(critical_subjects)}."
            else:
                primary = f"⚠️ Significant academic gaps require immediate attention. " \
                         f"Focus on: {', '.join(critical_subjects)}."
            
            detailed_recs.append("Address critical subject gaps before proceeding")
            detailed_recs.append(f"Focus intensive study on {critical_subjects[0]}")
            detailed_recs.append("Consider tutoring or additional support")
            detailed_recs.append("Reasses in 6-8 weeks after improvement")
            
            return (RecommendationType.DO_NOT_PROCEED, primary, detailed_recs)
        
        # Case 2: Critical gaps but no blockers - IMPROVE FIRST
        if critical_gaps:
            critical_subjects = [g.subject_name for g in critical_gaps[:2]]
            
            primary = f"⚠️ Improvement needed before pursuing selected goals. " \
                     f"Priority areas: {', '.join(critical_subjects)}."
            
            detailed_recs.append("Create dedicated study plan for critical subjects")
            detailed_recs.append("Aim to reach minimum required scores before next semester")
            detailed_recs.append("Consider lighter course load to focus on improvement")
            
            return (RecommendationType.IMPROVE_FIRST, primary, detailed_recs)
        
        # Case 3: High gaps only - PROCEED WITH CAUTION
        if high_gaps and readiness_level in [ReadinessLevel.MODERATE, ReadinessLevel.LOW]:
            high_subjects = [g.subject_name for g in high_gaps[:2]]
            
            primary = f"✓ Can proceed with caution. Monitor progress in: {', '.join(high_subjects)}."
            
            detailed_recs.append("You can pursue your selected interests/electives")
            detailed_recs.append("Allocate extra study time for weak areas")
            detailed_recs.append("Seek help early if struggling")
            
            return (RecommendationType.PROCEED_WITH_CAUTION, primary, detailed_recs)
        
        # Case 4: Good readiness - PROCEED
        if readiness_level in [ReadinessLevel.EXCELLENT, ReadinessLevel.GOOD]:
            if honours_minors:
                primary = f"✅ Ready to pursue {', '.join(honours_minors[:2])}! " \
                         f"Strong foundation detected."
            elif electives:
                primary = f"✅ Ready for selected electives: {', '.join(electives[:2])}. " \
                         f"Prerequisites are well covered."
            else:
                primary = f"✅ Strong academic foundation for your interests. " \
                         f"Continue your current study approach."
            
            detailed_recs.append("You are well-prepared for your academic goals")
            detailed_recs.append("Maintain current study habits")
            if high_gaps:
                detailed_recs.append(f"Minor improvement in {high_gaps[0].subject_name} could help further")
            
            return (RecommendationType.PROCEED, primary, detailed_recs)
        
        # Case 5: First semester special handling
        if is_first_semester:
            primary = "📘 As a first-semester student, focus on building strong foundations. " \
                     "Your interests are noted and we'll track your readiness as you progress."
            
            detailed_recs.append("Focus on excelling in current semester subjects")
            detailed_recs.append("Build strong fundamentals in Mathematics and Programming")
            detailed_recs.append("Explore your interests through online resources")
            detailed_recs.append("Readiness will be recalculated as you complete more subjects")
            
            return (RecommendationType.PROCEED_WITH_CAUTION, primary, detailed_recs)
        
        # Default case
        primary = "✓ Moderate readiness detected. You can proceed with awareness of gaps."
        detailed_recs.append("Review weak areas alongside new subjects")
        detailed_recs.append("Build study groups for challenging topics")
        
        return (RecommendationType.PROCEED_WITH_CAUTION, primary, detailed_recs)
    
    def _prioritize_subjects(
        self,
        all_gaps: List[SubjectGap]
    ) -> List[str]:
        """
        Prioritize subjects to focus on.
        
        Implements Step 6: Prioritize weaknesses
        
        Priority based on:
        1. Severity (critical first)
        2. Importance weight
        3. Number of things it affects
        """
        # Filter to only gaps
        actual_gaps = [g for g in all_gaps if g.gap > 0]
        
        if not actual_gaps:
            return []
        
        # Sort by priority
        sorted_gaps = sorted(
            actual_gaps,
            key=lambda g: (
                # Severity order (critical = 3, high = 2, etc.)
                -({'critical': 3, 'high': 2, 'medium': 1, 'low': 0}.get(g.severity.value, 0)),
                # Weight (higher = more important)
                -g.weight,
                # Number of things affected
                -len(g.contributes_to),
                # Gap size
                -g.gap
            )
        )
        
        return [g.subject_name for g in sorted_gaps[:5]]
    
    def _estimate_preparation_time(
        self,
        all_gaps: List[SubjectGap]
    ) -> str:
        """
        Estimate time needed to address all gaps.
        
        Based on gap size and count.
        """
        actual_gaps = [g for g in all_gaps if g.gap > 0]
        
        if not actual_gaps:
            return "No preparation needed"
        
        # Calculate total "gap points"
        total_gap_points = sum(
            g.gap * (2 if g.importance == ImportanceLevel.CRITICAL else 1)
            for g in actual_gaps
        )
        
        # Rough estimation: 2 hours per gap point
        total_hours = total_gap_points * 2
        
        if total_hours < 20:
            return "1-2 weeks"
        elif total_hours < 50:
            return "3-4 weeks"
        elif total_hours < 100:
            return "6-8 weeks"
        elif total_hours < 200:
            return "2-3 months"
        else:
            return "3-4 months of dedicated effort"


# Singleton instance
_calculator: Optional[ReadinessCalculator] = None

def get_readiness_calculator() -> ReadinessCalculator:
    """Get singleton instance of ReadinessCalculator"""
    global _calculator
    if _calculator is None:
        _calculator = ReadinessCalculator()
    return _calculator