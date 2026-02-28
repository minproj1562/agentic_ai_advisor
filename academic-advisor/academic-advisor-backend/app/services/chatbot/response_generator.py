# academic-advisor-backend/app/services/chatbot/response_generator.py
"""
Response generator — Groq / Llama-3 powered
Owns: CAREER_QUERY, PERFORMANCE_QUERY, ELECTIVE_QUERY, STUDY_PLAN_QUERY
Delegates: SYLLABUS_QUERY, FACULTY_QUERY → Person A
"""

import re
import json
import logging
from typing import Dict, Any, Optional, List

from app.core.config import settings
from app.models.chatbot import IntentType, ResponseType
from app.repositories.career_repository import CareerRepository

logger = logging.getLogger(__name__)

# Common career name aliases for better matching
_CAREER_ALIASES: Dict[str, str] = {
    "data scientist": "Data Scientist",
    "data science": "Data Scientist",
    "ml engineer": "ML Engineer",
    "machine learning engineer": "ML Engineer",
    "software developer": "Software Developer",
    "software engineer": "Software Developer",
    "sde": "Software Developer",
    "web developer": "Full Stack Developer",
    "full stack": "Full Stack Developer",
    "frontend": "Full Stack Developer",
    "backend": "Software Developer",
    "devops": "DevOps Engineer",
    "cloud": "Cloud Architect",
    "cloud engineer": "Cloud Architect",
    "cybersecurity": "Cybersecurity Analyst",
    "security": "Cybersecurity Analyst",
    "ethical hacking": "Cybersecurity Analyst",
    "hacker": "Cybersecurity Analyst",
    "mobile": "Mobile App Developer",
    "android": "Mobile App Developer",
    "ios": "Mobile App Developer",
    "flutter": "Mobile App Developer",
    "blockchain": "Blockchain Developer",
    "web3": "Blockchain Developer",
    "iot": "IoT Developer",
    "embedded": "IoT Developer",
    "product manager": "Product Manager (Tech)",
    "pm": "Product Manager (Tech)",
    "ai research": "AI Research Engineer",
    "research": "AI Research Engineer",
    "network": "Network Engineer",
    "networking": "Network Engineer",
    "ui ux": "UI/UX Designer",
    "ux": "UI/UX Designer",
    "designer": "UI/UX Designer",
    "qa": "QA / Test Automation Engineer",
    "testing": "QA / Test Automation Engineer",
    "tester": "QA / Test Automation Engineer",
    "nlp": "NLP Engineer",
    "natural language": "NLP Engineer",
    "chatbot": "NLP Engineer",
    "llm": "NLP Engineer",
    "business analyst": "Business Analyst",
    "ba": "Business Analyst",
    "data analyst": "Data Analyst",
    "analytics": "Data Analyst",
}


def _extract_career_name(query: str) -> Optional[str]:
    """Try to extract a career name from a natural language query."""
    ql = query.lower().strip()

    # Direct alias match (longest first for better matching)
    sorted_aliases = sorted(_CAREER_ALIASES.keys(), key=len, reverse=True)
    for alias in sorted_aliases:
        if alias in ql:
            return _CAREER_ALIASES[alias]

    return None


