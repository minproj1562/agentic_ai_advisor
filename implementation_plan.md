# Academic Advisor — Major Enhancement Plan

A comprehensive upgrade to replace synthetic data with real marks, add dynamic elective management, build an improvement roadmap & gamified hub, enable faculty resource sharing, add remedial student management, expand career paths, and enhance the chatbot.

---

## User Review Required

> [!IMPORTANT]
> **This is a very large scope (9 major features).** I recommend executing in **4 phases** to keep each step testable and avoid breaking the existing system. Please confirm the phasing below.

> [!WARNING]
> **Point 1 (Clear DB)** will permanently delete all existing student profiles from MongoDB. Make sure you have any needed backups before we proceed.

> [!IMPORTANT]
> **Point 9 (Chatbot Enhancement)** — The current chatbot uses a rule-based intent classifier + optional LLM (Gemini) fallback. Full "agentic AI" would require significant prompt engineering and possibly RAG upgrades. Please confirm: should I enhance the existing architecture (better prompts, more intents, student-context awareness) or rebuild with a pure LLM agent approach?

---

## Open Questions

1. **Roll Numbers & Names**: You said roll numbers are `5023101`–`5023174`, skipping `5023147` and `5023159` (= 72 students). The `IT - Copy.xlsx` has ~75 students with seat numbers but NO roll numbers. Should I map the students in order of appearance in the Excel (i.e., first student = `5023101`, second = `5023102`, …, skipping the two)?

2. **Admission Year**: The Excel has Sem-III (SH-2024), Sem-IV (FH-2025), Sem-V (SH-2025). This implies admission year **2023**. Should all 72 students use `admission_year = 2023`?

3. **Lab Performance for Training Data**: You said "use practical marks" for lab_performance field. In the Excel, practicals have CIA + ESE columns (out of 25 each, total 50). Should I use the **TOT** (total) column for each practical subject as the lab_performance score?

4. **Elective Dynamic Training** (Point 4): When admin adds a new elective, should the system auto-generate synthetic training data for the new elective class and retrain the ML model automatically? Or should this be a manual trigger (admin clicks "Retrain Model")?

5. **Gamified Hub** (Point 5): What gamification elements do you want?
   - XP points for completing resources/quizzes?
   - Badges/achievements?
   - Streak tracking?
   - Leaderboard (class-level or personal only)?
   - Please confirm which of these to include.

6. **Faculty Resources** (Point 6): Should faculty upload actual files (PDFs, PPTs) to cloud storage, or only paste links/URLs? File upload requires Cloudinary/Firebase Storage integration.

7. **Additional Career Paths** (Point 8): Currently there are 18 careers. Which additional paths do you want? Some suggestions:
   - Game Developer, AR/VR Engineer, Embedded Systems Engineer, Database Administrator, Technical Writer, Quantitative Analyst, Site Reliability Engineer (SRE), Solutions Architect, Data Engineer, Platform Engineer?

---

## Proposed Changes — Phased Execution

---

### Phase 1: Data Foundation (Points 1, 2, 3)
*Clear DB, create student roster XLSX, replace synthetic training data with real marks*

---

#### [NEW] `scripts/clear_student_profiles.py`
- Script to connect to MongoDB and drop all documents from `student_profiles` collection
- Also clears related collections: `student_performance`, `recommendation_records`, `recommendation_feedback`, `training_data_points`
- Prints counts before and after deletion
- Requires user confirmation before executing

#### [NEW] `scripts/generate_student_roster_xlsx.py`
- Reads student names from `IT - Copy.xlsx` (column "Name of Student")
- Assigns roll numbers `5023101`–`5023174` (skipping `5023147`, `5023159`)
- Generates XLSX with columns: `Name`, `Roll Number`, `Branch` (IT), `Admission Year` (2023)
- Output: `exported_marks/IT_Student_Roster.xlsx` — ready for admin portal upload

#### [MODIFY] `scripts/generate_training_data_v2.py`
- Replace the `SUBJECTS_BY_SEMESTER` dictionary with subjects matching the **actual Excel data** (Automata Theory, AI, IoT, Program Elective-I, Cloud Computing Lab, Mobile App Dev Lab, IoT Lab, etc.)
- Replace the synthetic mark generation with a function that reads real marks from `IT - Copy.xlsx`
- For **lab_performance** field: use practical subject TOT marks (Cloud Computing Lab, Mobile App Dev Lab, IoT Lab averages)
- Remove `attendance` field from performance training data (as per your instruction "don't keep it for now")
- Generate performance/weakness training data based on real student scores

#### [MODIFY] `scripts/train_all_models.py`
- Update to use the new real-data-based training data
- Ensure models retrain cleanly with the updated data format

---

### Phase 2: Dynamic Elective System (Point 4)

---

