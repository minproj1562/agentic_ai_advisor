# academic-advisor/academic-advisor-backend/scripts/train_performance_weakness_models.py
"""
Training Pipeline for Performance Predictor & Weakness Detector
================================================================
Compares XGBoost, RandomForest, GradientBoosting, LightGBM.
Auto-selects best model by validation metrics.
Saves trained models + comparison report.

Usage:
    python -m scripts.generate_comprehensive_training_data
    python -m scripts.train_performance_weakness_models
"""

import os
import sys
import json
import time
import logging
import argparse
import warnings
import numpy as np
import pandas as pd
import joblib
from datetime import datetime
from typing import Dict, Any, Tuple

from sklearn.ensemble import (
    RandomForestRegressor, GradientBoostingRegressor,
    RandomForestClassifier, GradientBoostingClassifier,
)
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (
    mean_squared_error, mean_absolute_error, r2_score,
    accuracy_score, f1_score, classification_report, confusion_matrix,
)
import xgboost as xgb
import lightgbm as lgb

warnings.filterwarnings("ignore", category=UserWarning)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

SAVE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "app", "ml", "models", "saved"
)

# ═══════════════════════════════════════════════════════════════════
#  FEATURE DEFINITIONS
# ═══════════════════════════════════════════════════════════════════

PERFORMANCE_FEATURES = [
    "current_cgpa", "current_sgpa", "previous_sgpa", "sgpa_trend",
    "attendance", "assignment_completion", "quiz_average",
    "lab_performance", "project_score", "study_hours",
    "participation_score", "extracurricular", "dept_avg",
    "num_subjects", "num_backlogs", "num_strong_subjects", "num_weak_subjects",
    "avg_subject_score", "min_subject_score", "max_subject_score", "std_subject_score",
    "practical_avg", "theory_avg", "credits_completed_ratio", "semester",
]

WEAKNESS_FEATURES = [
    "subject_score", "attendance", "assignment_score", "quiz_average",
    "lab_performance", "previous_related_score", "study_hours",
    "difficulty_factor", "cgpa", "credits", "is_practical",
    "class_avg_score", "score_vs_class_avg", "trend_indicator", "semester",
]


# ═══════════════════════════════════════════════════════════════════
#  PERFORMANCE PREDICTOR TRAINING
# ═══════════════════════════════════════════════════════════════════

