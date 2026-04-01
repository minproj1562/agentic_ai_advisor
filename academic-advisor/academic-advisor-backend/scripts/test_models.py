# scripts/test_models.py
"""
Standalone Model Testing Script
================================
Tests all trained models on fresh synthetic data and reports metrics.

Usage:
    python -m scripts.test_models
    python -m scripts.test_models --pec-only
    python -m scripts.test_models --verbose
"""

import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sklearn.metrics import (
    accuracy_score, f1_score, classification_report, confusion_matrix,
    mean_squared_error, mean_absolute_error, r2_score,
)

# ═══════════════════════════════════════════════════════════════════
#  IMPORTS — all from the single v2 generator
# ═══════════════════════════════════════════════════════════════════

print("Loading models...")
from app.ml.models.recommendation_engine import recommendation_engine
from app.ml.models.performance_predictor import performance_predictor
from app.ml.models.weakness_detector import weakness_detector

from scripts.generate_training_data_v2 import (
    generate_pec_dataset,
    generate_oec_dataset,
    generate_performance_dataset,
    generate_weakness_dataset,
    PEC_LABELS,
    OEC_LABELS,
)

REPORT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "training_data", "test_reports"
)


# ═══════════════════════════════════════════════════════════════════
#  TEST FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def test_pec_recommender(n_per_class: int = 150, verbose: bool = False) -> Dict[str, Any]:
    """Test Program Elective Recommender on fresh data."""
    print("\n" + "=" * 60)
    print("  TESTING PROGRAM ELECTIVE RECOMMENDER")
    print("=" * 60)

    if not recommendation_engine.is_trained:
        print("  Model not trained!")
        return {"error": "not_trained"}

    print(f"  Generating {n_per_class * 4} fresh test samples...")
    test_data = generate_pec_dataset(n_per_class)

    code_to_label = {
        "ITPEC5012": "ML", "ITPEC5013": "WT",
        "ITPEC5014": "DWM", "ITPEC5015": "CCS",
    }

    y_true, y_pred, y_scores = [], [], []
    correct_by_class = {l: 0 for l in PEC_LABELS}
    total_by_class = {l: 0 for l in PEC_LABELS}

    print("  Running predictions...")
    for sample in test_data:
        true_label = sample["label"]
        y_true.append(true_label)
        total_by_class[true_label] += 1

        recs = recommendation_engine.recommend_electives(
            marks=sample["marks"],
            interests=sample["interests"],
            projects=sample["projects"],
            use_ml=True,
        )

        if recs:
            top_code = recs[0].get("elective_code", "")
            pred_label = code_to_label.get(top_code, "UNKNOWN")
            top_score = recs[0].get("match_score", 0)
        else:
            pred_label = "UNKNOWN"
            top_score = 0

        y_pred.append(pred_label)
        y_scores.append(top_score)

        if pred_label == true_label:
            correct_by_class[true_label] += 1

    accuracy = accuracy_score(y_true, y_pred)
    f1_w = f1_score(y_true, y_pred, average="weighted", labels=PEC_LABELS)
    f1_m = f1_score(y_true, y_pred, average="macro", labels=PEC_LABELS)

    per_class_acc = {
        l: correct_by_class[l] / total_by_class[l] if total_by_class[l] > 0 else 0
        for l in PEC_LABELS
    }

    print(f"\n  Results:")
    print(f"     Accuracy:       {accuracy:.4f} ({accuracy * 100:.1f}%)")
    print(f"     F1 (weighted):  {f1_w:.4f}")
    print(f"     F1 (macro):     {f1_m:.4f}")
    print(f"\n     Per-Class Accuracy:")
    for label in PEC_LABELS:
        acc = per_class_acc[label]
        bar = "=" * int(acc * 20)
        print(f"       {label}: [{bar:<20}] {acc:.3f} ({correct_by_class[label]}/{total_by_class[label]})")

    cm = confusion_matrix(y_true, y_pred, labels=PEC_LABELS)
    print(f"\n     Confusion Matrix:")
    print(f"            {'  '.join(f'{l:>4}' for l in PEC_LABELS)}")
    for i, label in enumerate(PEC_LABELS):
        row = "  ".join(f"{cm[i][j]:4d}" for j in range(len(PEC_LABELS)))
        print(f"       {label}: {row}")

    correct_scores = [y_scores[i] for i in range(len(y_true)) if y_pred[i] == y_true[i]]
    wrong_scores = [y_scores[i] for i in range(len(y_true)) if y_pred[i] != y_true[i]]

    print(f"\n     Confidence Analysis:")
    print(f"       Correct predictions avg score: {np.mean(correct_scores):.1f}")
    if wrong_scores:
        print(f"       Wrong predictions avg score:   {np.mean(wrong_scores):.1f}")

    if verbose:
        print("\n     Classification Report:")
        print(classification_report(y_true, y_pred, labels=PEC_LABELS))

    return {
        "model": "PEC Recommender",
        "accuracy": round(accuracy, 4),
        "f1_weighted": round(f1_w, 4),
        "f1_macro": round(f1_m, 4),
        "per_class_accuracy": per_class_acc,
        "confusion_matrix": cm.tolist(),
        "n_samples": len(test_data),
        "avg_confidence_correct": round(float(np.mean(correct_scores)), 2),
        "avg_confidence_wrong": round(float(np.mean(wrong_scores)), 2) if wrong_scores else None,
    }


