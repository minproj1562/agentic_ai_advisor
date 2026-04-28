# Academic Advisor — Enhancement Task Tracker

## Phase 1: Data Foundation (Points 1, 2, 3) ✅ COMPLETE

- [x] Create `scripts/clear_student_profiles.py` — wipe all student data from MongoDB
- [x] Create `scripts/generate_student_roster_xlsx.py` — extract names from IT_COPY.xlsx, assign roll numbers 5023101-5023174 (skip 5023147, 5023159)
- [x] Modify training data generation to use real marks from IT_COPY.xlsx
- [x] Update `lab_performance` to use practical marks TOT column
- [x] Remove attendance from training data
- [x] Retrain models with real data

## Phase 2: Dynamic Elective System (Point 4) ✅ COMPLETE

- [x] Create `app/services/dynamic_training_service.py`
- [x] Modify admin elective endpoints to auto-trigger training data gen + retrain
- [x] Modify recommendation engine for dynamic elective support
- [x] Update CurriculumManagement.tsx with retrain status

## Phase 3: Improvement Hub, Resources, Remedial (Points 5, 6, 7) ✅ COMPLETE

- [x] Create improvement/gamification models
- [x] Create improvement service with interactive game hub
- [x] Create improvement API endpoints
- [x] Build ImprovementHub.tsx with animated interactive games
- [x] Create faculty resource models & API (Cloudinary + links)
- [x] Build FacultyResourceUpload.tsx
- [x] Update student Resources.tsx with faculty resources tab
- [x] Create remedial student models & API
- [x] Build RemedialManagement.tsx for faculty
- [x] Update Faculty/Student dashboards (ImprovementHub integrated in Student Dashboard)

## Phase 4: Career Paths & Chatbot (Points 8, 9) ✅ COMPLETE

- [x] Add 10+ new career paths to seed_career_data.py (18→28 careers)
- [x] Add new chatbot intents (game dev, AR/VR, SRE, quant, AI ethics, etc.)
- [x] Enhance intent classifier with 20+ new career name keywords
- [x] Add shortform expansions for new careers (sre, dba, de, xr, quant, etc.)
- [x] Register Phase 3 models in `__init__.py` exports
