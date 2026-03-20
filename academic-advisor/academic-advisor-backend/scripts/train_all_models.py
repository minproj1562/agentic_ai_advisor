# academic-advisor/academic-advisor-backend/scripts/train_all_models.py
"""
Unified Training Script — Trains ALL models
=============================================
1. Elective Recommender (RF + KNN with diverse data)
2. Performance Predictor (best of XGBoost/RF/GBR/LightGBM)
3. Weakness Detector (best of XGBoost/LightGBM/RF/GBR)

Usage:
    python -m scripts.generate_comprehensive_training_data --students 15000
    python -m scripts.train_all_models
"""

import asyncio
import os
import sys
import logging
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "training_data")
SAVE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "app", "ml", "models", "saved"
)


async def train_elective_recommender():
    """Train the elective recommendation model with diverse data."""
    logger.info("=" * 60)
    logger.info("🎯 TRAINING ELECTIVE RECOMMENDER")
    logger.info("=" * 60)

    from app.ml.utils.training import (
        generate_training_dataset,
        generate_training_csv,
    )
    from app.ml.models.recommendation_engine import recommendation_engine

    # Check if pre-generated data exists
    json_path = os.path.join(DATA_DIR, "elective_training_data.json")
    if os.path.exists(json_path):
        logger.info(f"  Loading pre-generated data from {json_path}")
        with open(json_path) as f:
            training_data = json.load(f)
        logger.info(f"  Loaded {len(training_data)} samples")
    else:
        logger.info("  Generating fresh training data (1500 per class)...")
        training_data = generate_training_dataset(
            n_samples_per_class=1500,
            include_hard_samples=True,
        )
        # Export CSV for review
        csv_path = os.path.join(DATA_DIR, "elective_training_data.csv")
        os.makedirs(DATA_DIR, exist_ok=True)
        generate_training_csv(training_data, csv_path)

    # Train
    logger.info("  Training RandomForest(200) + KNN(5)...")
    metrics = recommendation_engine.train(training_data, test_size=0.2)

    logger.info(f"\n  📊 Results:")
    logger.info(f"     Accuracy:      {metrics['accuracy']:.4f} ({metrics['accuracy']*100:.2f}%)")
    logger.info(f"     F1 (weighted): {metrics['f1_weighted']:.4f}")
    logger.info(f"     F1 (macro):    {metrics['f1_macro']:.4f}")
    logger.info(f"     Cross-val:     {metrics['cross_val_mean']:.4f} ± {metrics['cross_val_std']:.4f}")

    if "per_class" in metrics:
        logger.info(f"\n     Per-Class:")
        for cls, m in metrics["per_class"].items():
            logger.info(f"       {cls}: P={m['precision']:.3f} R={m['recall']:.3f} F1={m['f1']:.3f}")

    if "confusion_matrix" in metrics:
        labels = ["CCS", "DWM", "ML", "WT"]
        cm = metrics["confusion_matrix"]
        logger.info(f"\n     Confusion Matrix:")
        logger.info(f"     {'':>6} " + " ".join(f"{l:>6}" for l in labels))
        for i, row in enumerate(cm):
            logger.info(f"     {labels[i]:>6} " + " ".join(f"{v:>6}" for v in row))

    # Evaluate on fresh data
    logger.info("\n  🧪 Evaluating on fresh test set...")
    from app.ml.utils.training import evaluate_model_accuracy
    eval_results = await evaluate_model_accuracy(n_test_per_class=300)
    logger.info(f"     Fresh test accuracy: {eval_results.get('accuracy', 0):.4f}")
    if "per_class_accuracy" in eval_results:
        for cls, acc in eval_results["per_class_accuracy"].items():
            bar = "█" * int(acc * 20)
            logger.info(f"       {cls}: {bar} {acc:.4f}")

    return metrics


async def train_performance_and_weakness():
    """Train performance predictor and weakness detector."""
    from scripts.train_performance_weakness_models import (
        train_performance_predictor,
        train_weakness_detector,
    )

    perf_path = os.path.join(DATA_DIR, "performance_training_data.csv")
    weak_path = os.path.join(DATA_DIR, "weakness_training_data.csv")

    results = {}

    if os.path.exists(perf_path):
        results["performance"] = train_performance_predictor(perf_path)
    else:
        logger.error(f"❌ {perf_path} not found. Run generate_comprehensive_training_data.py first!")

    if os.path.exists(weak_path):
        results["weakness"] = train_weakness_detector(weak_path)
    else:
        logger.error(f"❌ {weak_path} not found. Run generate_comprehensive_training_data.py first!")

    return results