def test_oec_recommender(n_per_class: int = 120, verbose: bool = False) -> Dict[str, Any]:
    """Test Open Elective Recommender on fresh data."""
    print("\n" + "=" * 60)
    print("  TESTING OPEN ELECTIVE RECOMMENDER")
    print("=" * 60)

    if not recommendation_engine.oe_is_trained:
        print("  OEC Model not trained!")
        return {"error": "not_trained"}

    print(f"  Generating {n_per_class * 5} fresh test samples...")
    test_data = generate_oec_dataset(n_per_class)

    code_to_label = {
        "OEC7012": "RE", "OEC7015": "OR", "OEC7016": "CSL",
        "OEC7017": "DBM", "OEC7018": "EAM",
    }

    y_true, y_pred = [], []
    correct_by_class = {l: 0 for l in OEC_LABELS}
    total_by_class = {l: 0 for l in OEC_LABELS}

    print("  Running predictions...")
    for sample in test_data:
        true_label = sample["label"]
        y_true.append(true_label)
        total_by_class[true_label] += 1

        recs = recommendation_engine.recommend_open_electives(
            marks=sample["marks"],
            interests=sample["interests"],
            projects=sample["projects"],
            use_ml=True,
        )

        if recs:
            top_code = recs[0].get("elective_code", "")
            pred_label = code_to_label.get(top_code, "UNKNOWN")
        else:
            pred_label = "UNKNOWN"

        y_pred.append(pred_label)
        if pred_label == true_label:
            correct_by_class[true_label] += 1

    accuracy = accuracy_score(y_true, y_pred)
    f1_w = f1_score(y_true, y_pred, average="weighted", labels=OEC_LABELS)
    f1_m = f1_score(y_true, y_pred, average="macro", labels=OEC_LABELS)

    per_class_acc = {
        l: correct_by_class[l] / total_by_class[l] if total_by_class[l] > 0 else 0
        for l in OEC_LABELS
    }

    print(f"\n  Results:")
    print(f"     Accuracy:       {accuracy:.4f} ({accuracy * 100:.1f}%)")
    print(f"     F1 (weighted):  {f1_w:.4f}")
    print(f"     F1 (macro):     {f1_m:.4f}")
    print(f"\n     Per-Class Accuracy:")
    for label in OEC_LABELS:
        acc = per_class_acc[label]
        bar = "=" * int(acc * 20)
        print(f"       {label}: [{bar:<20}] {acc:.3f} ({correct_by_class[label]}/{total_by_class[label]})")

    cm = confusion_matrix(y_true, y_pred, labels=OEC_LABELS)
    print(f"\n     Confusion Matrix:")
    print(f"            {'  '.join(f'{l:>4}' for l in OEC_LABELS)}")
    for i, label in enumerate(OEC_LABELS):
        row = "  ".join(f"{cm[i][j]:4d}" for j in range(len(OEC_LABELS)))
        print(f"       {label}: {row}")

    if verbose:
        print("\n     Classification Report:")
        print(classification_report(y_true, y_pred, labels=OEC_LABELS))

    return {
        "model": "OEC Recommender",
        "accuracy": round(accuracy, 4),
        "f1_weighted": round(f1_w, 4),
        "f1_macro": round(f1_m, 4),
        "per_class_accuracy": per_class_acc,
        "confusion_matrix": cm.tolist(),
        "n_samples": len(test_data),
    }


