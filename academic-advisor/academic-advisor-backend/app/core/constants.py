# app/core/constants.py
"""
Application constants
"""

# User roles
ROLES = {
    "STUDENT": "student",
    "FACULTY": "faculty",
    "ADMIN": "admin",
    "COORDINATOR": "coordinator",
    "HOD": "hod"
}

# Departments
DEPARTMENTS = ["CS", "ECE", "MECH", "CIVIL", "EEE"]

# Risk levels
RISK_LEVELS = {
    "LOW": "low",
    "MEDIUM": "medium",
    "HIGH": "high",
    "CRITICAL": "critical"
}

# Performance categories
PERFORMANCE_CATEGORIES = {
    "EXCELLENT": {"min": 8.5, "max": 10.0},
    "GOOD": {"min": 7.0, "max": 8.49},
    "AVERAGE": {"min": 5.5, "max": 6.99},
    "POOR": {"min": 0, "max": 5.49}
}

# Severity levels for weaknesses
SEVERITY_LEVELS = ["none", "low", "medium", "high", "critical"]

# Improvement trends
IMPROVEMENT_TRENDS = ["improving", "stable", "declining"]

# Resource types
RESOURCE_TYPES = ["book", "video", "article", "tutorial", "practice", "course"]

# File upload limits
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_CV_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = ["pdf", "docx", "txt", "png", "jpg", "jpeg"]

# Cache TTL values (in seconds)
CACHE_TTL = {
    "SHORT": 300,      # 5 minutes
    "MEDIUM": 1800,    # 30 minutes
    "LONG": 3600,      # 1 hour
    "VERY_LONG": 86400 # 24 hours
}

# Pagination defaults
DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 100

# ML Model thresholds
ML_THRESHOLDS = {
    "CONFIDENCE_MIN": 0.7,
    "RISK_HIGH": 70,
    "RISK_MEDIUM": 40,
    "WEAKNESS_DETECTION": 60,
    "PASSING_SCORE": 60
}

# Attendance thresholds
ATTENDANCE_THRESHOLDS = {
    "MINIMUM": 75,
    "GOOD": 85,
    "EXCELLENT": 95
}

# CGPA thresholds
CGPA_THRESHOLDS = {
    "DISTINCTION": 8.5,
    "FIRST_CLASS": 7.0,
    "SECOND_CLASS": 5.5,
    "PASS": 5.0
}

# Notification types
NOTIFICATION_TYPES = [
    "performance_alert",
    "attendance_warning",
    "risk_alert",
    "recommendation",
    "announcement",
    "intervention",
    "achievement"
]

# Email templates
EMAIL_TEMPLATES = {
    "WELCOME": "welcome_email.html",
    "RISK_ALERT": "risk_alert_email.html",
    "PERFORMANCE_UPDATE": "performance_update_email.html",
    "INTERVENTION": "intervention_email.html"
}

# API rate limits
RATE_LIMITS = {
    "DEFAULT": {"requests": 100, "period": 60},
    "AUTH": {"requests": 10, "period": 60},
    "UPLOAD": {"requests": 20, "period": 60},
    "EXPORT": {"requests": 10, "period": 60}
}

# WebSocket settings
WS_SETTINGS = {
    "HEARTBEAT_INTERVAL": 30,
    "CONNECTION_TIMEOUT": 600,
    "MAX_CONNECTIONS_PER_USER": 5,
    "MESSAGE_QUEUE_SIZE": 100
}

# Export formats
EXPORT_FORMATS = ["csv", "excel", "pdf", "json"]

# Time ranges for analysis
TIME_RANGES = ["all", "current", "last_year", "last_semester"]

# Grading system
GRADE_POINTS = {
    "S": 10,
    "A": 9,
    "B": 8,
    "C": 7,
    "D": 6,
    "E": 5,
    "F": 0
}

# Course types
COURSE_TYPES = ["core", "elective", "minor", "audit", "project"]

# Difficulty levels
DIFFICULTY_LEVELS = ["easy", "medium", "hard", "expert"]

# Career paths by department
CAREER_PATHS = {
    "CS": [
        "Software Developer",
        "Data Scientist",
        "ML Engineer",
        "DevOps Engineer",
        "Full Stack Developer",
        "System Architect"
    ],
    "ECE": [
        "Embedded Systems Engineer",
        "VLSI Designer",
        "Signal Processing Engineer",
        "Network Engineer",
        "IoT Developer"
    ],
    "MECH": [
        "Design Engineer",
        "Manufacturing Engineer",
        "Quality Engineer",
        "R&D Engineer",
        "Project Manager"
    ],
    "CIVIL": [
        "Structural Engineer",
        "Construction Manager",
        "Urban Planner",
        "Transportation Engineer",
        "Environmental Engineer"
    ],
    "EEE": [
        "Power Systems Engineer",
        "Control Systems Engineer",
        "Electrical Design Engineer",
        "Renewable Energy Engineer"
    ]
}

# Skills by department
DEPARTMENT_SKILLS = {
    "CS": [
        "Python", "Java", "JavaScript", "C++",
        "Data Structures", "Algorithms", "Machine Learning",
        "Web Development", "Database Management", "Cloud Computing"
    ],
    "ECE": [
        "VHDL", "Verilog", "Embedded C", "MATLAB",
        "Circuit Design", "Signal Processing", "Microcontrollers",
        "Communication Systems", "VLSI Design"
    ],
    "MECH": [
        "CAD/CAM", "SolidWorks", "ANSYS", "MATLAB",
        "Thermodynamics", "Fluid Mechanics", "Manufacturing",
        "Material Science", "Robotics"
    ],
    "CIVIL": [
        "AutoCAD", "STAAD Pro", "Primavera", "Revit",
        "Structural Analysis", "Construction Management",
        "Surveying", "Transportation Engineering"
    ],
    "EEE": [
        "MATLAB", "Simulink", "PLC Programming", "SCADA",
        "Power Systems", "Control Systems", "Electrical Machines",
        "Power Electronics", "Renewable Energy"
    ]
}
# ═══════════════════════════════════════════════════════════════
#  OPEN ELECTIVE CONSTANTS (Semester VII)
# ═══════════════════════════════════════════════════════════════

OPEN_ELECTIVE_CODES = {
    "RE": "OEC7012",
    "OR": "OEC7015",
    "CSL": "OEC7016",
    "DBM": "OEC7017",
    "EAM": "OEC7018",
}

OPEN_ELECTIVE_NAMES = {
    "OEC7012": "Reliability Engineering",
    "OEC7015": "Operation Research",
    "OEC7016": "Cyber Security and Laws",
    "OEC7017": "Digital Business Management",
    "OEC7018": "Energy Audit and Management",
}

OPEN_ELECTIVE_LABELS = ["RE", "OR", "CSL", "DBM", "EAM"]

# Currently offered OECs for SH-2026 (Sem VII)
OFFERED_OEC_SEM7_2026 = list(OPEN_ELECTIVE_CODES.keys())