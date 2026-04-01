# scripts/train_all_models.py
"""
Unified Training Script — Trains ALL models (v2 - Optimized)
=============================================================
1. Elective Recommender   PEC: RF + KNN   (ML, WT, DWM, CCS)
2. Open Elective Recommender OEC: RF       (RE, OR, CSL, DBM, EAM)
3. Performance Predictor   (best of XGBoost/RF/GBR/LightGBM)
4. Weakness Detector       (best of XGBoost/LightGBM/RF/GBR)

Usage:
    # Generate fresh data + train (recommended)
    python -m scripts.train_all_models --generate
    
    # Train using existing data
    python -m scripts.train_all_models
    
    # Custom sample sizes
    python -m scripts.train_all_models --generate --pec 800 --oec 600
"""

import asyncio
import csv
import os
import sys
import logging
import json
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
#  PATHS
# ═══════════════════════════════════════════════════════════════

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "training_data")
SAVE_DIR = os.path.join(
    os.path.dirname(SCRIPT_DIR),
    "app", "ml", "models", "saved",
)
REPORT_DIR = os.path.join(DATA_DIR, "reports")

# Data file paths
PEC_JSON_PATH = os.path.join(DATA_DIR, "elective_training_data.json")
PEC_CSV_PATH = os.path.join(DATA_DIR, "elective_training_data.csv")
OEC_JSON_PATH = os.path.join(DATA_DIR, "oe_training_data.json")
OEC_CSV_PATH = os.path.join(DATA_DIR, "oe_training_data.csv")
PERF_CSV_PATH = os.path.join(DATA_DIR, "performance_training_data.csv")
WEAK_CSV_PATH = os.path.join(DATA_DIR, "weakness_training_data.csv")

# Default sample sizes (optimized - not excessive)
DEFAULT_PEC_PER_CLASS = 600
DEFAULT_OEC_PER_CLASS = 500
DEFAULT_PERF_SAMPLES = 6000
DEFAULT_WEAK_STUDENTS = 4000


# ═══════════════════════════════════════════════════════════════
#  DATA GENERATION (using optimized v2 generator)
# ═══════════════════════════════════════════════════════════════

def generate_all_training_data(
    pec_per_class: int = DEFAULT_PEC_PER_CLASS,
    oec_per_class: int = DEFAULT_OEC_PER_CLASS,
    perf_samples: int = DEFAULT_PERF_SAMPLES,
    weak_students: int = DEFAULT_WEAK_STUDENTS,
):
    """Generate all training data using the v2 generator."""
    logger.info("=" * 60)
    logger.info("GENERATING OPTIMIZED TRAINING DATA (v2)")
    logger.info("=" * 60)

    os.makedirs(DATA_DIR, exist_ok=True)

    # All imports from the single self-contained v2 generator
    from scripts.generate_training_data_v2 import (
        generate_pec_dataset,
        generate_oec_dataset,
        generate_performance_dataset,
        generate_weakness_dataset,
        save_elective_data,
    )

    # ── PEC Data ──
    logger.info(
        f"\n  Generating PEC data: {pec_per_class} x 4 = "
        f"{pec_per_class * 4} samples"
    )
    pec_data = generate_pec_dataset(pec_per_class)
    save_elective_data(pec_data, DATA_DIR, "elective")
    logger.info(f"     Saved {len(pec_data)} PEC samples")

    # ── OEC Data ──
    logger.info(
        f"\n  Generating OEC data: {oec_per_class} x 5 = "
        f"{oec_per_class * 5} samples"
    )
    oec_data = generate_oec_dataset(oec_per_class)
    save_elective_data(oec_data, DATA_DIR, "oe")
    logger.info(f"     Saved {len(oec_data)} OEC samples")

    # ── Performance Data ──
    logger.info(f"\n  Generating Performance data: {perf_samples} samples")
    perf_df = generate_performance_dataset(perf_samples)
    perf_df.to_csv(PERF_CSV_PATH, index=False)
    logger.info(f"     Saved {len(perf_df)} performance records")

    # ── Weakness Data ──
    logger.info(f"  Generating Weakness data: {weak_students} students")
    weak_df = generate_weakness_dataset(weak_students)
    weak_df.to_csv(WEAK_CSV_PATH, index=False)
    logger.info(f"     Saved {len(weak_df)} weakness records")

    # ── Save metadata ──
    meta = {
        "generated_at": datetime.utcnow().isoformat(),
        "generator_version": "v2",
        "pec_samples": len(pec_data),
        "oec_samples": len(oec_data),
        "performance_samples": len(perf_df),
        "weakness_samples": len(weak_df),
        "pec_per_class": pec_per_class,
        "oec_per_class": oec_per_class,
    }
    with open(os.path.join(DATA_DIR, "data_generation_meta.json"), "w") as f:
        json.dump(meta, f, indent=2)

    return {
        "pec_data": pec_data,
        "oec_data": oec_data,
        "perf_path": PERF_CSV_PATH,
        "weak_path": WEAK_CSV_PATH,
    }