def train_performance_predictor(data_path: str) -> Dict[str, Any]:
    """Train and compare models for SGPA prediction (regression)."""
    logger.info("=" * 60)
    logger.info("📈 TRAINING PERFORMANCE PREDICTOR")
    logger.info("=" * 60)

    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df):,} records from {data_path}")

    X = df[PERFORMANCE_FEATURES].values
    y = df["next_sgpa"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    # ── Define candidate models ──
    candidates = {
        "XGBoost": xgb.XGBRegressor(
            n_estimators=300, max_depth=7, learning_rate=0.08,
            subsample=0.85, colsample_bytree=0.85, reg_alpha=0.1,
            reg_lambda=1.0, random_state=42, n_jobs=-1,
        ),
        "RandomForest": RandomForestRegressor(
            n_estimators=300, max_depth=12, min_samples_split=5,
            min_samples_leaf=3, random_state=42, n_jobs=-1,
        ),
        "GradientBoosting": GradientBoostingRegressor(
            n_estimators=250, max_depth=6, learning_rate=0.08,
            subsample=0.85, min_samples_split=5, random_state=42,
        ),
        "LightGBM": lgb.LGBMRegressor(
            n_estimators=300, max_depth=7, learning_rate=0.08,
            subsample=0.85, colsample_bytree=0.85, reg_alpha=0.1,
            reg_lambda=1.0, random_state=42, n_jobs=-1, verbose=-1,
        ),
    }

    results = {}
    best_name = None
    best_rmse = float("inf")
    best_model = None

    for name, model in candidates.items():
        logger.info(f"\n  Training {name}...")
        t0 = time.time()
        model.fit(X_train_s, y_train)
        train_time = time.time() - t0

        y_pred = model.predict(X_test_s)
        rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
        mae = float(mean_absolute_error(y_test, y_pred))
        r2 = float(r2_score(y_test, y_pred))

        cv = cross_val_score(model, X_train_s, y_train, cv=5, scoring="neg_root_mean_squared_error")
        cv_rmse = float(-cv.mean())
        cv_std = float(cv.std())

        results[name] = {
            "rmse": round(rmse, 4), "mae": round(mae, 4), "r2": round(r2, 4),
            "cv_rmse": round(cv_rmse, 4), "cv_std": round(cv_std, 4),
            "train_time_s": round(train_time, 2),
        }

        logger.info(f"    RMSE: {rmse:.4f}  MAE: {mae:.4f}  R²: {r2:.4f}  CV-RMSE: {cv_rmse:.4f}±{cv_std:.4f}  ({train_time:.1f}s)")

        if rmse < best_rmse:
            best_rmse = rmse
            best_name = name
            best_model = model

    logger.info(f"\n  🏆 Best model: {best_name} (RMSE={best_rmse:.4f})")

    # Feature importance
    if hasattr(best_model, "feature_importances_"):
        importance = dict(zip(PERFORMANCE_FEATURES, best_model.feature_importances_.tolist()))
        importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
    else:
        importance = {}

    # ── Save ──
    os.makedirs(SAVE_DIR, exist_ok=True)
    joblib.dump(best_model, os.path.join(SAVE_DIR, "performance_model.joblib"))
    joblib.dump(scaler, os.path.join(SAVE_DIR, "performance_scaler.joblib"))

    report = {
        "task": "performance_prediction",
        "target": "next_sgpa",
        "best_model": best_name,
        "best_rmse": round(best_rmse, 4),
        "all_results": results,
        "feature_importance": {k: round(v, 4) for k, v in list(importance.items())[:15]},
        "features": PERFORMANCE_FEATURES,
        "n_train": len(X_train),
        "n_test": len(X_test),
        "timestamp": datetime.utcnow().isoformat(),
    }

    with open(os.path.join(SAVE_DIR, "performance_training_report.json"), "w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"  ✅ Model saved to {SAVE_DIR}/performance_model.joblib")
    return report


# ═══════════════════════════════════════════════════════════════════
#  WEAKNESS DETECTOR TRAINING
# ═══════════════════════════════════════════════════════════════════

def train_weakness_detector(data_path: str) -> Dict[str, Any]:
    """Train and compare models for weakness severity classification."""
    logger.info("\n" + "=" * 60)
    logger.info("🔍 TRAINING WEAKNESS DETECTOR")
    logger.info("=" * 60)

    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df):,} records from {data_path}")

    X = df[WEAKNESS_FEATURES].values
    y_severity = df["weakness_severity"].values
    y_intervention = df["needs_intervention"].values

    # ── Train severity classifier ──
    logger.info("\n  ── Severity Classification (5-class) ──")
    X_train, X_test, ys_train, ys_test, yi_train, yi_test = train_test_split(
        X, y_severity, y_intervention, test_size=0.2, random_state=42, stratify=y_severity
    )

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    severity_candidates = {
        "XGBoost": xgb.XGBClassifier(
            n_estimators=300, max_depth=7, learning_rate=0.08,
            subsample=0.85, colsample_bytree=0.85,
            random_state=42, n_jobs=-1, eval_metric="mlogloss",
        ),
        "LightGBM": lgb.LGBMClassifier(
            n_estimators=300, max_depth=7, learning_rate=0.08,
            subsample=0.85, colsample_bytree=0.85,
            random_state=42, n_jobs=-1, verbose=-1,
        ),
        "RandomForest": RandomForestClassifier(
            n_estimators=300, max_depth=12, min_samples_split=5,
            random_state=42, n_jobs=-1,
        ),
        "GradientBoosting": GradientBoostingClassifier(
            n_estimators=200, max_depth=6, learning_rate=0.1,
            random_state=42,
        ),
    }

    severity_results = {}
    best_sev_name = None
    best_sev_f1 = 0.0
    best_sev_model = None

    for name, model in severity_candidates.items():
        logger.info(f"\n    Training {name} (severity)...")
        t0 = time.time()
        model.fit(X_train_s, ys_train)
        train_time = time.time() - t0

        y_pred = model.predict(X_test_s)
        acc = float(accuracy_score(ys_test, y_pred))
        f1_w = float(f1_score(ys_test, y_pred, average="weighted"))
        f1_m = float(f1_score(ys_test, y_pred, average="macro"))

        cv = cross_val_score(model, X_train_s, ys_train, cv=5, scoring="f1_weighted")

        severity_results[name] = {
            "accuracy": round(acc, 4), "f1_weighted": round(f1_w, 4),
            "f1_macro": round(f1_m, 4),
            "cv_f1_mean": round(float(cv.mean()), 4),
            "cv_f1_std": round(float(cv.std()), 4),
            "train_time_s": round(train_time, 2),
        }

        logger.info(f"      Acc: {acc:.4f}  F1w: {f1_w:.4f}  F1m: {f1_m:.4f}  CV: {cv.mean():.4f}±{cv.std():.4f}  ({train_time:.1f}s)")

        if f1_w > best_sev_f1:
            best_sev_f1 = f1_w
            best_sev_name = name
            best_sev_model = model

    logger.info(f"\n    🏆 Best severity model: {best_sev_name} (F1w={best_sev_f1:.4f})")

    # Per-class report for best model
    y_pred_best = best_sev_model.predict(X_test_s)
    sev_report = classification_report(ys_test, y_pred_best, output_dict=True,
                                        target_names=["none", "low", "medium", "high", "critical"])
    cm = confusion_matrix(ys_test, y_pred_best).tolist()

    logger.info(f"\n    Per-class F1 scores:")
    for cls_name in ["none", "low", "medium", "high", "critical"]:
        if cls_name in sev_report:
            f1 = sev_report[cls_name]["f1-score"]
            bar = "█" * int(f1 * 20)
            logger.info(f"      {cls_name:<10} F1={f1:.3f} {bar}")

    # ── Train intervention classifier (binary) ──
    logger.info("\n  ── Intervention Classification (binary) ──")
    
    best_int_model = lgb.LGBMClassifier(
        n_estimators=200, max_depth=6, learning_rate=0.1,
        random_state=42, n_jobs=-1, verbose=-1,
    )
    best_int_model.fit(X_train_s, yi_train)
    yi_pred = best_int_model.predict(X_test_s)
    int_acc = float(accuracy_score(yi_test, yi_pred))
    int_f1 = float(f1_score(yi_test, yi_pred))
    logger.info(f"    Intervention — Acc: {int_acc:.4f}  F1: {int_f1:.4f}")

    # Feature importance
    if hasattr(best_sev_model, "feature_importances_"):
        importance = dict(zip(WEAKNESS_FEATURES, best_sev_model.feature_importances_.tolist()))
        importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
    else:
        importance = {}

    # ── Save ──
    joblib.dump(best_sev_model, os.path.join(SAVE_DIR, "weakness_severity_model.joblib"))
    joblib.dump(best_int_model, os.path.join(SAVE_DIR, "weakness_intervention_model.joblib"))
    joblib.dump(scaler, os.path.join(SAVE_DIR, "weakness_scaler.joblib"))

    # Save severity label mapping
    severity_map = {0: "none", 1: "low", 2: "medium", 3: "high", 4: "critical"}
    with open(os.path.join(SAVE_DIR, "weakness_severity_map.json"), "w") as f:
        json.dump(severity_map, f)

    report = {
        "task": "weakness_detection",
        "severity_best_model": best_sev_name,
        "severity_best_f1_weighted": round(best_sev_f1, 4),
        "severity_results": severity_results,
        "severity_per_class": {k: v for k, v in sev_report.items() if k in ["none", "low", "medium", "high", "critical"]},
        "severity_confusion_matrix": cm,
        "intervention_accuracy": round(int_acc, 4),
        "intervention_f1": round(int_f1, 4),
        "feature_importance": {k: round(v, 4) for k, v in list(importance.items())[:15]},
        "features": WEAKNESS_FEATURES,
        "n_train": len(X_train),
        "n_test": len(X_test),
        "timestamp": datetime.utcnow().isoformat(),
    }

    with open(os.path.join(SAVE_DIR, "weakness_training_report.json"), "w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"\n  ✅ Models saved to {SAVE_DIR}/weakness_*.joblib")
    return report


# ═══════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="scripts/training_data")
    parser.add_argument("--skip-performance", action="store_true")
    parser.add_argument("--skip-weakness", action="store_true")
    args = parser.parse_args()

    logger.info("🎓 Academic Advisor — Model Training Pipeline")
    logger.info(f"   Data dir: {args.data_dir}")
    logger.info(f"   Save dir: {SAVE_DIR}\n")

    os.makedirs(SAVE_DIR, exist_ok=True)
    all_reports = {}

    if not args.skip_performance:
        perf_path = os.path.join(args.data_dir, "performance_training_data.csv")
        if os.path.exists(perf_path):
            all_reports["performance"] = train_performance_predictor(perf_path)
        else:
            logger.error(f"❌ Not found: {perf_path}. Run generate_comprehensive_training_data.py first!")

    if not args.skip_weakness:
        weak_path = os.path.join(args.data_dir, "weakness_training_data.csv")
        if os.path.exists(weak_path):
            all_reports["weakness"] = train_weakness_detector(weak_path)
        else:
            logger.error(f"❌ Not found: {weak_path}. Run generate_comprehensive_training_data.py first!")

    # ── Summary ──
    print("\n" + "=" * 60)
    print("📋 TRAINING SUMMARY")
    print("=" * 60)

    if "performance" in all_reports:
        r = all_reports["performance"]
        print(f"\n  📈 Performance Predictor:")
        print(f"     Best model:  {r['best_model']}")
        print(f"     RMSE:        {r['best_rmse']:.4f}")
        print(f"     Top features: {', '.join(list(r['feature_importance'].keys())[:5])}")

    if "weakness" in all_reports:
        r = all_reports["weakness"]
        print(f"\n  🔍 Weakness Detector:")
        print(f"     Best model:       {r['severity_best_model']}")
        print(f"     Severity F1w:     {r['severity_best_f1_weighted']:.4f}")
        print(f"     Intervention F1:  {r['intervention_f1']:.4f}")
        print(f"     Top features:     {', '.join(list(r['feature_importance'].keys())[:5])}")

    # Update master meta.json
    meta_path = os.path.join(SAVE_DIR, "meta.json")
    existing_meta = {}
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            existing_meta = json.load(f)

    existing_meta.update({
        "performance_predictor_trained": "performance" in all_reports,
        "weakness_detector_trained": "weakness" in all_reports,
        "performance_model": all_reports.get("performance", {}).get("best_model"),
        "weakness_model": all_reports.get("weakness", {}).get("severity_best_model"),
        "last_trained": datetime.utcnow().isoformat(),
    })
    with open(meta_path, "w") as f:
        json.dump(existing_meta, f, indent=2)

    print(f"\n✅ All models saved to: {SAVE_DIR}/")
    print("=" * 60)


if __name__ == "__main__":
    main()