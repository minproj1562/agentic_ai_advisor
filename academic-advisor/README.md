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
academic-advisor
  .venv
    bin
      activate
      activate.csh
      activate.fish
      Activate.ps1
      pip3
      pip3.12
      python
      python3
      python3.12
    Include
    Lib
      python3.12
    Scripts
      activate
      activate.bat
      activate.fish
      Activate.ps1
      deactivate.bat
      pip.exe
      pip3.13.exe
      pip3.exe
      python.exe
      pythonw.exe
      uvicorn.exe
    .gitignore
    lib64
    pip.pyz
    pyvenv.cfg
  academic-advisor-backend
    app
      api
        middleware
          auth.py
          cors.py
          logging.py
          rate_limit.py
          __init__.py
        v1
          endpoints
            academic.py
            achievements.py
            analytics.py
            appointments.py
            electives.py
            faculty_profile.py
            meeting_requests.py
            messages.py
            ml_insights.py
            notifications.py
            publications.py
            research_area.py
            resources.py
            students.py
            student_analysis.py
            student_profile.py
            student_projects_enhanced.py
            weakness.py
            __init__.py
          api.py
          auth.py
          cv.py
          faculty.py
          messages.py
          recommendations.py
          resources.py
          students.py
          student_analysis.py
          websocket.py
          __init__.py
        __init__.py
      core
        cache.py
        config.py
        constants.py
        curriculum.py
        database.py
        deps.py
        error_tracking.py
        exceptions.py
        firebase.py
        firebase_admin.py
        firebase_sync.py
        logging.py
        metrics.py
        monitoring.py
        performance.py
        security.py
        websocket_manager.py
        __init__.py
      database
        base.py
        connection.py
        __init__.py
      ml
        models
          saved
            README.md
          performance_predictor.py
          recommendation_engine.py
          weakness_detector.py
          __init__.py
        preprocessors
          data_preprocessor.py
          feature_engineering.py
          __init__.py
        utils
          metrics.py
          model_utils.py
          training.py
          __init__.py
        elective_recommender.py
        ml_service.py
        weakness_predictor.py
        __init__.py
      models
        academic_record.py
        achievement.py
        analytics.py
        appointment.py
        cv.py
        elective.py
        faculty.py
        meeting_request.py
        mentorship.py
        messages.py
        performance.py
        publications.py
        recommendation.py
        research_area.py
        resource.py
        student.py
        student_analysis.py
        student_performance.py
        student_profile.py
        student_projects.py
        weakness.py
        __init__.py
      routers
        academic.py
      schemas
        achievement.py
        analytics_schemas.py
        faculty_schemas.py
        performance_schemas.py
        recommendation_schemas.py
        student_schemas.py
        __init__.py
      scripts
        create_sample_data.py
        set_faculty_role.py
      services
        academic_service.py
        achievement_service.py
        analytics_service.py
        appointment_service.py
        cloudinary_service.py
        cv_analysis_service.py
        cv_parser_v2.py
        elective_recommendation_service.py
        enhanced_ml_inference.py
        faculty_service.py
        messaging_service.py
        ml_performance_analysis.py
        ml_service.py
        nlp_service.py
        notification_service.py
        publication_service.py
        recommendation_engine.py
        recommendation_service.py
        research_service.py
        resource_matcher.py
        resource_service.py
        skill_extractor.py
        student_analysis_service.py
        student_projects_service.py
        student_service.py
        weakness_analysis_service.py
        websocket_manager.py
        __init__.py
      tasks
        semester_updater.py
      utils
        data_validator.py
        decorators.py
        formatters.py
        helpers.py
        metrics.py
        pagination.py
        validators.py
        __init__.py
      v1
        endpoints
          achievements.py
          analytics.py
      config.py
      database.py
      dependencies.py
      main.py
      __init__.py
    scripts
      backup.py
      init_db.py
      migrate_data.py
      seed_faculty_data.py
      train_models.py
    tests
      conftest.py
      test_analytics.py
      test_auth.py
      test_ml_models.py
      test_services.py
      test_students.py
      test_student_analysis.py
      __init__.py
    .env
    .gitignore
    docker-compose.yml
    Dockerfile
    firebase.py
    main.py
    ml_server.py
    requirements.txt
    serviceAccountKey.json
    serviceAccountKey.template.json
  academic-advisor-frontend
    src
      assets
        confetti.json
        react.svg
      components
        auth
          LoginForm.tsx
          ProtectedRoute.tsx
        common
          LoadingSpinner
            index.tsx
          CTALink.tsx
          LoadingSpinner.tsx
          Modal.tsx
          StatCard.tsx
        CVUploader
          index.tsx
          UploadZone.tsx
        dashboard
          cards
            CVAnalyserCard.tsx
            ExpertiseSummaryCard.tsx
            MenteeOverviewCard.tsx
            MentorshipSlotsCard.tsx
            NotificationsCard.tsx
            PerformanceSnapshot.tsx
            QuickActionsCard.tsx
            StudentAnalysisTable.tsx
            StudentDetailModal.tsx
            WeaknessIndicator.tsx
          common
            ErrorBoundary.tsx
            LoadingSkeleton.tsx
          sections
            Achievements.tsx
            Analytics.tsx
            CVAnalysisSection.tsx
            DashboardOverview.tsx
            FacultyOverview.tsx
            FacultyProfileView.tsx
            Messages.tsx
            NotificationsSection.tsx
            Performance.tsx
            ProjectAnalysisResults.tsx
            Publications.tsx
            ResearchAreas.tsx
            Settings.tsx
            StudentAnalysisSection.tsx
            StudentProjectsList.tsx
            StudentProjectsUpload.tsx
          AcademicDataEntry.tsx
          AcademicInsights.tsx
          AIInsightsDashboard.tsx
          CVAnalyser.tsx
          EngineeringGuidance.tsx
          FacultyHeader.tsx
          FacultyMatcher.tsx
          FacultySidebar.tsx
          InterestManagement.tsx
          MLDashboardWidget.tsx
          MLInsights.tsx
          PerformanceChart.tsx
        ErrorBoundary
          index.tsx
        meetings
          FacultyMeetingManagement.tsx
          index.ts
          MeetingsCalendar.tsx
          StudentMeetingRequest.tsx
        messaging
          MessageCenter.tsx
        AuthLayout.tsx
        ErrorBoundary.tsx
        FacultyGuard.tsx
        ProtectedRoute.tsx
      config
        environment.ts
      contexts
        AuthContext.tsx
        ThemeContext.tsx
      core
        api
          interceptors
            auth.interceptor.ts
            error.interceptor.ts
        integrations
          firebase
            config.ts
            realtime.ts
            storage.ts
          youtube
            youtube.service.ts
      hooks
        useAnalytics.ts
        useAuth.ts
        useCVParser.ts
        useDashboardData.ts
        useDebounce.ts
        useEngineeringGuidance.ts
        useErrorHandler.ts
        useMessaging.ts
        useMLInsights.ts
        useTheme.ts
        useWebSocket.ts
      modules
        agent1
          performance-analytics
            components
              SubjectPerformance
                index.tsx
                SubjectRadar.tsx
              TrendAnalyzer
                index.tsx
                TrendChart.tsx
            constants
              thresholds.ts
            hooks
              usePerformanceTrends.ts
              usePredictiveMetrics.ts
              useWeaknessAnalysis.ts
            services
              analytics.service.ts
              prediction.service.ts
              trend.service.ts
            types
              analytics.types.ts
            utils
              calculations.ts
              formatters.ts
              validators.ts
          shared
            components
              ActionButton.tsx
              InsightPanel.tsx
              RecommendationCard.tsx
            hooks
              useAgent1Data.ts
              useRecommendations.ts
            utils
              agent1.helpers.ts
              data.transformers.ts
          student-analysis
            components
              PerformanceTrends
                index.tsx
                TrendPredictor.tsx
              StudentAnalysisTable
                index.tsx
                types.ts
              WeaknessIndicator
                index.tsx
                WeaknessChart.tsx
            hooks
              useMLPredictions.ts
              useRealTimeUpdates.ts
              useStudentAnalysis.ts
            services
              ml-integration.service.ts
              realtime-sync.service.ts
              student-analysis.service.ts
            types
              student-analysis.types.ts
        shared
          services
            api.service.ts
      monitoring
        error.tracker.ts
        performance.monitor.ts
      pages
        Dashboard
          FacultyDashboard.tsx
          index.tsx
          StudentDashboard.tsx
        About.tsx
        Academics.tsx
        Admissions.tsx
        Alumni.tsx
        CampusLife.tsx
        CampusTour.tsx
        CareerServices.tsx
        Demo.tsx
        Departments.tsx
        DigitalLibrary.tsx
        FacultyPortal.tsx
        FacultyProfileSetup.tsx
        Features.tsx
        Help.tsx
        HomePage.tsx
        Login.tsx
        NotFound.tsx
        ProgramDetail.tsx
        ProgramsList.tsx
        Register.tsx
        Research.tsx
        Resources.tsx
        StudentPortal.tsx
      parsers
        pdf.parser.ts
        skill.extractor.ts
        text.parser.ts
      routes
        AppRouter.tsx
        ProtectedRoute.tsx
      security
        encryption.ts
        sanitization.ts
      services
        analytics.service.ts
        api.service.ts
        auth.service.ts
        cloudinary.service.ts
        engineering.service.ts
        extraction.service.ts
        firebase.config.ts
        github.service.ts
        ml.service.ts
        nlp.service.ts
        parser.service.ts
        student_analysis.service.ts
        student_projects_cloudinary.service.ts
        student_projects_no_storage.service.ts
        weakness.service.ts
      styles
        global.css
      types
        analytics.types.ts
        auth.types.ts
        cv.types.ts
        dashboard.types.ts
      utils
        cn.ts
        formatters.ts
        mockData.ts
        theme.utils.ts
        validation.ts
      App.css
      App.test.js
      App.tsx
      index.css
      index.tsx
      logo.svg
      main.tsx
      reportWebVitals.js
      reportWebVitals.tsx
      setupTests.js
      vite-env.d.ts
    .env
    .firebaserc
    .gitignore
    craco.config.js
    eslint.config.js
    firebase.json
    firestore.indexes.json
    firestore.rules
    index.html
    package-lock.json
    package.json
    postcss.config.js
    README.md
    tailwind.config.js
    tsconfig.app.json
    tsconfig.json
    tsconfig.node.json
    vite.config.ts
  .gitattributes
  .gitignore
  academic-advisor-clean-tree.txt
  package-lock.json
  package.json
  README.md
.gitignore
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

# For .gitignore merge conflict problem:
git checkout --ours ../.gitignore
git add ../.gitignore
git status
git commit

# show the true repo
git rev-parse --show-toplevel

# For merging your code to main
git checkout main
git merge Sharon

# For pulling the changes from main
git pull origin main

# for automatically updating the requirements.txt file
pip freeze > requirements.txt

# To check the loading routes
python -c "from app.api.v1.api import api_router; print('Registered routes:'); [print('  {} {}'.format(r.methods if hasattr(r, 'methods') else '', r.path)) for r in api_router.routes if hasattr(r, 'path')]"

# For syncing mongodb with firebase
# Step 1: Preview what will happen (no changes)
cd academic-advisor-backend
python scripts/sync_faculty_to_firebase.py --dry-run

# Step 2: Actually sync
python scripts/sync_faculty_to_firebase.py

# Step 3: Sync a specific faculty only
python scripts/sync_faculty_to_firebase.py --email "rajesh.kumar@fcrit.ac.in"

# Step 4: Custom password
python scripts/sync_faculty_to_firebase.py --default-password "MyCustomPass@123"