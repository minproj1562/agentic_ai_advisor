# app/models/__init__.py
from .student import StudentPerformance, StudentInfo, Subject, TrendEnum
from .student_projects import StudentProject, StudentInterestProfile, ProjectType, TeamMember, ProjectFile, InferredInterest
from .student_profile import StudentProfile, SemesterRecord, SubjectScore, Branch, Grade
from .resource import StudyResource
from .research_area import ResearchArea, ResearchCategory, ExpertiseLevel, ProjectStatus, SubArea, ResearchProject, Expertise, Impact, TrendData
from .publications import Publication, PublicationType, PublicationStatus, CitationTrend, Collaborator, SupplementaryMaterial
from .elective import Elective, InstructorInfo, DifficultyLevel, ElectiveCategory
from .messages import Message, Conversation
from .weakness import WeaknessAnalysisResult, TopicAnalysis
from .analytics import Analytics
from .mentorship import (
    MentorshipSlot, MentorshipSession, FacultyMentorshipSettings, 
    MentorshipStatistics, MentorshipSlotType, MentorshipSessionStatus, 
    SessionTopic, AvailabilityDay
)

__all__ = [
    "StudentPerformance", "StudentInfo", "Subject", "TrendEnum",
    "StudentProject", "StudentInterestProfile", "ProjectType", "TeamMember", "ProjectFile", "InferredInterest",
    "StudentProfile", "SemesterRecord", "SubjectScore", "Branch", "Grade",
    "StudyResource",
    "ResearchArea", "ResearchCategory", "ExpertiseLevel", "ProjectStatus", "SubArea", "ResearchProject", "Expertise", "Impact", "TrendData",
    "Publication", "PublicationType", "PublicationStatus", "CitationTrend", "Collaborator", "SupplementaryMaterial",
    "Elective", "InstructorInfo", "DifficultyLevel", "ElectiveCategory",
    "Message", "Conversation",
    "WeaknessAnalysisResult", "TopicAnalysis",
    "Analytics", 
    "MentorshipSlot", "MentorshipSession", "FacultyMentorshipSettings", "MentorshipStatistics",
    "MentorshipSlotType", "MentorshipSessionStatus", "SessionTopic", "AvailabilityDay"
]