# ═══════════════════════════════════════════════════════════════
#  1. PROGRAM ELECTIVE + OPEN ELECTIVE RECOMMENDERS
# ═══════════════════════════════════════════════════════════════

async def train_elective_recommenders(
    pec_data: list = None,
    oec_data: list = None,
    run_evaluation: bool = True,
):
    """Train BOTH Program Elective (PEC) and Open Elective (OEC) models."""
    logger.info("=" * 60)
    logger.info("TRAINING ELECTIVE RECOMMENDERS (PEC + OEC)")
    logger.info("=" * 60)

    from app.ml.models.recommendation_engine import recommendation_engine

    # ── Load PEC data ──
    if pec_data is None:
        if os.path.exists(PEC_JSON_PATH):
            logger.info(f"  Loading PEC data from {PEC_JSON_PATH}")
            with open(PEC_JSON_PATH) as f:
                pec_data = json.load(f)
            logger.info(f"  Loaded {len(pec_data)} PEC samples")
        else:
            logger.error(f"  PEC data not found at {PEC_JSON_PATH}")
            logger.error("     Run with --generate flag to create training data")
            return None
    else:
        logger.info(f"  Using provided PEC data: {len(pec_data)} samples")

    # ── Train PEC ──
    logger.info("  Training PEC: RandomForest(200) + KNN(5)...")
    pec_metrics = recommendation_engine.train(pec_data, test_size=0.2)

    logger.info(f"\n  PEC Results:")
    logger.info(f"     Accuracy:      {pec_metrics['accuracy']:.4f}")
    logger.info(f"     F1 (weighted): {pec_metrics['f1_weighted']:.4f}")
    logger.info(
        f"     Cross-val:     {pec_metrics['cross_val_mean']:.4f}"
        f" +/- {pec_metrics['cross_val_std']:.4f}"
    )
    if "per_class" in pec_metrics:
        logger.info("     Per-Class:")
        for cls, m in pec_metrics["per_class"].items():
            logger.info(
                f"       {cls}: P={m['precision']:.3f} "
                f"R={m['recall']:.3f} F1={m['f1']:.3f}"
            )

    # ── Load OEC data ──
    if oec_data is None:
        if os.path.exists(OEC_JSON_PATH):
            logger.info(f"\n  Loading OEC data from {OEC_JSON_PATH}")
            with open(OEC_JSON_PATH) as f:
                oec_data = json.load(f)
            logger.info(f"  Loaded {len(oec_data)} OEC samples")
        else:
            logger.error(f"  OEC data not found at {OEC_JSON_PATH}")
            logger.error("     Run with --generate flag to create training data")
            return None
    else:
        logger.info(f"  Using provided OEC data: {len(oec_data)} samples")

    # ── Train OEC ──
    logger.info("  Training OEC: RandomForest(200)...")
    oec_metrics = recommendation_engine.train_open_electives(oec_data, test_size=0.2)

    logger.info(f"\n  OEC Results:")
    logger.info(f"     Accuracy:      {oec_metrics['accuracy']:.4f}")
    logger.info(f"     F1 (weighted): {oec_metrics['f1_weighted']:.4f}")
    logger.info(
        f"     Cross-val:     {oec_metrics['cross_val_mean']:.4f}"
        f" +/- {oec_metrics['cross_val_std']:.4f}"
    )
    if "per_class" in oec_metrics:
        logger.info("     Per-Class:")
        for cls, m in oec_metrics["per_class"].items():
            logger.info(
                f"       {cls}: P={m['precision']:.3f} "
                f"R={m['recall']:.3f} F1={m['f1']:.3f}"
            )

    # ── Evaluate on fresh data (optional) ──
    eval_results = {}
    if run_evaluation:
        logger.info("\n  Evaluating on fresh test set...")
        try:
            from scripts.generate_training_data_v2 import (
                generate_pec_dataset as gen_pec_test,
                generate_oec_dataset as gen_oec_test,
            )

            # PEC fresh eval
            pec_test = gen_pec_test(150)
            code_to_label = {
                "ITPEC5012": "ML", "ITPEC5013": "WT",
                "ITPEC5014": "DWM", "ITPEC5015": "CCS",
            }
            pec_correct, pec_total = 0, 0
            pec_per_class_c = {"ML": 0, "WT": 0, "DWM": 0, "CCS": 0}
            pec_per_class_t = {"ML": 0, "WT": 0, "DWM": 0, "CCS": 0}

            for sample in pec_test:
                true_label = sample["label"]
                pec_per_class_t[true_label] += 1
                pec_total += 1
                recs = recommendation_engine.recommend_electives(
                    marks=sample["marks"],
                    interests=sample["interests"],
                    projects=sample["projects"],
                    use_ml=True,
                )
                if recs:
                    pred = code_to_label.get(recs[0].get("elective_code", ""), "")
                    if pred == true_label:
                        pec_correct += 1
                        pec_per_class_c[true_label] += 1

            pec_acc = pec_correct / pec_total if pec_total > 0 else 0
            pec_per_class_acc = {
                l: pec_per_class_c[l] / pec_per_class_t[l]
                if pec_per_class_t[l] > 0 else 0
                for l in ["ML", "WT", "DWM", "CCS"]
            }

            logger.info(f"     PEC fresh accuracy: {pec_acc:.4f}")
            for cls, acc in pec_per_class_acc.items():
                bar = "=" * int(acc * 20)
                logger.info(f"       {cls}: [{bar:<20}] {acc:.4f}")

            eval_results["program_electives"] = {
                "accuracy": round(pec_acc, 4),
                "per_class_accuracy": {
                    k: round(v, 4) for k, v in pec_per_class_acc.items()
                },
            }

            # OEC fresh eval
            if recommendation_engine.oe_is_trained:
                oec_test = gen_oec_test(120)
                oe_code_to_label = {
                    "OEC7012": "RE", "OEC7015": "OR", "OEC7016": "CSL",
                    "OEC7017": "DBM", "OEC7018": "EAM",
                }
                oe_correct, oe_total = 0, 0
                oe_per_c = {l: 0 for l in ["RE", "OR", "CSL", "DBM", "EAM"]}
                oe_per_t = {l: 0 for l in ["RE", "OR", "CSL", "DBM", "EAM"]}

                for sample in oec_test:
                    true_label = sample["label"]
                    oe_per_t[true_label] += 1
                    oe_total += 1
                    recs = recommendation_engine.recommend_open_electives(
                        marks=sample["marks"],
                        interests=sample["interests"],
                        projects=sample["projects"],
                        use_ml=True,
                    )
                    if recs:
                        pred = oe_code_to_label.get(
                            recs[0].get("elective_code", ""), ""
                        )
                        if pred == true_label:
                            oe_correct += 1
                            oe_per_c[true_label] += 1

                oe_acc = oe_correct / oe_total if oe_total > 0 else 0
                oe_per_acc = {
                    l: oe_per_c[l] / oe_per_t[l] if oe_per_t[l] > 0 else 0
                    for l in ["RE", "OR", "CSL", "DBM", "EAM"]
                }

                logger.info(f"     OEC fresh accuracy: {oe_acc:.4f}")
                for cls, acc in oe_per_acc.items():
                    bar = "=" * int(acc * 20)
                    logger.info(f"       {cls}: [{bar:<20}] {acc:.4f}")

                eval_results["open_electives"] = {
                    "accuracy": round(oe_acc, 4),
                    "per_class_accuracy": {
                        k: round(v, 4) for k, v in oe_per_acc.items()
                    },
                }

        except Exception as e:
            logger.warning(f"     Evaluation failed: {e}")
            import traceback
            traceback.print_exc()

    # Return combined metrics
    return {
        # PEC metrics
        "accuracy": pec_metrics["accuracy"],
        "f1_weighted": pec_metrics["f1_weighted"],
        "f1_macro": pec_metrics["f1_macro"],
        "cross_val_mean": pec_metrics["cross_val_mean"],
        "cross_val_std": pec_metrics["cross_val_std"],
        "per_class": pec_metrics.get("per_class", {}),
        "confusion_matrix": pec_metrics.get("confusion_matrix", []),
        "pec_samples": len(pec_data),
        # OEC metrics
        "oec_accuracy": oec_metrics["accuracy"],
        "oec_f1_weighted": oec_metrics["f1_weighted"],
        "oec_f1_macro": oec_metrics.get("f1_macro", 0),
        "oec_cross_val_mean": oec_metrics.get("cross_val_mean", 0),
        "oec_cross_val_std": oec_metrics.get("cross_val_std", 0),
        "oec_per_class": oec_metrics.get("per_class", {}),
        "oec_confusion_matrix": oec_metrics.get("confusion_matrix", []),
        "oec_samples": len(oec_data),
        # Fresh evaluation
        "fresh_eval": eval_results,
    }