def test_performance_predictor(n_samples: int = 1000) -> Dict[str, Any]:
    """Test Performance Predictor on synthetic data."""
    print("\n" + "=" * 60)
    print("  TESTING PERFORMANCE PREDICTOR")
    print("=" * 60)

    if not performance_predictor.is_trained:
        print("  Model not trained!")
        return {"error": "not_trained"}

    print(f"  Generating {n_samples} test samples...")
    test_df = generate_performance_dataset(n_samples)

    y_true = test_df["next_sgpa"].values

    from app.ml.models.performance_predictor import FEATURE_COLUMNS
    X_test = test_df[FEATURE_COLUMNS].to_dict(orient="records")

    y_pred = []
    print("  Running predictions...")
    for record in X_test:
        result = performance_predictor.predict(record)
        y_pred.append(result["predicted_sgpa"])

    y_pred = np.array(y_pred)

    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae = float(mean_absolute_error(y_true, y_pred))
    r2 = float(r2_score(y_true, y_pred))

    errors = np.abs(y_true - y_pred)
    within_05 = float(np.mean(errors <= 0.5) * 100)
    within_1 = float(np.mean(errors <= 1.0) * 100)
    within_15 = float(np.mean(errors <= 1.5) * 100)

    print(f"\n  Results:")
    print(f"     RMSE:  {rmse:.4f}")
    print(f"     MAE:   {mae:.4f}")
    print(f"     R2:    {r2:.4f}")
    print(f"\n     Error Distribution:")
    print(f"       Within +/-0.5 SGPA: {within_05:.1f}%")
    print(f"       Within +/-1.0 SGPA: {within_1:.1f}%")
    print(f"       Within +/-1.5 SGPA: {within_15:.1f}%")

    importance = performance_predictor.get_feature_importance()
    if importance:
        top_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:5]
        print(f"\n     Top Features (importance):")
        for feat, imp in top_features:
            print(f"       {feat}: {imp:.3f}")

    return {
        "model": "Performance Predictor",
        "rmse": round(rmse, 4),
        "mae": round(mae, 4),
        "r2": round(r2, 4),
        "within_0.5": round(within_05, 1),
        "within_1.0": round(within_1, 1),
        "within_1.5": round(within_15, 1),
        "n_samples": n_samples,
    }