async def main():
    logger.info("🎓 Academic Advisor — Complete Model Training Pipeline")
    logger.info("=" * 60)

    os.makedirs(SAVE_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)

    # ── 1. Elective Recommender ──
    elective_metrics = await train_elective_recommender()

    # ── 2. Performance Predictor + Weakness Detector ──
    pw_results = await train_performance_and_weakness()

    # ── Summary ──
    print("\n" + "=" * 60)
    print("📋 COMPLETE TRAINING SUMMARY")
    print("=" * 60)

    print(f"\n  🎯 Elective Recommender:")
    print(f"     Model:    RandomForest(200) + KNN(5)")
    print(f"     Accuracy: {elective_metrics['accuracy']:.4f}")
    print(f"     F1w:      {elective_metrics['f1_weighted']:.4f}")

    if "performance" in pw_results:
        r = pw_results["performance"]
        print(f"\n  📈 Performance Predictor:")
        print(f"     Model: {r['best_model']}")
        print(f"     RMSE:  {r['best_rmse']:.4f}")

    if "weakness" in pw_results:
        r = pw_results["weakness"]
        print(f"\n  🔍 Weakness Detector:")
        print(f"     Model:        {r['severity_best_model']}")
        print(f"     Severity F1w: {r['severity_best_f1_weighted']:.4f}")
        print(f"     Interv. F1:   {r['intervention_f1']:.4f}")

    # Update meta.json
    meta_path = os.path.join(SAVE_DIR, "meta.json")
    meta = {}
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            meta = json.load(f)

    meta.update({
        "elective_recommender_trained": True,
        "elective_accuracy": elective_metrics.get("accuracy"),
        "performance_predictor_trained": "performance" in pw_results,
        "performance_model": pw_results.get("performance", {}).get("best_model"),
        "weakness_detector_trained": "weakness" in pw_results,
        "weakness_model": pw_results.get("weakness", {}).get("severity_best_model"),
        "all_models_trained": datetime.utcnow().isoformat() if "datetime" in dir() else "now",
    })
    from datetime import datetime
    meta["all_models_trained"] = datetime.utcnow().isoformat()

    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    print(f"\n  📁 All models saved to: {SAVE_DIR}/")
    print("=" * 60)
    
    # List saved files
    print("\n  Saved model files:")
    for fname in sorted(os.listdir(SAVE_DIR)):
        fpath = os.path.join(SAVE_DIR, fname)
        size_kb = os.path.getsize(fpath) / 1024
        print(f"    {fname:<45} {size_kb:>8.1f} KB")
    print()

    # ═══════════════════════════════════════════════════════════
    # SAVE COMPREHENSIVE TRAINING + TESTING REPORT
    # ═══════════════════════════════════════════════════════════
    
    import csv
    from datetime import datetime

    report_dir = os.path.join(DATA_DIR, "reports")
    os.makedirs(report_dir, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    # ── 1. Save combined JSON report ──
    combined_report = {
        "training_timestamp": datetime.utcnow().isoformat(),
        "elective_recommender": {
            "model": "RandomForest(200) + KNN(5)",
            "metrics": elective_metrics,
        },
    }
    if "performance" in pw_results:
        combined_report["performance_predictor"] = pw_results["performance"]
    if "weakness" in pw_results:
        combined_report["weakness_detector"] = pw_results["weakness"]

    combined_path = os.path.join(report_dir, f"training_report_{timestamp}.json")
    with open(combined_path, "w") as f:
        json.dump(combined_report, f, indent=2, default=str)
    print(f"\n  📄 Combined report: {combined_path}")

    # ── 2. Save model comparison CSV (easy to show teacher) ──
    csv_path = os.path.join(report_dir, f"model_comparison_{timestamp}.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Task", "Model", "Primary Metric", "Value",
            "Secondary Metric", "Value", "CV Score", "Train Time (s)"
        ])

        # Elective
        writer.writerow([
            "Elective Recommender", "RandomForest(200)+KNN(5)",
            "Accuracy", f"{elective_metrics['accuracy']:.4f}",
            "F1 Weighted", f"{elective_metrics['f1_weighted']:.4f}",
            f"{elective_metrics['cross_val_mean']:.4f}±{elective_metrics['cross_val_std']:.4f}",
            "-",
        ])

        # Performance predictor — all candidates
        if "performance" in pw_results:
            pr = pw_results["performance"]
            for model_name, model_metrics in pr.get("all_results", {}).items():
                is_best = "✅" if model_name == pr["best_model"] else ""
                writer.writerow([
                    f"Perf. Predictor {is_best}", model_name,
                    "RMSE", f"{model_metrics['rmse']:.4f}",
                    "R²", f"{model_metrics['r2']:.4f}",
                    f"{model_metrics['cv_rmse']:.4f}±{model_metrics['cv_std']:.4f}",
                    f"{model_metrics['train_time_s']:.2f}",
                ])

        # Weakness detector — all candidates
        if "weakness" in pw_results:
            wr = pw_results["weakness"]
            for model_name, model_metrics in wr.get("severity_results", {}).items():
                is_best = "✅" if model_name == wr["severity_best_model"] else ""
                writer.writerow([
                    f"Weakness Detector {is_best}", model_name,
                    "F1 Weighted", f"{model_metrics['f1_weighted']:.4f}",
                    "Accuracy", f"{model_metrics['accuracy']:.4f}",
                    f"{model_metrics['cv_f1_mean']:.4f}±{model_metrics['cv_f1_std']:.4f}",
                    f"{model_metrics['train_time_s']:.2f}",
                ])

    print(f"  📊 Comparison CSV: {csv_path}")

    # ── 3. Save per-class metrics for weakness ──
    if "weakness" in pw_results and "severity_per_class" in pw_results["weakness"]:
        per_class_path = os.path.join(report_dir, f"weakness_per_class_{timestamp}.csv")
        with open(per_class_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Severity", "Precision", "Recall", "F1-Score", "Support"])
            for cls_name, metrics in pw_results["weakness"]["severity_per_class"].items():
                writer.writerow([
                    cls_name,
                    f"{metrics['precision']:.4f}",
                    f"{metrics['recall']:.4f}",
                    f"{metrics['f1-score']:.4f}",
                    metrics.get("support", "-"),
                ])
        print(f"  📋 Per-class report: {per_class_path}")

    # ── 4. Save confusion matrices as readable text ──
    cm_path = os.path.join(report_dir, f"confusion_matrices_{timestamp}.txt")
    with open(cm_path, "w") as f:
        f.write("CONFUSION MATRICES — Training Results\n")
        f.write(f"Generated: {datetime.utcnow().isoformat()}\n")
        f.write("=" * 60 + "\n\n")

        if "confusion_matrix" in elective_metrics:
            labels = sorted(elective_metrics.get("per_class", {}).keys())
            if not labels:
                labels = ["CCS", "DWM", "ML", "WT"]
            cm = elective_metrics["confusion_matrix"]
            f.write("ELECTIVE RECOMMENDER\n")
            f.write(f"{'':>12} " + " ".join(f"{l:>6}" for l in labels) + "\n")
            for i, row in enumerate(cm):
                f.write(f"{labels[i]:>12} " + " ".join(f"{v:>6}" for v in row) + "\n")
            f.write("\n")

        if "weakness" in pw_results and "severity_confusion_matrix" in pw_results["weakness"]:
            sev_labels = ["none", "low", "medium", "high", "critical"]
            cm = pw_results["weakness"]["severity_confusion_matrix"]
            f.write("WEAKNESS DETECTOR (Severity)\n")
            f.write(f"{'':>12} " + " ".join(f"{l:>8}" for l in sev_labels) + "\n")
            for i, row in enumerate(cm):
                f.write(f"{sev_labels[i]:>12} " + " ".join(f"{v:>8}" for v in row) + "\n")

    print(f"  📊 Confusion matrices: {cm_path}")
    print(f"\n  📁 All reports in: {report_dir}/")

if __name__ == "__main__":
    asyncio.run(main())