# ═══════════════════════════════════════════════════════════════
#  2. PERFORMANCE PREDICTOR + WEAKNESS DETECTOR
# ═══════════════════════════════════════════════════════════════

async def train_performance_and_weakness(
    perf_path: str = None,
    weak_path: str = None,
):
    """Train Performance Predictor and Weakness Detector."""
    logger.info("\n" + "=" * 60)
    logger.info("TRAINING PERFORMANCE & WEAKNESS MODELS")
    logger.info("=" * 60)

    from scripts.train_performance_weakness_models import (
        train_performance_predictor,
        train_weakness_detector,
    )

    perf_path = perf_path or PERF_CSV_PATH
    weak_path = weak_path or WEAK_CSV_PATH

    results = {}

    # ── Performance Predictor ──
    if os.path.exists(perf_path):
        logger.info(f"  Training Performance Predictor from {perf_path}")
        results["performance"] = train_performance_predictor(perf_path)
    else:
        logger.error(
            f"  {perf_path} not found. "
            "Run with --generate flag first!"
        )

    # ── Weakness Detector ──
    if os.path.exists(weak_path):
        logger.info(f"  Training Weakness Detector from {weak_path}")
        results["weakness"] = train_weakness_detector(weak_path)
    else:
        logger.error(
            f"  {weak_path} not found. "
            "Run with --generate flag first!"
        )

    return results