def test_weakness_detector(n_students: int = 500) -> Dict[str, Any]:
    """Test Weakness Detector on synthetic data."""
    print("\n" + "=" * 60)
    print("  TESTING WEAKNESS DETECTOR")
    print("=" * 60)

    if not weakness_detector.is_trained:
        print("  Model not trained (ML). Testing heuristic mode...")

    print(f"  Generating test data for {n_students} students...")
    test_df = generate_weakness_dataset(n_students)

    print("  Running weakness detection...")

    reverse_mapping = {"none": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}

    y_true_sev = test_df["weakness_severity"].values
    y_pred_sev = []

    for _, row in test_df.iterrows():
        subject_data = {
            "score": row["subject_score"],
            "attendance": row["attendance"],
            "assignment_completion": row["assignment_score"],
        }
        result = weakness_detector._analyze_subject(row["subject_name"], subject_data)
        pred_sev = reverse_mapping.get(result["severity"], 0)
        y_pred_sev.append(pred_sev)

    y_pred_sev = np.array(y_pred_sev)

    accuracy = accuracy_score(y_true_sev, y_pred_sev)
    f1_w = f1_score(y_true_sev, y_pred_sev, average="weighted")

    severity_names = ["none", "low", "medium", "high", "critical"]

    mode = "trained" if weakness_detector.is_trained else "heuristic"
    print(f"\n  Results ({mode} mode):")
    print(f"     Severity Accuracy: {accuracy:.4f} ({accuracy * 100:.1f}%)")
    print(f"     F1 (weighted):     {f1_w:.4f}")

    print(f"\n     Per-Severity Accuracy:")
    for sev_int, sev_name in enumerate(severity_names):
        mask = y_true_sev == sev_int
        if mask.sum() > 0:
            acc = accuracy_score(y_true_sev[mask], y_pred_sev[mask])
            bar = "=" * int(acc * 20)
            print(f"       {sev_name:<10}: [{bar:<20}] {acc:.3f} ({mask.sum()} samples)")

    return {
        "model": "Weakness Detector",
        "mode": mode,
        "severity_accuracy": round(accuracy, 4),
        "f1_weighted": round(f1_w, 4),
        "n_samples": len(test_df),
    }


# ═══════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Test all ML models")
    parser.add_argument("--pec-only", action="store_true", help="Test only PEC model")
    parser.add_argument("--oec-only", action="store_true", help="Test only OEC model")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--pec-samples", type=int, default=150, help="Samples per PEC class")
    parser.add_argument("--oec-samples", type=int, default=120, help="Samples per OEC class")
    parser.add_argument("--perf-samples", type=int, default=1000, help="Performance test samples")
    parser.add_argument("--weak-samples", type=int, default=500, help="Weakness test students")
    args = parser.parse_args()

    print("ML Model Testing Suite")
    print("=" * 60)
    print(f"  Testing at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = {}

    if not args.oec_only:
        results["pec"] = test_pec_recommender(args.pec_samples, args.verbose)

    if not args.pec_only:
        results["oec"] = test_oec_recommender(args.oec_samples, args.verbose)

    if not args.pec_only and not args.oec_only:
        results["performance"] = test_performance_predictor(args.perf_samples)
        results["weakness"] = test_weakness_detector(args.weak_samples)

    # Summary
    print("\n" + "=" * 60)
    print("  TEST SUMMARY")
    print("=" * 60)

    if "pec" in results and "error" not in results["pec"]:
        r = results["pec"]
        print(f"\n  PEC Recommender:")
        print(f"     Accuracy: {r['accuracy']:.4f}  F1w: {r['f1_weighted']:.4f}")

    if "oec" in results and "error" not in results["oec"]:
        r = results["oec"]
        print(f"\n  OEC Recommender:")
        print(f"     Accuracy: {r['accuracy']:.4f}  F1w: {r['f1_weighted']:.4f}")

    if "performance" in results and "error" not in results["performance"]:
        r = results["performance"]
        print(f"\n  Performance Predictor:")
        print(f"     RMSE: {r['rmse']:.4f}  R2: {r['r2']:.4f}")

    if "weakness" in results and "error" not in results["weakness"]:
        r = results["weakness"]
        print(f"\n  Weakness Detector ({r['mode']}):")
        print(f"     Severity Acc: {r['severity_accuracy']:.4f}")

    # Save report
    os.makedirs(REPORT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(REPORT_DIR, f"test_report_{timestamp}.json")

    report = {
        "timestamp": datetime.now().isoformat(),
        "results": results,
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\n  Report saved to: {report_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()