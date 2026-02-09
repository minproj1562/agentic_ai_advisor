# app/models/__init__.py
"""
Models package - exports all Beanie document models
"""

# Import from student.py (primary source for StudentPerformance)
from .student import StudentPerformance, StudentInfo, Subject, TrendEnum

# Don't import from student_performance.py to avoid duplicate
# The student_performance.py file has duplicate definitions

# Student projects
from .student_projects import (
    StudentProject, 
    StudentInterestProfile as ProjectInterestProfile,  # Rename to avoid conflict
    ProjectType, 
    TeamMember, 
    ProjectFile, 
    InferredInterest
)

# Student profile
from .student_profile import (
    StudentProfile,
    SemesterRecord,
    SubjectScore,
    Branch,
    Grade
)

# Resources
from .resource import StudyResource

# Research & Publications
from .research_area import (
    ResearchArea, 
    ResearchCategory, 
    ExpertiseLevel, 
    ProjectStatus, 
    SubArea, 
    ResearchProject, 
    Expertise, 
    Impact, 
    TrendData
)
from .publications import (
    Publication, 
    PublicationType, 
    PublicationStatus, 
    CitationTrend, 
    Collaborator, 
    SupplementaryMaterial
)

# Academic
from .elective import Elective, DifficultyLevel, ElectiveCategory

# Messaging
from .messages import Message, Conversation

# Weakness
from .weakness import (
    WeaknessAnalysisResult, 
    TopicAnalysis,
    StudentInterestProfile,  # This is from weakness.py
    WeaknessArea,
    SeverityLevel,
    AnalysisBasis
)

# Analytics
from .analytics import Analytics

# Mentorship
from .mentorship import (
    MentorshipSlot, 
    MentorshipSession, 
    FacultyMentorshipSettings, 
    MentorshipStatistics, 
    MentorshipSlotType, 
    MentorshipSessionStatus, 
    SessionTopic, 
    AvailabilityDay
)

# Faculty
from .faculty import (
    Faculty, 
    FacultyStatus, 
    Qualification, 
    MeetingSlot,
    UniformFacultyProfile,
    PersonalInfo,
    AcademicQualifications,
    CurrentPosition,
    ResearchExpertise,
    TeachingInfo,
    FacultyAvailability,
    PublicationSummary,
    Degree
)

# Meeting Requests
from .meeting_request import (
    MeetingRequest,
    MeetingRequestStatus,
    ScheduledMeeting
)

__all__ = [
    # Student
    "StudentPerformance", "StudentInfo", "Subject", "TrendEnum",
    "StudentProject", "ProjectInterestProfile", "ProjectType", "TeamMember", "ProjectFile", "InferredInterest",
    "StudentProfile", "SemesterRecord", "SubjectScore", "Branch", "Grade",
    
    # Resources
    "StudyResource",
    
    # Research & Publications
    "ResearchArea", "ResearchCategory", "ExpertiseLevel", "ProjectStatus", 
    "SubArea", "ResearchProject", "Expertise", "Impact", "TrendData",
    "Publication", "PublicationType", "PublicationStatus", "CitationTrend", 
    "Collaborator", "SupplementaryMaterial",
    
    # Academic
    "Elective", "InstructorInfo", "DifficultyLevel", "ElectiveCategory",
    
    # Messaging
    "Message", "Conversation",
    
    # Weakness & Analysis
    "WeaknessAnalysisResult", "TopicAnalysis", "StudentInterestProfile",
    "WeaknessArea", "SeverityLevel", "AnalysisBasis",
    
    # Analytics
    "Analytics", 
    
    # Mentorship
    "MentorshipSlot", "MentorshipSession", "FacultyMentorshipSettings", 
    "MentorshipStatistics", "MentorshipSlotType", "MentorshipSessionStatus", 
    "SessionTopic", "AvailabilityDay",
    
    # Faculty
    "Faculty", "FacultyStatus", "Qualification", "MeetingSlot",
    "UniformFacultyProfile", "PersonalInfo", "AcademicQualifications", 
    "CurrentPosition", "ResearchExpertise", "TeachingInfo", 
    "FacultyAvailability", "PublicationSummary", "Degree",
      
    # Meeting Requests
    "MeetingRequest", "MeetingRequestStatus", "ScheduledMeeting",
]