#### [MODIFY] `app/api/v1/admin.py`
- Enhance `POST /admin/curriculum/electives` to trigger training data generation when a new elective is added
- Add endpoint `POST /admin/curriculum/electives/retrain` — generates training data for all current electives and retrains the recommendation engine
- The training data generation happens in the background using the existing elective affinity patterns but extended dynamically

#### [NEW] `app/services/dynamic_training_service.py`
- Service that auto-generates training data for newly added electives
- Uses the elective's `topics`, `skills_covered`, `career_paths` metadata to create affinity maps
- Generates N synthetic training samples per new elective class
- Triggers model retraining via `app/ml/utils/training.py`

#### [MODIFY] `app/ml/models/recommendation_engine.py`
- Add method `add_elective_class(code, name, affinity_map)` to dynamically extend `PEC_LABELS` / `OEC_LABELS`
- Add method `retrain_with_new_data(training_data)` that retrains without needing server restart
- Update `recommend_electives()` and `recommend_open_electives()` to dynamically read from DB instead of hardcoded lists

#### [MODIFY] `app/services/recommendation_service.py`
- Update `get_model_info()` to return dynamically loaded elective lists instead of hardcoded values
- Invalidate all cached recommendations when retraining happens

#### [MODIFY] Frontend: `CurriculumManagement.tsx`
- Add "Retrain Model" button in the elective management section
- Show training status indicator (trained/training/needs retraining)
- Display the current elective labels the model knows about

---

### Phase 3: Improvement Roadmap, Gamified Hub, Resources, Remedial (Points 5, 6, 7)

---

#### Point 5: Improvement Roadmap & Gamified Hub

##### [NEW] `app/models/improvement.py`
- `ImprovementPlan` — Document: student_id, target (elective/career/honour), weak_subjects, roadmap_steps[], status, created_at
- `RoadmapStep` — Embedded: title, description, resources[], is_completed, xp_reward, completion_date
- `StudentProgress` — Document: student_id, total_xp, level, badges[], streaks, resource_completions[], quiz_scores[], project_submissions[]
- `Badge` — Embedded: name, description, icon, earned_at, category
- `ResourceCompletion` — Embedded: resource_id, completed_at, time_spent_minutes, quiz_score

##### [NEW] `app/services/improvement_service.py`
- `generate_roadmap(student_id, target_elective/career)` — analyzes student's weak subjects related to the target, generates a step-by-step improvement plan with resources
- `track_resource_completion(student_id, resource_id, quiz_score)` — records progress, awards XP
- `get_progress_dashboard(student_id)` — returns XP, level, badges, completion stats
- `check_badge_eligibility(student_id)` — checks and awards badges based on milestones

##### [NEW] `app/api/v1/endpoints/improvement.py`
- `POST /improvement/roadmap` — generate roadmap for a target
- `GET /improvement/progress/{student_id}` — get progress dashboard
- `POST /improvement/track-resource` — mark resource as completed
- `GET /improvement/roadmap/{plan_id}` — get a specific roadmap
- `GET /improvement/faculty-view/{student_id}` — faculty view of student progress

##### [NEW] Frontend: `ImprovementHub.tsx`
- Main gamified hub component with:
  - XP bar and level indicator
  - Active roadmaps with progress bars
  - Resource cards (video, article, quiz) with completion tracking
  - Badge showcase
  - Streak counter
  - "Choose Your Path" — pick an elective/career/honour to get a roadmap
- Accessible from Student Dashboard sidebar

##### [MODIFY] Frontend: `StudentDashboard.tsx`
- Add "Improvement Hub" section to sidebar navigation
- Add progress summary card to dashboard overview

##### [MODIFY] Frontend: `FacultyDashboard.tsx` / `FacultyOverview.tsx`
- Add student progress tracking widget showing which students are on improvement plans and their progress

---

#### Point 6: Faculty Resource Upload

##### [NEW] `app/models/faculty_resource.py`
- `FacultyResource` — Document: faculty_id, title, description, resource_type (link/video/ppt/pdf/book), url, file_url, semester, branch, subject, tags[], created_at

##### [NEW] `app/api/v1/endpoints/faculty_resources.py`
- `POST /faculty/resources` — create a resource (links/URLs)
- `POST /faculty/resources/upload` — upload file (PDF/PPT) to Firebase Storage
- `GET /faculty/resources` — list resources (filterable by semester, branch, subject)
- `DELETE /faculty/resources/{id}` — delete a resource
- `GET /students/resources` — student endpoint to fetch resources for their semester/branch

##### [NEW] Frontend: `FacultyResourceUpload.tsx`
- Form for faculty to add resources: title, type, URL/file upload, semester picker, branch picker, subject picker
- List view of uploaded resources with edit/delete

##### [MODIFY] Frontend: Student `Resources.tsx`
- Add "Faculty Resources" tab showing resources uploaded by faculty for the student's semester/branch
- Display with nice cards showing resource type icons, faculty name, date

---

#### Point 7: Remedial Student Management

