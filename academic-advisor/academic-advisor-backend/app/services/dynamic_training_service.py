# app/services/dynamic_training_service.py
"""
Dynamic Training Service
========================
Auto-generates training data and retrains the recommendation engine
when admins add/modify electives. Uses real student marks from DB.
"""

import logging
import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class DynamicTrainingService:
    """
    Handles dynamic elective training data generation and model retraining.
    Triggered automatically when admin adds/updates/deletes electives.
    """

    def __init__(self):
        self._training_lock = asyncio.Lock()
        self._last_train_time: Optional[datetime] = None
        self._training_status = "idle"  # idle, generating, training, done, error
        self._last_error: Optional[str] = None

    @property
    def status(self) -> Dict[str, Any]:
        return {
            "status": self._training_status,
            "last_trained": self._last_train_time.isoformat() if self._last_train_time else None,
            "last_error": self._last_error,
        }

    async def on_elective_changed(self, action: str, elective_data: dict):
        """
        Called when admin creates/updates/deletes an elective.
        Triggers background retraining.
        """
        logger.info(f"Elective {action}: {elective_data.get('name', 'unknown')}")
        asyncio.create_task(self._retrain_in_background())

    async def trigger_retrain(self) -> Dict[str, Any]:
        """Manual retrain trigger from admin API."""
        if self._training_status == "training":
            return {"status": "already_training", "message": "Training is already in progress"}
        asyncio.create_task(self._retrain_in_background())
        return {"status": "started", "message": "Retraining started in background"}

    async def _retrain_in_background(self):
        """Background task to generate training data and retrain."""
        if self._training_lock.locked():
            logger.info("Training already in progress, skipping")
            return

        async with self._training_lock:
            try:
                self._training_status = "generating"
                logger.info("🔄 Generating training data from real student marks...")

                # Step 1: Fetch real student data from DB
                student_data = await self._fetch_student_marks()
                if not student_data:
                    self._training_status = "error"
                    self._last_error = "No student data found in DB"
                    return

                # Step 2: Fetch current elective catalog from DB
                elective_catalog = await self._fetch_elective_catalog()

                # Step 3: Generate training data
                pec_data, oec_data = self._generate_elective_training(
                    student_data, elective_catalog
                )

                # Step 4: Retrain the model
                self._training_status = "training"
                logger.info("🔄 Retraining recommendation engine...")
                await self._retrain_model(pec_data, oec_data)

                # Step 5: Invalidate caches
                await self._invalidate_caches()

                self._training_status = "done"
                self._last_train_time = datetime.utcnow()
                self._last_error = None
                logger.info("✅ Retraining complete!")

            except Exception as e:
                self._training_status = "error"
                self._last_error = str(e)
                logger.error(f"❌ Retraining failed: {e}", exc_info=True)

    async def _fetch_student_marks(self) -> Dict[str, List[Dict]]:
        """Fetch all student marks from MongoDB."""
        try:
            from app.models.student_profile import StudentProfile

            profiles = await StudentProfile.find_all().to_list()
            student_data = {}

            for profile in profiles:
                name = profile.name or str(profile.roll_number)
                semesters = []

                for sem in (profile.semester_records or []):
                    sem_data = {
                        "semester": sem.semester,
                        "theory_marks": {},
                        "practical_marks": {},
                        "sgpi": sem.sgpi or 0.0,
                        "cgpi": profile.cgpa or 0.0,
                    }
                    for subj in (sem.subjects or []):
                        mark_info = {
                            "raw": subj.total_marks,
                            "max": 100,
                            "pct": subj.total_marks,
                        }
                        if subj.is_practical:
                            sem_data["practical_marks"][subj.subject_name] = mark_info
                        else:
                            sem_data["theory_marks"][subj.subject_name] = mark_info

                    # Lab performance from practical marks
                    prac_pcts = [p["pct"] for p in sem_data["practical_marks"].values() if p["pct"] > 0]
                    sem_data["lab_performance"] = np.mean(prac_pcts) if prac_pcts else 50.0

                    semesters.append(sem_data)

                if semesters:
                    student_data[name] = semesters

            logger.info(f"Fetched marks for {len(student_data)} students")
            return student_data

        except Exception as e:
            logger.error(f"Error fetching student marks: {e}")
            return {}

    async def _fetch_elective_catalog(self) -> Dict[str, Dict]:
        """Fetch current elective catalog from DB."""
        try:
            from app.models.elective import ElectiveCourse

            electives = await ElectiveCourse.find_all().to_list()
            catalog = {}

            for e in electives:
                code = e.code or e.short_code or str(e.id)
                catalog[code] = {
                    "name": e.name,
                    "code": code,
                    "category": e.category,
                    "semester": e.semester,
                    "topics": getattr(e, "topics", []),
                    "skills_covered": getattr(e, "skills_covered", []),
                    "career_paths": getattr(e, "career_paths", []),
                }

            logger.info(f"Fetched {len(catalog)} electives from DB")
            return catalog

        except Exception as e:
            logger.warning(f"Could not fetch elective catalog: {e}")
            return {}

    def _generate_elective_training(
        self, student_data: Dict, elective_catalog: Dict
    ) -> tuple:
        """Generate training data using real student marks."""
        from app.ml.models.recommendation_engine import (
            CANONICAL_SUBJECTS, INTEREST_AREAS, ELECTIVE_META,
            OPEN_ELECTIVE_META, SUBJECT_WEIGHTS, OE_SUBJECT_WEIGHTS,
        )

        pec_labels = list(ELECTIVE_META.keys())
        oec_labels = list(OPEN_ELECTIVE_META.keys())

        # Add any new electives from DB that aren't in the hardcoded catalog
        for code, info in elective_catalog.items():
            short = code.upper()[:4]
            cat = info.get("category", "").lower()
            if "program" in cat and short not in pec_labels:
                pec_labels.append(short)
            elif "open" in cat and short not in oec_labels:
                oec_labels.append(short)

        pec_rows, oec_rows = [], []

        for name, semesters in student_data.items():
            # Merge marks across semesters
            marks = {}
            for sem in semesters:
                for subj, info in sem.get("theory_marks", {}).items():
                    marks[subj] = info["pct"]

            if not marks:
                continue

            lab_perfs = [s.get("lab_performance", 50) for s in semesters]
            avg_lab = float(np.mean(lab_perfs))
            sgpis = [s.get("sgpi", 5.0) for s in semesters]
            avg_sgpi = float(np.mean(sgpis))

            # Score each PEC
            pec_scores = {}
            for lbl in pec_labels:
                weights = SUBJECT_WEIGHTS.get(lbl, {})
                score = sum(marks.get(s, 50) * w for s, w in weights.items())
                pec_scores[lbl] = score
            best_pec = max(pec_scores, key=pec_scores.get) if pec_scores else pec_labels[0]

            # Score each OEC
            oec_scores = {}
            for lbl in oec_labels:
                weights = OE_SUBJECT_WEIGHTS.get(lbl, {})
                score = sum(marks.get(s, 50) * w for s, w in weights.items())
                oec_scores[lbl] = score
            best_oec = max(oec_scores, key=oec_scores.get) if oec_scores else oec_labels[0]

            interest = np.random.choice(INTEREST_AREAS)

            base = {}
            for subj in CANONICAL_SUBJECTS:
                base[subj] = marks.get(subj, 50.0)
            base["lab_performance"] = avg_lab
            base["sgpi"] = avg_sgpi
            base["interest_area"] = interest

            pec_rows.append({**base, "recommended_pec": best_pec})
            oec_rows.append({**base, "recommended_oec": best_oec})

            # Augment with noise (5x)
            for _ in range(5):
                noisy = {}
                for k, v in base.items():
                    if isinstance(v, (int, float)):
                        noisy[k] = float(np.clip(v + np.random.normal(0, 3), 0, 100))
                    else:
                        noisy[k] = v
                noisy["interest_area"] = np.random.choice(INTEREST_AREAS)
                pec_rows.append({**noisy, "recommended_pec": best_pec})
                oec_rows.append({**noisy, "recommended_oec": best_oec})

        return pd.DataFrame(pec_rows), pd.DataFrame(oec_rows)

    async def _retrain_model(self, pec_df: pd.DataFrame, oec_df: pd.DataFrame):
        """Retrain the recommendation engine with new data."""
        try:
            from app.ml.models.recommendation_engine import recommendation_engine
            import os

            save_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "ml", "models", "saved",
            )
            os.makedirs(save_dir, exist_ok=True)

            # Save training data
            pec_path = os.path.join(save_dir, "pec_training_data.csv")
            oec_path = os.path.join(save_dir, "oec_training_data.csv")
            pec_df.to_csv(pec_path, index=False)
            oec_df.to_csv(oec_path, index=False)

            logger.info(f"Saved training data: PEC={len(pec_df)}, OEC={len(oec_df)}")

            # Retrain if the engine has a train method
            if hasattr(recommendation_engine, 'train_pec_model'):
                recommendation_engine.train_pec_model(pec_df)
                logger.info("✅ PEC model retrained")

            if hasattr(recommendation_engine, 'train_oec_model'):
                recommendation_engine.train_oec_model(oec_df)
                logger.info("✅ OEC model retrained")

        except Exception as e:
            logger.error(f"Model retraining error: {e}", exc_info=True)
            raise

    async def _invalidate_caches(self):
        """Clear recommendation caches after retraining."""
        try:
            from app.models.recommendation import RecommendationRecord
            # Delete cached recommendations so they regenerate with new model
            result = await RecommendationRecord.find_all().delete()
            logger.info(f"Invalidated recommendation cache")
        except Exception as e:
            logger.warning(f"Cache invalidation warning: {e}")


# Singleton
_dynamic_training_service: Optional[DynamicTrainingService] = None


def get_dynamic_training_service() -> DynamicTrainingService:
    global _dynamic_training_service
    if _dynamic_training_service is None:
        _dynamic_training_service = DynamicTrainingService()
    return _dynamic_training_service