class ResponseGenerator:

    def __init__(self):
        self.career_repo = CareerRepository()
        self._client = None

    @property
    def llm(self):
        if self._client is None and settings.GROQ_API_KEY:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(
                    api_key=settings.GROQ_API_KEY,
                    base_url="https://api.groq.com/openai/v1",
                )
                logger.info("✅ Groq LLM client initialized")
            except Exception as e:
                logger.warning(f"Groq client init failed: {e}")
                self._client = None
        return self._client

    # ── Public entry point ───────────────────────────────

    async def generate_response(
        self,
        query: str,
        intent: IntentType,
        context: Dict[str, Any],
        student_data: Optional[Dict] = None,
    ) -> Dict[str, Any] | str:
        if intent == IntentType.OUT_OF_SCOPE:
            return "Beyond my scope"

        handlers = {
            IntentType.CAREER_QUERY: self._career,
            IntentType.PERFORMANCE_QUERY: self._performance,
            IntentType.ELECTIVE_QUERY: self._elective,
            IntentType.STUDY_PLAN_QUERY: self._study_plan,
            IntentType.CLARIFICATION: self._clarification,
        }
        handler = handlers.get(intent, self._generic)
        try:
            return await handler(query, context, student_data)
        except Exception as e:
            logger.error(f"ResponseGenerator error: {e}", exc_info=True)
            return self._error()

    # ════════════════  CAREER  ════════════════════════════

    async def _career(
        self, query: str, ctx: Dict, stu: Optional[Dict]
    ) -> Dict[str, Any]:

        # Step 1: Try alias-based exact match first
        career_name = _extract_career_name(query)
        target = None

        if career_name:
            target = await self.career_repo.find_by_title(career_name)

        # Step 2: Try keyword search
        if not target:
            careers = await self.career_repo.search(query, limit=5)
            if careers:
                # Check for close title match
                ql = query.lower()
                for c in careers:
                    if c.title.lower() in ql or any(
                        kw in ql for kw in [k.lower() for k in c.keywords[:5]]
                    ):
                        target = c
                        break
                if not target:
                    target = careers[0]  # Best scored result

        # Step 3: Try interests-based search
        if not target and stu:
            interests = stu.get("interests", [])
            if interests:
                careers = await self.career_repo.find_by_interests(interests, 5)
                if careers:
                    target = careers[0]

        # Step 4: If still nothing, return career list
        if not target:
            all_c = await self.career_repo.get_all()
            if all_c:
                return {
                    "type": ResponseType.CAREER_LIST.value,
                    "intent": IntentType.CAREER_QUERY.value,
                    "content": {
                        "message": "Here are career paths I can help you explore:",
                        "careers": [
                            {
                                "title": c.title,
                                "category": c.category.value,
                                "demand": c.market_demand.value,
                                "description": c.description[:150],
                            }
                            for c in all_c[:10]
                        ],
                        "hint": "Ask about a specific career for a detailed roadmap. E.g., 'Tell me about data science career'",
                    },
                    "confidence": "Medium",
                }
            return self._no_data(IntentType.CAREER_QUERY)

        # ── We have a target career — build detailed response ──

        # Get LLM personalized advice
        llm_advice = await self._llm_career(query, target, stu)

        career_obj = {
            "title": target.title,
            "category": target.category.value,
            "description": target.description,
            "required_skills": target.required_skills,
            "recommended_subjects": target.recommended_subjects,
            "recommended_electives": target.recommended_electives,
            "job_titles": target.job_titles,
            "salary_range": {
                "entry_level": target.salary_range.entry_level,
                "mid_level": target.salary_range.mid_level,
                "senior_level": target.salary_range.senior_level,
                "top_companies": target.salary_range.top_companies,
            },
            "top_companies_india": target.top_companies_india,
            "top_companies_global": target.top_companies_global,
            "certifications": target.certifications,
            "market_demand": target.market_demand.value,
            "growth_potential": target.growth_potential,
        }

        roadmap = [
            {
                "step": s.step,
                "title": s.title,
                "description": s.description,
                "duration": s.duration,
            }
            for s in target.roadmap
        ]

        next_steps = []
        if target.recommended_subjects:
            next_steps.append(
                f"Focus on: {', '.join(target.recommended_subjects[:3])}"
            )
        if target.recommended_electives:
            next_steps.append(
                f"Electives: {', '.join(target.recommended_electives[:3])}"
            )
        if target.certifications:
            next_steps.append(f"Certify: {target.certifications[0]}")

        body: Dict[str, Any] = {
            "career": career_obj,
            "roadmap": roadmap,
            "next_steps": next_steps,
        }

        if llm_advice:
            body["personalized_advice"] = llm_advice

        if stu:
            gap = self._gap(target, stu)
            if gap:
                body["gap_analysis"] = gap

        return {
            "type": ResponseType.CAREER_GUIDANCE.value,
            "intent": IntentType.CAREER_QUERY.value,
            "content": body,
            "confidence": "High",
        }

    def _gap(self, career, stu: Dict) -> Optional[Dict]:
        req = [s.lower() for s in career.required_skills]
        have = [s.lower() for s in stu.get("skills", [])]
        match = [s for s in req if s in have]
        miss = [s for s in req if s not in have]
        if not req:
            return None
        return {
            "matching_skills": match,
            "missing_skills": miss,
            "skill_match_pct": round(len(match) / max(len(req), 1) * 100),
            "cgpa_meets": (stu.get("cgpa", 0) >= career.min_cgpa_recommended),
            "recommended_cgpa": career.min_cgpa_recommended,
            "your_cgpa": stu.get("cgpa", 0),
        }

    async def _llm_career(self, query, career, stu) -> Optional[str]:
        if not self.llm:
            return None
        try:
            stu_str = ""
            if stu:
                stu_str = (
                    f"\nStudent context — CGPA: {stu.get('cgpa', 'N/A')}, "
                    f"Semester: {stu.get('semester', 'N/A')}, "
                    f"Interests: {', '.join(stu.get('interests', []))}, "
                    f"Strong subjects: {', '.join(stu.get('strong_subjects', [])[:3])}, "
                    f"Weak subjects: {', '.join(stu.get('weak_subjects', [])[:3])}"
                )

            resp = await self.llm.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a career counselor at FCRIT Mumbai (IT department). "
                            "Give 3-4 brief, actionable, personalized sentences. "
                            "Focus on Indian job market. Be encouraging but realistic. "
                            "Don't repeat info already shown — add NEW insights."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Student asked: '{query}'\n"
                            f"Career: {career.title}\n"
                            f"Key skills needed: {', '.join(career.required_skills[:6])}\n"
                            f"Market demand: {career.market_demand.value}\n"
                            f"Entry salary: {career.salary_range.entry_level}"
                            f"{stu_str}\n\n"
                            f"Give personalized advice for this student."
                        ),
                    },
                ],
                temperature=0.3,
                max_tokens=300,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"LLM career advice failed: {e}")
            return None

    # ════════════════  PERFORMANCE  ═══════════════════════

    async def _performance(
        self, query: str, ctx: Dict, stu: Optional[Dict]
    ) -> Dict[str, Any]:
        if not stu:
            return {
                "type": ResponseType.TEXT.value,
                "intent": IntentType.PERFORMANCE_QUERY.value,
                "content": {
                    "message": (
                        "To provide your performance analysis, I need your academic data.\n\n"
                        "Please ensure you have:\n"
                        "1. Completed your academic profile\n"
                        "2. Entered semester-wise grades\n"
                        "3. Updated current semester info\n\n"
                        "Once done, ask me again and I'll show your detailed analysis!"
                    ),
                    "actions": [
                        "Go to Academic Data Entry",
                        "Add your grades",
                        "Come back and ask again",
                    ],
                },
                "confidence": "High",
            }

        a = self._analyse(stu)
        llm_ins = await self._llm_perf(stu, a)

        body: Dict[str, Any] = {
            "profile": {
                "name": stu.get("name", "Student"),
                "branch": stu.get("branch", "IT"),
                "semester": stu.get("semester", "N/A"),
                "cgpa": stu.get("cgpa", 0),
            },
            "current_cgpa": stu.get("cgpa", 0),
            "latest_sgpa": stu.get("latest_sgpa", 0),
            "sgpa_trend": stu.get("sgpa_trend", []),
            "trend_direction": a["trend"],
            "subject_analysis": a["breakdown"],
            "weak_subjects": a["weak"],
            "strong_subjects": a["strong"],
            "insights": a["insights"],
            "recommendations": a["suggestions"],
        }
        if llm_ins:
            body["ai_insights"] = llm_ins

        return {
            "type": ResponseType.PERFORMANCE_ANALYSIS.value,
            "intent": IntentType.PERFORMANCE_QUERY.value,
            "content": body,
            "confidence": "High",
        }

    def _analyse(self, d: Dict) -> Dict:
        subjects = d.get("subjects", [])
        weak, strong, bd = [], [], []
        for s in subjects:
            nm = s.get("name", s.get("subject_name", "?"))
            sc = s.get("score", s.get("marks", 0))
            st = "weak" if sc < 50 else ("strong" if sc >= 75 else "average")
            bd.append({"subject": nm, "score": sc, "status": st})
            if st == "weak":
                weak.append(nm)
            elif st == "strong":
                strong.append(nm)

        trend_list = d.get("sgpa_trend", [])
        trend = "stable"
        if len(trend_list) >= 2:
            cur = (
                trend_list[-1].get("sgpa", 0)
                if isinstance(trend_list[-1], dict)
                else trend_list[-1]
            )
            prev = (
                trend_list[-2].get("sgpa", 0)
                if isinstance(trend_list[-2], dict)
                else trend_list[-2]
            )
            trend = (
                "improving"
                if cur > prev + 0.3
                else ("declining" if cur < prev - 0.3 else "stable")
            )

        insights = []
        if trend == "improving":
            insights.append("📈 Your grades are improving — great work!")
        elif trend == "declining":
            insights.append(
                "⚠️ Performance is declining — consider seeking help."
            )
        if len(weak) > 2:
            insights.append(f"📚 Focus needed on: {', '.join(weak[:3])}")
        if strong:
            insights.append(f"💪 Strong in: {', '.join(strong[:3])}")
        if not insights:
            insights.append("📊 Performance is consistent — keep going!")

        sug = (
            [f"Strengthen {w}" for w in weak[:3]]
            or ["Maintain current performance"]
        )

        return {
            "breakdown": bd,
            "weak": weak,
            "strong": strong,
            "trend": trend,
            "insights": insights,
            "suggestions": sug,
        }

    async def _llm_perf(self, stu, a) -> Optional[str]:
        if not self.llm:
            return None
        try:
            resp = await self.llm.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an academic advisor at FCRIT Mumbai. "
                            "Give 2-3 specific, actionable study tips. "
                            "Be encouraging. Keep it brief."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Student: CGPA {stu.get('cgpa', '?')}, "
                            f"Semester {stu.get('semester', '?')}\n"
                            f"Weak subjects: {a['weak']}\n"
                            f"Strong subjects: {a['strong']}\n"
                            f"Trend: {a['trend']}\n"
                            f"Give brief study advice."
                        ),
                    },
                ],
                temperature=0.3,
                max_tokens=250,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"LLM perf insights failed: {e}")
            return None

    # ════════════════  ELECTIVE  ══════════════════════════

    async def _elective(
        self, query: str, ctx: Dict, stu: Optional[Dict]
    ) -> Dict[str, Any]:
        from app.models.elective import Elective

        electives = await Elective.find(Elective.is_available == True).to_list()
        if not electives:
            return {
                "type": ResponseType.TEXT.value,
                "intent": IntentType.ELECTIVE_QUERY.value,
                "content": {
                    "message": (
                        "Check the AI Recommendations section in your dashboard "
                        "for personalized elective suggestions based on your "
                        "interests and career goals."
                    ),
                },
                "confidence": "Medium",
            }

        interests = stu.get("interests", []) if stu else []
        sem = stu.get("semester", 5) if stu else 5
        if isinstance(sem, str):
            sem = int(sem) if sem.isdigit() else 5

        # Also extract interests from query
        query_interests = []
        interest_keywords = {
            "ml": "Machine Learning", "machine learning": "Machine Learning",
            "ai": "AI", "data": "Data Science", "cloud": "Cloud Computing",
            "security": "Cybersecurity", "web": "Web Development",
            "mobile": "Mobile Development", "iot": "IoT",
            "blockchain": "Blockchain",
        }
        ql = query.lower()
        for kw, interest in interest_keywords.items():
            if kw in ql:
                query_interests.append(interest)

        all_interests = list(set(interests + query_interests))

        scored = []
        for e in electives:
            sc, reasons = 0, []
            if e.semester <= sem:
                sc += 10
                reasons.append("Available for your semester")

            for i in all_interests:
                il = i.lower()
                skill_match = any(
                    il in s.lower() for s in e.skills_covered
                )
                career_match = any(
                    il in c.lower() for c in e.career_paths
                )
                name_match = il in e.name.lower()

                if skill_match or career_match or name_match:
                    sc += 20
                    reasons.append(f"Matches interest: {i}")

            if e.career_paths:
                sc += 5
                reasons.append(f"Careers: {', '.join(e.career_paths[:2])}")

            scored.append(
                {
                    "code": e.code,
                    "name": e.name,
                    "category": e.category.value,
                    "credits": e.credits,
                    "description": e.description,
                    "skills": e.skills_covered[:5],
                    "career_paths": e.career_paths[:3],
                    "difficulty": e.difficulty_level.value,
                    "score": sc,
                    "reasons": reasons,
                }
            )

        scored.sort(key=lambda x: x["score"], reverse=True)
        return {
            "type": ResponseType.ELECTIVE_RECOMMENDATION.value,
            "intent": IntentType.ELECTIVE_QUERY.value,
            "content": {
                "recommendations": scored[:5],
                "based_on": {
                    "interests": all_interests,
                    "semester": sem,
                },
                "advice": (
                    "Choose electives that align with your career goals. "
                    "Visit the Recommendations dashboard for detailed AI-powered suggestions."
                ),
            },
            "confidence": "High" if all_interests else "Medium",
        }

    # ════════════════  STUDY PLAN  ════════════════════════

    async def _study_plan(
        self, query: str, ctx: Dict, stu: Optional[Dict]
    ) -> Dict[str, Any]:
        if not stu:
            return {
                "type": ResponseType.TEXT.value,
                "intent": IntentType.STUDY_PLAN_QUERY.value,
                "content": {
                    "message": (
                        "I need your academic data to create a personalized study plan.\n\n"
                        "Please:\n"
                        "1. Complete your Academic Data Entry\n"
                        "2. Add semester grades\n"
                        "3. Come back and ask again!\n\n"
                        "I'll create a plan focusing on your weak areas."
                    ),
                },
                "confidence": "Medium",
            }

        subjects = stu.get("subjects", [])
        weak = stu.get("weak_subjects", [])

        schedule = []
        for s in subjects:
            nm = s.get("name", s.get("subject_name", "Subject"))
            sc = s.get("score", 0)
            pri = "high" if nm in weak or sc < 50 else "normal"
            schedule.append(
                {
                    "subject": nm,
                    "priority": pri,
                    "suggested_hours": 2.5 if pri == "high" else 1.5,
                }
            )
        schedule.sort(key=lambda x: 0 if x["priority"] == "high" else 1)

        goals = [
            "Complete all pending assignments",
            "Review weak subjects daily for at least 1 hour",
            "Solve previous year question papers (2 per week)",
            "Attend all lectures & labs without fail",
            "Practice coding on LeetCode/GFG for 1 hour daily",
        ]
        recs = (
            [f"Prioritize {w}" for w in weak[:3]]
            or ["Balanced study across all subjects"]
        )

        tips = await self._llm_tips(stu, weak)
        total_hours = round(sum(s["suggested_hours"] for s in schedule), 1)

        body: Dict[str, Any] = {
            "semester": stu.get("semester", "current"),
            "daily_schedule": schedule,
            "weekly_goals": goals,
            "focus_areas": weak[:5],
            "recommendations": recs,
            "total_daily_hours": total_hours,
        }
        if tips:
            body["ai_study_tips"] = tips

        return {
            "type": ResponseType.STUDY_PLAN.value,
            "intent": IntentType.STUDY_PLAN_QUERY.value,
            "content": body,
            "confidence": "High" if subjects else "Medium",
        }

    async def _llm_tips(self, stu, weak) -> Optional[str]:
        if not self.llm or not weak:
            return None
        try:
            resp = await self.llm.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Give 3 brief, specific study tips for an engineering student. "
                            "Be practical and encouraging."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Weak subjects: {', '.join(weak)}\n"
                            f"Semester: {stu.get('semester', '?')}\n"
                            f"CGPA: {stu.get('cgpa', '?')}\n"
                            f"Give 3 study tips."
                        ),
                    },
                ],
                temperature=0.3,
                max_tokens=200,
            )
            return resp.choices[0].message.content.strip()
        except Exception:
            return None

    # ════════════════  CLARIFICATION / GENERIC  ═══════════

    async def _clarification(self, q, c, s) -> Dict:
        return {
            "type": ResponseType.TEXT.value,
            "intent": IntentType.CLARIFICATION.value,
            "content": {
                "message": "Could you be more specific? I can help with:",
                "options": [
                    "📚 Syllabus & concept explanations",
                    "👨‍🏫 Faculty information & mentors",
                    "📊 Performance analysis & insights",
                    "📖 Elective recommendations",
                    "💼 Career guidance & roadmaps",
                    "📅 Personalized study plans",
                ],
                "suggestions": [
                    "How to become a data scientist?",
                    "Show my performance analysis",
                    "Which electives for ML?",
                    "Create a study plan",
                ],
            },
            "confidence": "High",
        }

    async def _generic(self, q, c, s) -> Dict:
        return {
            "type": ResponseType.TEXT.value,
            "intent": "GENERAL",
            "content": {
                "message": (
                    "I'm your Academic Guidance Assistant! I can help with:\n\n"
                    "📚 **Syllabus** — Concept explanations\n"
                    "👨‍🏫 **Faculty** — Mentor recommendations\n"
                    "📊 **Performance** — Grade analysis & insights\n"
                    "📖 **Electives** — Smart course selection\n"
                    "💼 **Career** — Detailed career roadmaps\n"
                    "📅 **Study Plan** — Personalized schedules\n\n"
                    "What would you like to know?"
                ),
                "suggestions": [
                    "How to become a data scientist?",
                    "Show my performance analysis",
                    "Which electives should I choose?",
                    "Create a study plan for me",
                    "Career in cybersecurity",
                ],
            },
            "confidence": "High",
        }

    # ── Helpers ──────────────────────────────────────────

    def _no_data(self, intent: IntentType) -> Dict:
        return {
            "type": ResponseType.TEXT.value,
            "intent": intent.value,
            "content": {
                "message": "Information not available in academic database."
            },
            "confidence": "Low",
        }

    def _error(self) -> Dict:
        return {
            "type": ResponseType.ERROR.value,
            "intent": "ERROR",
            "content": {
                "message": "An error occurred. Please try again."
            },
            "confidence": "Low",
        }