##### [NEW] `app/models/remedial.py`
- `RemedialEntry` — Document: faculty_id, student_id, semester, branch, subject, reason, notes, status (active/resolved), progress_notes[], created_at, resolved_at

##### [NEW] `app/api/v1/endpoints/remedial.py`
- `POST /faculty/remedial` — add a student as remedial for a subject
- `GET /faculty/remedial` — list all remedial students for a faculty member (filterable)
- `PUT /faculty/remedial/{id}/progress` — add progress note
- `PUT /faculty/remedial/{id}/resolve` — mark as resolved
- `GET /faculty/remedial/student/{student_id}` — get remedial entries for a student

##### [NEW] Frontend: `RemedialManagement.tsx`
- Faculty view to add remedial students (select semester, branch, subject, then pick students)
- List view with progress tracking
- Progress note addition modal
- Status badges (Active, Improving, Resolved)

##### [MODIFY] Frontend: `FacultyDashboard.tsx`
- Add "Remedial Students" section to sidebar

##### [MODIFY] Frontend: `StudentDashboard.tsx`
- If student has remedial entries, show notification/banner with improvement resources

---

### Phase 4: Career Paths & Chatbot Enhancement (Points 8, 9)

---

#### Point 8: More Career Paths

##### [MODIFY] `scripts/seed_career_data.py`
- Add 8-10 new career paths:
  - **Game Developer** (SOFTWARE_DEVELOPMENT)
  - **AR/VR Engineer** (SOFTWARE_DEVELOPMENT)
  - **Embedded Systems Engineer** (NETWORKING_AND_IOT)
  - **Database Administrator** (DATA_AND_AI)
  - **Technical Writer** (MANAGEMENT)
  - **Data Engineer** (DATA_AND_AI)
  - **Site Reliability Engineer** (CLOUD_AND_DEVOPS)
  - **Solutions Architect** (CLOUD_AND_DEVOPS)
  - **Quantitative Analyst / FinTech** (DATA_AND_AI)
  - **AI Ethics & Governance Specialist** (RESEARCH)
- Each with complete: description, required_skills, recommended_subjects, salary_range, roadmap, certifications, etc.

---

#### Point 9: Chatbot Enhancement

##### [MODIFY] `app/services/chatbot/intent_classifier.py`
- Add new intents: `IMPROVEMENT_QUERY`, `RESOURCE_QUERY`, `REMEDIAL_QUERY`, `ELECTIVE_COMPARISON`, `SKILL_GAP_ANALYSIS`
- Improve pattern matching for existing intents with more keywords
- Add student-context-aware classification (if student has weak subjects, bias towards improvement suggestions)

##### [MODIFY] `app/services/chatbot/response_generator.py`
- Add handlers for new intents
- Improve existing handlers to use more student data (semester records, weak subjects, interests)
- Add "proactive suggestions" — when student asks about a career, also mention if they have weak prerequisites
- Better formatted responses with actionable next steps

##### [MODIFY] `app/services/chatbot/chatbot_service.py`
- Improve student data enrichment to include improvement plans, remedial status, faculty resources
- Add "conversation memory" improvements — remember what the student was discussing
- Add automatic linking to improvement hub when weak subjects are detected

##### [MODIFY] `app/services/chatbot/llm_service.py`
- Update system prompts to be more knowledgeable about the FCRIT IT curriculum
- Add RAG context about the student's specific situation (marks, weak subjects, improvement plans)
- Improve the Gemini prompt templates for career guidance, elective recommendations, and concept explanations

##### [MODIFY] `app/services/chatbot/student_data_service.py`
- Fetch improvement plans, remedial status, resource completions
- Provide richer student context to the chatbot for personalized responses

---

## Verification Plan

### Automated Tests

1. **Phase 1**: 
   - Run `clear_student_profiles.py` and verify MongoDB is empty
   - Run `generate_student_roster_xlsx.py` and verify output XLSX has 72 students with correct roll numbers
   - Upload the roster through admin portal and verify student profiles are created
   - Run training data generation and verify output CSVs have real marks data
   - Retrain models and verify accuracy metrics

2. **Phase 2**:
   - Create a new elective via admin API and verify training data is generated
   - Trigger retrain and verify model includes the new elective
   - Get recommendations and verify new elective appears in results

3. **Phase 3**:
   - Test improvement roadmap generation for a student with weak subjects
   - Test resource completion tracking and XP awards
   - Test faculty resource upload and student fetch
   - Test remedial student CRUD operations

4. **Phase 4**:
   - Verify new career paths are seeded correctly
   - Test chatbot with queries about improvement, resources, remedial
   - Test chatbot context awareness with student data

### Manual Verification
- Upload marks via admin portal and verify student dashboard shows correct data
- Navigate gamified hub as a student and verify XP/badges/progress
- Upload resources as faculty and verify student can see them
- Test chatbot conversation flow end-to-end
