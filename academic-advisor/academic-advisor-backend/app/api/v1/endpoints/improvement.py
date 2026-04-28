# app/api/v1/endpoints/improvement.py
"""
Improvement & Gamification API Endpoints
=========================================
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from typing import Optional

from app.dependencies import get_current_user, get_admin_user
from app.core.security import FirebaseUser
from app.services.improvement_service import improvement_service

router = APIRouter(prefix="/improvement", tags=["improvement"])


class RoadmapRequest(BaseModel):
    target_type: str  # "elective", "career", "subject", "honours"
    target_name: str


class StepCompleteRequest(BaseModel):
    plan_id: str
    step_number: int


class ResourceTrackRequest(BaseModel):
    resource_id: str
    resource_title: str
    resource_type: str = "article"
    subject: str = ""
    time_spent_minutes: int = 0
    quiz_score: Optional[float] = None


class GameScoreRequest(BaseModel):
    game_id: str
    game_name: str
    subject: str
    score: int
    max_score: int = 100
    level_reached: int = 1
    time_spent_seconds: int = 0


@router.post("/roadmap")
async def generate_roadmap(
    req: RoadmapRequest,
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Generate a personalized improvement roadmap."""
    result = await improvement_service.generate_roadmap(
        student_id=current_user.uid,
        target_type=req.target_type,
        target_name=req.target_name,
    )
    return result


@router.post("/complete-step")
async def complete_step(
    req: StepCompleteRequest,
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Mark a roadmap step as completed."""
    result = await improvement_service.complete_step(
        student_id=current_user.uid,
        plan_id=req.plan_id,
        step_number=req.step_number,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/track-resource")
async def track_resource(
    req: ResourceTrackRequest,
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Track resource completion and earn XP."""
    return await improvement_service.track_resource(
        student_id=current_user.uid,
        resource_id=req.resource_id,
        resource_title=req.resource_title,
        resource_type=req.resource_type,
        subject=req.subject,
        time_spent=req.time_spent_minutes,
        quiz_score=req.quiz_score,
    )


@router.post("/game-score")
async def record_game_score(
    req: GameScoreRequest,
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Record a learning game score and earn XP."""
    return await improvement_service.record_game_score(
        student_id=current_user.uid,
        game_id=req.game_id,
        game_name=req.game_name,
        subject=req.subject,
        score=req.score,
        max_score=req.max_score,
        level_reached=req.level_reached,
        time_spent=req.time_spent_seconds,
    )


@router.get("/progress")
async def get_progress(
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Get gamification progress dashboard."""
    return await improvement_service.get_progress(current_user.uid)


@router.get("/progress/{student_id}")
async def get_student_progress(
    student_id: str,
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Get progress for a specific student (faculty view)."""
    return await improvement_service.get_progress(student_id)


@router.get("/roadmap/{plan_id}")
async def get_roadmap(
    plan_id: str,
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Get a specific roadmap."""
    result = await improvement_service.get_roadmap(plan_id)
    if not result:
        raise HTTPException(status_code=404, detail="Plan not found")
    return result


# ── Quiz Generation (LLM-powered) ────────────────────────────


class QuizRequest(BaseModel):
    subject: str
    topic: str = ""
    difficulty: str = "medium"  # easy, medium, hard
    count: int = 5
    quiz_type: str = "mcq"  # mcq, true_false, fill_blank, code_debug


@router.post("/generate-quiz")
async def generate_quiz(
    req: QuizRequest,
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Generate educational quiz questions using LLM for a specific subject."""
    result = await improvement_service.generate_quiz(
        student_id=current_user.uid,
        subject=req.subject,
        topic=req.topic,
        difficulty=req.difficulty,
        count=req.count,
        quiz_type=req.quiz_type,
    )
    return result


class QuizSubmitRequest(BaseModel):
    subject: str
    quiz_type: str = "mcq"
    total_questions: int
    correct_answers: int
    time_spent_seconds: int = 0
    topic: str = ""


@router.post("/submit-quiz")
async def submit_quiz(
    req: QuizSubmitRequest,
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Submit quiz results, earn XP based on performance."""
    score = int((req.correct_answers / max(req.total_questions, 1)) * 100)
    result = await improvement_service.record_game_score(
        student_id=current_user.uid,
        game_id=f"quiz-{req.quiz_type}-{req.subject.lower().replace(' ', '-')}",
        game_name=f"{req.quiz_type.upper()} Quiz: {req.subject}",
        subject=req.subject,
        score=score,
        max_score=100,
        level_reached=1 if score < 50 else (2 if score < 80 else 3),
        time_spent=req.time_spent_seconds,
    )
    result["correct"] = req.correct_answers
    result["total"] = req.total_questions
    result["percentage"] = score
    return result


@router.get("/weak-subjects")
async def get_weak_subjects(
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Get the student's weak subjects auto-detected from their marks."""
    return await improvement_service.get_weak_subjects(current_user.uid)


class MasteryUpdateRequest(BaseModel):
    subject: str
    lane: str = "theory"  # theory, practical, coding
    score: int
    total_questions: int
    correct_answers: int


@router.post("/update-mastery")
async def update_mastery(
    req: MasteryUpdateRequest,
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Update topic mastery after a game/quiz with adaptive difficulty."""
    return await improvement_service.update_mastery(
        student_id=current_user.uid,
        subject=req.subject,
        lane=req.lane,
        score=req.score,
        total_questions=req.total_questions,
        correct=req.correct_answers,
    )


@router.get("/mastery-summary")
async def get_mastery_summary(
    current_user: FirebaseUser = Depends(get_current_user),
):
    """Get per-subject mastery overview with lane breakdown."""
    return await improvement_service.get_mastery_summary(current_user.uid)