# ═══════════════════════════════════════════════════════════════
#  REPORTING
# ═══════════════════════════════════════════════════════════════

def save_training_report(
    elective_metrics: dict,
    pw_results: dict,
    timestamp: str,
):
    """Save comprehensive training report."""
    os.makedirs(REPORT_DIR, exist_ok=True)

    # Combined JSON report
    combined_report = {
        "training_timestamp": datetime.utcnow().isoformat(),
        "program_elective_recommender": {
            "model": "RandomForest(200) + KNN(5)",
            "accuracy": elective_metrics["accuracy"],
            "f1_weighted": elective_metrics["f1_weighted"],
            "f1_macro": elective_metrics["f1_macro"],
            "cross_val": (
                f"{elective_metrics['cross_val_mean']:.4f}"
                f"+/-{elective_metrics['cross_val_std']:.4f}"
            ),
            "per_class": elective_metrics.get("per_class", {}),
            "n_samples": elective_metrics.get("pec_samples", 0),
        },
        "open_elective_recommender": {
            "model": "RandomForest(200)",
            "accuracy": elective_metrics.get("oec_accuracy"),
            "f1_weighted": elective_metrics.get("oec_f1_weighted"),
            "per_class": elective_metrics.get("oec_per_class", {}),
            "n_samples": elective_metrics.get("oec_samples", 0),
        },
    }

    if "performance" in pw_results:
        combined_report["performance_predictor"] = pw_results["performance"]
    if "weakness" in pw_results:
        combined_report["weakness_detector"] = pw_results["weakness"]

    if elective_metrics.get("fresh_eval"):
        combined_report["fresh_evaluation"] = elective_metrics["fresh_eval"]

    combined_path = os.path.join(
        REPORT_DIR, f"training_report_{timestamp}.json"
    )
    with open(combined_path, "w", encoding="utf-8") as f:
        json.dump(combined_report, f, indent=2, default=str)
    logger.info(f"\n  Combined report: {combined_path}")

    # Model comparison CSV
    csv_path = os.path.join(
        REPORT_DIR, f"model_comparison_{timestamp}.csv"
    )
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Task", "Model", "Primary Metric", "Value",
            "Secondary Metric", "Value", "CV Score", "N Samples",
        ])

        writer.writerow([
            "PEC Recommender", "RandomForest(200)+KNN(5)",
            "Accuracy", f"{elective_metrics['accuracy']:.4f}",
            "F1 Weighted", f"{elective_metrics['f1_weighted']:.4f}",
            (
                f"{elective_metrics['cross_val_mean']:.4f}"
                f"+/-{elective_metrics['cross_val_std']:.4f}"
            ),
            elective_metrics.get("pec_samples", "-"),
        ])

        writer.writerow([
            "OEC Recommender", "RandomForest(200)",
            "Accuracy",
            f"{elective_metrics.get('oec_accuracy', 0):.4f}",
            "F1 Weighted",
            f"{elective_metrics.get('oec_f1_weighted', 0):.4f}",
            (
                f"{elective_metrics.get('oec_cross_val_mean', 0):.4f}"
                f"+/-{elective_metrics.get('oec_cross_val_std', 0):.4f}"
            ),
            elective_metrics.get("oec_samples", "-"),
        ])

        if "performance" in pw_results:
            pr = pw_results["performance"]
            for model_name, mm in pr.get("all_results", {}).items():
                is_best = (
                    " [BEST]" if model_name == pr["best_model"] else ""
                )
                writer.writerow([
                    f"Perf. Predictor{is_best}", model_name,
                    "RMSE", f"{mm['rmse']:.4f}",
                    "R2", f"{mm['r2']:.4f}",
                    f"{mm['cv_rmse']:.4f}+/-{mm['cv_std']:.4f}",
                    pr.get("n_train", "-"),
                ])

        if "weakness" in pw_results:
            wr = pw_results["weakness"]
            for model_name, mm in wr.get("severity_results", {}).items():
                is_best = (
                    " [BEST]"
                    if model_name == wr["severity_best_model"]
                    else ""
                )
                writer.writerow([
                    f"Weakness Detector{is_best}", model_name,
                    "F1 Weighted", f"{mm['f1_weighted']:.4f}",
                    "Accuracy", f"{mm['accuracy']:.4f}",
                    f"{mm['cv_f1_mean']:.4f}+/-{mm['cv_f1_std']:.4f}",
                    wr.get("n_train", "-"),
                ])

    logger.info(f"  Comparison CSV: {csv_path}")


# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════

async def main():
    parser = argparse.ArgumentParser(
        description="Train all Academic Advisor ML models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate fresh data and train (recommended)
  python -m scripts.train_all_models --generate
  
  # Train using existing data files
  python -m scripts.train_all_models
  
  # Custom sample sizes (smaller for testing)
  python -m scripts.train_all_models --generate --pec 300 --oec 250
  
  # Skip certain models
  python -m scripts.train_all_models --skip-perf-weak
        """,
    )
    parser.add_argument(
        "--generate", "-g", action="store_true",
        help="Generate fresh training data before training",
    )
    parser.add_argument(
        "--pec", type=int, default=DEFAULT_PEC_PER_CLASS,
        help=f"Samples per PEC class (default: {DEFAULT_PEC_PER_CLASS})",
    )
    parser.add_argument(
        "--oec", type=int, default=DEFAULT_OEC_PER_CLASS,
        help=f"Samples per OEC class (default: {DEFAULT_OEC_PER_CLASS})",
    )
    parser.add_argument(
        "--perf", type=int, default=DEFAULT_PERF_SAMPLES,
        help=f"Performance predictor samples (default: {DEFAULT_PERF_SAMPLES})",
    )
    parser.add_argument(
        "--weak", type=int, default=DEFAULT_WEAK_STUDENTS,
        help=f"Weakness detector students (default: {DEFAULT_WEAK_STUDENTS})",
    )
    parser.add_argument(
        "--skip-perf-weak", action="store_true",
        help="Skip Performance Predictor and Weakness Detector training",
    )
    parser.add_argument(
        "--skip-eval", action="store_true",
        help="Skip fresh data evaluation after training",
    )
    args = parser.parse_args()

    logger.info("Academic Advisor - Complete Model Training Pipeline")
    logger.info("=" * 60)
    logger.info(f"  Data directory:  {DATA_DIR}")
    logger.info(f"  Model save dir:  {SAVE_DIR}")
    logger.info(f"  Generate data:   {args.generate}")
    logger.info(f"  PEC per class:   {args.pec}")
    logger.info(f"  OEC per class:   {args.oec}")
    logger.info(f"  Perf samples:    {args.perf}")
    logger.info(f"  Weak students:   {args.weak}")
    logger.info("=" * 60)

    os.makedirs(SAVE_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)

    # ── Generate data if requested ──
    generated_data = {}
    if args.generate:
        generated_data = generate_all_training_data(
            pec_per_class=args.pec,
            oec_per_class=args.oec,
            perf_samples=args.perf,
            weak_students=args.weak,
        )

    # ── Train Elective Recommenders ──
    elective_metrics = await train_elective_recommenders(
        pec_data=generated_data.get("pec_data"),
        oec_data=generated_data.get("oec_data"),
        run_evaluation=not args.skip_eval,
    )

    if elective_metrics is None:
        logger.error("Elective training failed. Exiting.")
        return

    # ── Train Performance & Weakness models ──
    pw_results = {}
    if not args.skip_perf_weak:
        pw_results = await train_performance_and_weakness(
            perf_path=generated_data.get("perf_path"),
            weak_path=generated_data.get("weak_path"),
        )

    # ── Summary ──
    print("\n" + "=" * 60)
    print("COMPLETE TRAINING SUMMARY")
    print("=" * 60)

    print(f"\n  Program Elective Recommender:")
    print(f"     Model:    RandomForest(200) + KNN(5)")
    print(f"     Samples:  {elective_metrics.get('pec_samples', 'N/A')}")
    print(f"     Accuracy: {elective_metrics['accuracy']:.4f}")
    print(f"     F1w:      {elective_metrics['f1_weighted']:.4f}")
    print(
        f"     CV:       {elective_metrics['cross_val_mean']:.4f} "
        f"+/- {elective_metrics['cross_val_std']:.4f}"
    )

    print(f"\n  Open Elective Recommender (Sem VII):")
    print(f"     Model:    RandomForest(200)")
    print(f"     Samples:  {elective_metrics.get('oec_samples', 'N/A')}")
    print(f"     Accuracy: {elective_metrics.get('oec_accuracy', 0):.4f}")
    print(f"     F1w:      {elective_metrics.get('oec_f1_weighted', 0):.4f}")

    if "performance" in pw_results:
        r = pw_results["performance"]
        print(f"\n  Performance Predictor:")
        print(f"     Model:    {r['best_model']}")
        print(
            f"     Samples:  {r.get('n_train', 'N/A')} train / "
            f"{r.get('n_test', 'N/A')} test"
        )
        print(f"     RMSE:     {r['best_rmse']:.4f}")
        print(
            f"     R2:       "
            f"{r['all_results'][r['best_model']]['r2']:.4f}"
        )

    if "weakness" in pw_results:
        r = pw_results["weakness"]
        print(f"\n  Weakness Detector:")
        print(f"     Model:        {r['severity_best_model']}")
        print(
            f"     Samples:      {r.get('n_train', 'N/A')} train / "
            f"{r.get('n_test', 'N/A')} test"
        )
        print(f"     Severity F1w: {r['severity_best_f1_weighted']:.4f}")
        print(f"     Interv. F1:   {r['intervention_f1']:.4f}")

    # ── Update meta.json ──
    meta_path = os.path.join(SAVE_DIR, "meta.json")
    meta = {}
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            meta = json.load(f)

    meta.update({
        "elective_recommender_trained": True,
        "elective_accuracy": elective_metrics.get("accuracy"),
        "elective_samples": elective_metrics.get("pec_samples"),
        "oe_recommender_trained": True,
        "oe_accuracy": elective_metrics.get("oec_accuracy"),
        "oe_samples": elective_metrics.get("oec_samples"),
        "performance_predictor_trained": "performance" in pw_results,
        "performance_model": pw_results.get("performance", {}).get(
            "best_model"
        ),
        "weakness_detector_trained": "weakness" in pw_results,
        "weakness_model": pw_results.get("weakness", {}).get(
            "severity_best_model"
        ),
        "all_models_trained": datetime.utcnow().isoformat(),
    })

    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    print(f"\n  All models saved to: {SAVE_DIR}/")
    print("=" * 60)

    # List saved files
    print("\n  Saved model files:")
    for fname in sorted(os.listdir(SAVE_DIR)):
        fpath = os.path.join(SAVE_DIR, fname)
        size_kb = os.path.getsize(fpath) / 1024
        print(f"    {fname:<45} {size_kb:>8.1f} KB")

    # ── Save reports ──
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    save_training_report(elective_metrics, pw_results, timestamp)

    print(f"\n  All reports in: {REPORT_DIR}/")
    print("=" * 60)
    print("\nTraining complete!")


if __name__ == "__main__":
    asyncio.run(main())