# AI Student Guidance System

## 🎓 Project Title
**AI Student Guidance System: Intelligent Course and Faculty Recommendation Platform for Engineering Students**

## 📋 Table of Contents
- [Project Overview](#project-overview)
- [Motivation](#motivation)
- [Abstract](#abstract)
- [Objectives](#objectives)
- [Domain](#domain)
- [Technology Stack](#technology-stack)
- [Project Category](#project-category)
- [SDG & PSO Mapping](#sustainable-development-goal--program-specific-outcomes)
- [System Architecture](#system-architecture)
- [Installation & Setup](#installation--setup)
- [Project Structure](#project-structure)
- [Key Features](#key-features)
- [API Documentation](#api-documentation)
- [Development Guidelines](#development-guidelines)

## 🚀 Project Overview

An AI-powered platform that provides personalized academic and faculty guidance to engineering students. The system analyzes academic performance, recommends optimal courses/electives, matches students with suitable faculty mentors, and provides intelligent career guidance through AI-driven insights.

## 🎯 Motivation

Engineering students often struggle with course selection, elective choices, and faculty mentoring due to inadequate guidance systems. Poor academic decisions can lead to suboptimal grades, lower CGPA, and misalignment with career goals. Current academic systems primarily function as record-keeping tools without providing intelligent, data-driven recommendations.

Our motivation is to bridge this gap by creating an AI-based system that:
- Analyzes academic performance patterns
- Provides personalized course and elective recommendations
- Matches students with faculty based on expertise and teaching style
- Offers real-time academic advising through AI chatbots
- Enhances educational outcomes through data-driven insights

## 📝 Abstract

The AI Student Guidance System is a comprehensive web-based application where students can:
- Upload and analyze academic records
- Receive personalized course and specialization recommendations
- Get matched with suitable faculty mentors based on performance and interests
- Interact with an AI-powered chatbot for real-time academic guidance
- Access career path recommendations and skill gap analysis

The platform integrates machine learning models for performance prediction, natural language processing for feedback analysis, and recommendation engines for optimal academic planning. It serves as a holistic academic advisor, helping students make informed decisions throughout their engineering journey.

## 🎯 Objectives

### Primary Objectives:
1. **Personalized Academic Planning**: Build an AI-driven system that analyzes student performance and recommends optimal academic pathways
2. **Faculty-Student Matching**: Develop intelligent algorithms to match students with faculty mentors based on expertise, teaching style, and student needs
3. **Real-time Academic Advising**: Implement an AI chatbot that provides instant guidance on course selection, faculty choices, and career planning
4. **Performance Analytics**: Create comprehensive dashboards for tracking academic progress and identifying improvement areas
5. **Secure Data Management**: Implement robust authentication, authorization, and data protection mechanisms

### Technical Objectives:
6. **ML Model Integration**: Deploy machine learning models for grade prediction, weakness identification, and recommendation generation
7. **Real-time Communication**: Implement WebSocket-based messaging for instant faculty-student communication
8. **Scalable Architecture**: Design a modular, scalable system supporting multiple institutions and user types
9. **Mobile-responsive Design**: Ensure seamless experience across desktop and mobile devices
10. **Third-party Integration**: Connect with external services (GitHub, LinkedIn, academic databases) for enhanced insights

## 🏛️ Domain

**Primary Domains:**
- Educational Technology (EdTech)
- Artificial Intelligence & Machine Learning
- Recommender Systems
- Data Analytics in Education
- Natural Language Processing
- Web Application Development

**Sub-domains:**
- Academic Performance Analysis
- Career Path Planning
- Mentorship Systems
- Learning Analytics
- Predictive Modeling in Education

## 💻 Technology Stack

### **Frontend**
- **Framework**: React.js 18.3.1 with TypeScript
- **Styling**: Tailwind CSS 3.4.13 + Material-UI 7.3.5
- **State Management**: React Query 5.90.2, Context API
- **Routing**: React Router DOM 6.27.0
- **Build Tool**: Vite 5.4.8
- **UI Components**: Framer Motion 11.11.9, Recharts 3.2.0
- **Form Handling**: React Hook Form 7.53.0 + Zod 4.1.5

### **Backend**
- **Framework**: FastAPI 0.104.1
- **Database**: MongoDB with Motor 3.3.2 + Beanie 1.23.6 ODM
- **Authentication**: Firebase Auth + Python-JOSE 3.3.0
- **ML/Data Science**:
  - Scikit-learn 1.3.2
  - TensorFlow 2.15.0
  - Transformers 4.35.2
  - PyTorch (via transformers)
  - Pandas 2.1.3, NumPy 1.26.2
- **Caching**: Redis 5.0.1
- **Task Queue**: Celery 5.3.4
- **Real-time**: WebSockets with Uvicorn
- **File Processing**: aiofiles 23.2.1, python-multipart 0.0.6

### **DevOps & Tools**
- **Containerization**: Docker + Docker Compose
- **Environment Management**: Python virtual environments
- **Version Control**: Git + GitHub
- **API Testing**: pytest 7.4.3 + pytest-asyncio 0.21.1
- **Code Quality**: ESLint, TypeScript strict mode
- **Deployment**: Configurable for Heroku/Render/AWS

### **Third-party Services**
- **Cloud Storage**: Firebase Storage, Cloudinary
- **Authentication**: Firebase Authentication
- **ML Services**: HuggingFace, OpenAI API (optional)
- **Analytics**: Custom analytics engine
- **Email/SMS**: Integrated notification system

## 📁 Project Category

**Type**: Application Development - Full Stack Web Application  
**Scope**: Internal Development (no external organizational involvement)  
**Complexity**: Advanced (integrating AI/ML, real-time features, multiple services)  
**Team Size**: 4-6 developers (full stack, ML, frontend specialization)

## 🌍 Sustainable Development Goal & Program Specific Outcomes

### **SDG Alignment: SDG 4 - Quality Education**
- **Target 4.3**: Ensure equal access to affordable technical, vocational, and higher education
- **Target 4.4**: Increase the number of youth with relevant skills for employment
- **Target 4.5**: Eliminate gender disparities in education
- **Target 4.7**: Ensure all learners acquire knowledge and skills needed to promote sustainable development

### **Program Specific Outcomes (PSO) Mapping:**

**PSO 1: Technical Expertise**
- Application of programming principles (Python, React, TypeScript)
- Database design and management (MongoDB, PostgreSQL concepts)
- Software engineering practices (Agile, version control, testing)
- API design and microservices architecture

**PSO 2: Emerging Technologies**
- Implementation of AI/ML models for educational analytics
- Natural Language Processing for feedback analysis
- LLM integration for intelligent chatbots
- Real-time data processing and WebSocket communication
- Cloud computing and serverless architecture concepts

**PSO 3: Professional Skills**
- Collaborative development using Git workflows
- Project management and task allocation
- Documentation and technical writing
- Problem-solving and analytical thinking
- Client requirement analysis and solution design

## 🏗️ System Architecture

### **High-Level Architecture**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway   │    │   ML Services   │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (Python)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Real-time     │    │   Database      │    │   Cache Layer   │
│   (WebSocket)   │    │   (MongoDB)     │    │   (Redis)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **Component Architecture**
1. **Presentation Layer**: React components with responsive design
2. **Application Layer**: FastAPI routers and middleware
3. **Business Logic Layer**: Service classes and managers
4. **Data Access Layer**: Beanie ODM models and repositories
5. **ML Layer**: Scikit-learn/TensorFlow models and pipelines
6. **Integration Layer**: Third-party API connectors

## 🛠️ Installation & Setup

### **Prerequisites**
- Node.js 18+ & npm 9+
- Python 3.11+
- MongoDB 6.0+
- Redis 7.0+
- Git

### **Backend Setup**

```bash
# 1. Clone the repository
git clone <repository-url>
cd academic-advisor-backend

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# On Windows:
.\venv\Scripts\Activate.ps1


# 4. Install dependencies
# Upgrade pip
python -m pip install --upgrade pip setuptools wheel

# Install requirements
pip install -r requirements.txt

# Install spaCy model
python -m spacy download en_core_web_sm

# 5. Configure environment variables
# Copy .env.example to .env and update values
cp .env.example .env

# 6. Set up Firebase credentials
# Place serviceAccountKey.json in project root

# 7. Run database migrations (if any)
python scripts/initialize_db.py

# 8. Start the development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
uvicorn app.main:app --reload

# 9. Start Celery worker (optional, for background tasks)
celery -A tasks.celery_app worker --loglevel=info

# 10. Start ML server (optional)
python ml_server.py
```

### **Frontend Setup**

```bash
# 1. Navigate to frontend directory
cd academic-advisor-frontend

# 2. Install dependencies
npm install



# 4. Start development server
npm run dev


```

### **Docker Setup**

```bash
# Using Docker Compose
docker-compose up --build

# Individual services
docker build -t academic-advisor-backend .
docker run -p 8000:8000 academic-advisor-backend
```

### **Virtual Environment Management**

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate (Windows CMD)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Deactivate
deactivate

# Delete virtual environment
# Windows PowerShell:
Remove-Item -Recurse -Force .\venv
# Mac/Linux:
rm -rf venv

# Export requirements
pip freeze > requirements.txt
```

## 📁 Project Structure

### **Backend Structure**
```
academic-advisor-backend/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── academic.py          # Academic record endpoints
│   │   │   │   ├── achievements.py      # Achievement tracking
│   │   │   │   ├── analytics.py         # Analytics endpoints
│   │   │   │   ├── appointments.py      # Appointment scheduling
│   │   │   │   ├── electives.py         # Elective recommendations
│   │   │   │   ├── messages.py          # Messaging system
│   │   │   │   ├── ml_insights.py       # ML insights API
│   │   │   │   ├── publications.py      # Publication management
│   │   │   │   ├── research_area.py     # Research area endpoints
│   │   │   │   ├── resources.py         # Learning resources
│   │   │   │   ├── students.py          # Student management
│   │   │   │   ├── student_analysis.py  # Student analysis
│   │   │   │   ├── student_projects_enhanced.py # Project management
│   │   │   │   └── weakness.py          # Weakness analysis
│   │   │   └── __init__.py
│   │   ├── api.py                       # Main API router
│   │   ├── cv.py                        # CV processing
│   │   └── messages.py                  # Message schemas
│   ├── core/
│   │   ├── cache.py                     # Redis caching
│   │   ├── config.py                    # Configuration management
│   │   ├── exceptions.py                # Custom exceptions
│   │   ├── firebase.py                  # Firebase integration
│   │   ├── security.py                  # Security utilities
│   │   └── __init__.py
│   ├── ml/
│   │   ├── elective_recommender.py      # Elective recommendation model
│   │   ├── ml_service.py                # ML service orchestrator
│   │   └── weakness_predictor.py        # Weakness prediction model
│   ├── models/
│   │   ├── academic_record.py           # Academic record model
│   │   ├── achievement.py               # Achievement model
│   │   ├── analytics.py                 # Analytics model
│   │   ├── appointment.py               # Appointment model
│   │   ├── cv.py                        # CV model
│   │   ├── elective.py                  # Elective model
│   │   ├── mentorship.py                # Mentorship model
│   │   ├── messages.py                  # Message model
│   │   ├── publications.py              # Publication model
│   │   ├── research_area.py             # Research area model
│   │   ├── resource.py                  # Resource model
│   │   ├── student.py                   # Student model
│   │   ├── student_performance.py       # Performance model
│   │   ├── student_profile.py           # Profile model
│   │   ├── student_projects.py          # Project model
│   │   ├── weakness.py                  # Weakness model
│   │   └── __init__.py
│   ├── schemas/
│   │   └── achievement.py               # Pydantic schemas
│   ├── services/
│   │   ├── academic_service.py          # Academic service
│   │   ├── achievement_service.py       # Achievement service
│   │   ├── analytics_service.py         # Analytics service
│   │   ├── appointment_service.py       # Appointment service
│   │   ├── cloudinary_service.py        # Cloudinary integration
│   │   ├── cv_parser.py                 # CV parsing service
│   │   ├── enhanced_ml_inference.py     # ML inference service
│   │   ├── messaging_service.py         # Messaging service
│   │   ├── nlp_service.py               # NLP processing
│   │   ├── publication_service.py       # Publication service
│   │   ├── recommendation_engine.py     # Recommendation engine
│   │   ├── research_service.py          # Research service
│   │   ├── resource_matcher.py          # Resource matching
│   │   ├── skill_extractor.py           # Skill extraction
│   │   ├── student_projects_service.py  # Project service
│   │   ├── websocket_manager.py         # WebSocket management
│   │   └── __init__.py
│   ├── tasks/
│   │   └── semester_updater.py          # Background tasks
│   └── utils/
│       ├── metrics.py                   # Performance metrics
│       ├── validators.py                # Data validation
│       └── __init__.py
├── config.py                            # Application configuration
├── database.py                          # Database connection
├── main.py                              # Application entry point
├── ml_server.py                         # ML server entry point
├── requirements.txt                     # Python dependencies
├── serviceAccountKey.json               # Firebase credentials
├── .env                                 # Environment variables
├── docker-compose.yml                   # Docker Compose configuration
└── Dockerfile                           # Docker configuration
```

### **Frontend Structure**
```
academic-advisor-frontend/
├── public/                              # Static assets
├── src/
│   ├── assets/                          # Images, fonts, animations
│   ├── components/                      # Reusable components
│   │   ├── auth/                        # Authentication components
│   │   ├── common/                      # Common UI components
│   │   ├── CVUploader/                  # CV upload components
│   │   ├── dashboard/                   # Dashboard components
│   │   │   ├── cards/                   # Dashboard cards
│   │   │   ├── common/                  # Shared dashboard components
│   │   │   └── sections/                # Dashboard sections
│   │   ├── ErrorBoundary/               # Error handling
│   │   └── messaging/                   # Messaging components
│   ├── contexts/                        # React contexts
│   ├── core/                            # Core utilities
│   │   ├── api/                         # API configuration
│   │   ├── integrations/                # Third-party integrations
│   │   └── hooks/                       # Custom React hooks
│   ├── modules/                         # Feature modules
│   │   ├── agent1/                      # Performance analytics module
│   │   │   ├── performance-analytics/   # Performance analytics
│   │   │   ├── student-analysis/        # Student analysis
│   │   │   └── shared/                  # Shared module components
│   │   └── shared/                      # Shared utilities
│   ├── pages/                           # Page components
│   ├── parsers/                         # File parsers
│   ├── routes/                          # Routing configuration
│   ├── security/                        # Security utilities
│   ├── services/                        # Service layer
│   ├── styles/                          # Global styles
│   ├── types/                           # TypeScript definitions
│   └── utils/                           # Utility functions
├── .env                                 # Environment variables
├── package.json                         # Dependencies and scripts
├── vite.config.ts                       # Vite configuration
└── tailwind.config.js                   # Tailwind CSS configuration
```

## 🔑 Key Features

### **1. Academic Performance Analysis**
- Grade trend visualization
- Subject-wise performance comparison
- CGPA prediction
- Weakness identification using ML
- Performance benchmarking

### **2. Intelligent Recommendations**
- **Course Recommendations**: AI-driven elective suggestions
- **Faculty Matching**: Optimal professor-student pairing
- **Career Path Suggestions**: Based on skills and interests
- **Resource Recommendations**: Learning materials and projects

### **3. Faculty-Student Interaction**
- Appointment scheduling system
- Real-time messaging with WebSockets
- Progress tracking and feedback
- Research collaboration tools

### **4. ML-Powered Insights**
- Performance prediction models
- Weakness analysis algorithms
- Skill gap identification
- Trend analysis and forecasting

### **5. Portfolio Management**
- CV/Resume parsing and analysis
- Project portfolio building
- Achievement tracking
- Publication management

### **6. Analytics Dashboard**
- Real-time performance metrics
- Comparative analysis
- Progress tracking
- Export capabilities (PDF, CSV)

### **7. Administrative Features**
- Student management
- Faculty management
- Course catalog management
- System analytics and reporting

## 📚 API Documentation

### **Base URL**: `http://localhost:8000/api/v1`

### **Key Endpoints:**

#### **Authentication**
```
POST   /auth/login          # User login
POST   /auth/register       # User registration
POST   /auth/refresh        # Token refresh
POST   /auth/logout         # User logout
```

#### **Student Management**
```
GET    /students            # List all students
GET    /students/{id}       # Get student details
PUT    /students/{id}       # Update student
POST   /students/analyze    # Analyze student performance
GET    /students/{id}/weaknesses  # Get weakness analysis
```

#### **Academic Records**
```
GET    /academic/{student_id}      # Get academic records
POST   /academic/upload            # Upload academic data
GET    /academic/{id}/predictions  # Get grade predictions
POST   /academic/recommendations   # Get course recommendations
```

#### **Faculty Matching**
```
GET    /faculty/match              # Match with faculty
GET    /faculty/{id}/availability  # Check availability
POST   /faculty/appointment        # Schedule appointment
```

#### **Messaging**
```
WS     /ws/messages               # WebSocket for messages
GET    /messages/{user_id}        # Get messages
POST   /messages                  # Send message
```

#### **ML Insights**
```
POST   /ml/analyze-performance    # Analyze performance
GET    /ml/predict-grades         # Predict future grades
POST   /ml/recommend-electives    # Get elective recommendations
```

### **Sample API Call**
```javascript
// Get student performance analysis
fetch('http://localhost:8000/api/v1/students/123/analysis', {
  method: 'GET',
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN',
    'Content-Type': 'application/json'
  }
})
.then(response => response.json())
.then(data => console.log(data));
```

## 🚀 Development Guidelines

### **Git Workflow**
```bash
# 1. Create feature branch
git checkout -b feature/feature-name

# 2. Make changes and commit
git add .
git commit -m "feat: add feature description"

# 3. Push to remote
git push origin feature/feature-name

# 4. Create Pull Request on GitHub

# 5. After PR merge, update local main
git checkout main
git pull origin main

### **Commit Message Convention**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code formatting
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance tasks

### **Code Style Guidelines**

#### **Backend (Python)**
- Follow PEP 8 guidelines
- Use type hints for all functions
- Document functions with docstrings
- Maximum line length: 88 characters
- Use async/await for I/O operations

#### **Frontend (TypeScript)**
- Use functional components with hooks
- Follow Airbnb React/JSX Style Guide
- Use TypeScript strict mode
- Component naming: PascalCase
- File naming: kebab-case for files, PascalCase for components


## 🐛 Troubleshooting

### **Common Issues:**

1. **MongoDB Connection Error**
   - Ensure MongoDB is running: `mongod`
   - Check connection string in .env file

2. **Python Package Installation**
   - Use Python 3.11+
   - Upgrade pip: `python -m pip install --upgrade pip`
   - Clear pip cache: `pip cache purge`

3. **Firebase Authentication**
   - Verify serviceAccountKey.json exists
   - Check Firebase project configuration
   - Ensure correct environment variables

4. **Frontend Build Errors**
   - Clear node_modules: `rm -rf node_modules`
   - Clear npm cache: `npm cache clean --force`
   - Reinstall: `npm install`

5. **WebSocket Connection Issues**
   - Check CORS configuration
   - Verify WebSocket server is running
   - Check firewall settings

### **Debug Mode:**
```bash
# Backend with debug
uvicorn main:app --reload --log-level debug

# Frontend with debug
npm run dev -- --debug
```

## 📈 Future Enhancements

### **Planned Features:**
1. **Advanced ML Models**: Deep learning for performance prediction
2. **Mobile Application**: React Native mobile app
3. **Integration with LMS**: Moodle/Canvas integration
4. **AI Chatbot Enhancement**: GPT-4 integration
5. **Peer Comparison**: Anonymous benchmarking
6. **Industry Connect**: Job matching based on skills
7. **Research Paper Recommender**: Academic paper suggestions

### **Scalability Improvements:**
- Microservices architecture
- Kubernetes deployment
- CDN for static assets
- Database sharding
- Load balancing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

### **Development Team Roles:**
- **Frontend Lead**: UI/UX development
- **Backend Lead**: API and database design
- **ML Engineer**: Algorithm development
- **DevOps Engineer**: Deployment and CI/CD
- **QA Engineer**: Testing and validation

## 📄 License

This project is developed for academic purposes as part of the engineering curriculum. All rights reserved by the development team.


---

**Quick Reference Commands:**
```bash
# Start Backend
cd academic-advisor-backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload

# Start Frontend
cd academic-advisor-frontend
npm install
npm run dev

# Clean virtual environment
Remove-Item -Recurse -Force .\venv
```

function Clean-Tree($path, $indent = "") {
    $exclude = @(
        "venv","node_modules","__pycache__",".git",
        "site-packages","pip","dist","build",".cache","logs"
    )

    Get-ChildItem $path | Where-Object {
        $exclude -notcontains $_.Name
    } | ForEach-Object {
        Write-Output "$indent$($_.Name)"
        if ($_.PSIsContainer) {
            Clean-Tree $_.FullName "$indent  "
        }
    }
}

Clean-Tree .
