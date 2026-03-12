# scripts/train_models.py
"""
Enhanced Training Script with model comparison and selection.

Usage:
    python -m scripts.train_models                           # Default training
    python -m scripts.train_models --samples 1000            # More data
    python -m scripts.train_models --compare                 # Run comparison first
    python -m scripts.train_models --compare --hard-mode     # With hard samples
    python -m scripts.train_models --model XGBoost           # Use specific model
"""

import asyncio
import sys
import os
import logging
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description='Train recommendation models')
    parser.add_argument('--samples', '-n', type=int, default=1250,
                        help='Samples per class (default: 1250)')
    parser.add_argument('--test-size', '-t', type=float, default=0.2,
                        help='Test set proportion (default: 0.2)')
    parser.add_argument('--no-feedback', action='store_true',
                        help='Skip loading feedback from MongoDB')
    parser.add_argument('--compare', action='store_true',
                        help='Run full model comparison before training')
    parser.add_argument('--hard-mode', action='store_true',
                        help='Include hard/overlapping samples for robust evaluation')
    parser.add_argument('--model', type=str, default=None,
                        help='Specific model to use (e.g., XGBoost, RandomForest)')
    parser.add_argument('--export-data', action='store_true',
                        help='Export training data to JSON')
    return parser.parse_args()


async def main():
    args = parse_args()

    total_samples = args.samples * 4
    
    logger.info("=" * 70)
    logger.info("🎓 Academic Advisor — Model Training Pipeline")
    logger.info("=" * 70)
    logger.info(f"  Samples per class: {args.samples}")
    logger.info(f"  Total samples: {total_samples}")
    logger.info(f"  Test size: {args.test_size * 100:.0f}%")
    logger.info(f"  Compare models: {args.compare}")
    logger.info(f"  Hard mode: {args.hard_mode}")
    if args.model:
        logger.info(f"  Requested model: {args.model}")
    logger.info("")

    # ── Step 0: Model Comparison (optional) ──
    if args.compare:
        logger.info("🔬 Running model comparison first...")
        from app.ml.utils.training import generate_training_dataset
        from app.ml.models.recommendation_engine import recommendation_engine
        from app.ml.utils.model_comparison import run_model_comparison

        comparison_data = generate_training_dataset(n_samples_per_class=min(args.samples, 500))
        
        if args.hard_mode:
            from scripts.compare_models import generate_hard_samples
            hard = generate_hard_samples(n_per_class=100)
            comparison_data.extend(hard)

        save_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'app', 'ml', 'models', 'saved',
        )

        report = run_model_comparison(
            training_data=comparison_data,
            feature_extractor=recommendation_engine.extract_features,
            test_size=args.test_size,
            save_dir=save_dir,
        )
        
        best_model_name = report.get('recommendation', {}).get('recommended_model', 'RandomForest')
        logger.info(f"\n🏆 Best model from comparison: {best_model_name}")
        logger.info("Now training with full dataset...\n")

    # ── Step 1: Connect to MongoDB (optional) ──
    db_connected = False
    if not args.no_feedback:
        try:
            from app.config import settings
            from beanie import init_beanie
            from motor.motor_asyncio import AsyncIOMotorClient
            from app.models.recommendation import RecommendationFeedback, TrainingDataPoint

            client = AsyncIOMotorClient(settings.MONGODB_URL)
            await init_beanie(
                database=client[settings.MONGODB_DATABASE],
                document_models=[RecommendationFeedback, TrainingDataPoint],
            )
            db_connected = True
            feedback_count = await RecommendationFeedback.count()
            logger.info(f"✅ MongoDB connected ({feedback_count} feedback records)")
        except Exception as e:
            logger.warning(f"⚠️ MongoDB not available: {e}")

    # ── Step 2: Train ──
    from app.ml.utils.training import (
        train_recommendation_model,
        evaluate_model_accuracy,
    )

    logger.info("🚀 Starting training...")
    metrics = await train_recommendation_model(
        n_synthetic=args.samples,
        include_feedback=db_connected,
        test_size=args.test_size,
    )

    # ── Step 3: Display Results ──
    logger.info("\n" + "=" * 70)
    logger.info("📈 TRAINING RESULTS")
    logger.info("=" * 70)
    logger.info(f"")
    logger.info(f"  📊 Overall Metrics:")
    logger.info(f"     Accuracy:       {metrics['accuracy']:.4f} ({metrics['accuracy']*100:.2f}%)")
    logger.info(f"     F1 (weighted):  {metrics['f1_weighted']:.4f}")
    logger.info(f"     F1 (macro):     {metrics['f1_macro']:.4f}")
    logger.info(f"     Cross-val:      {metrics['cross_val_mean']:.4f} ± {metrics['cross_val_std']:.4f}")
    logger.info(f"")
    logger.info(f"  📦 Dataset Split:")
    logger.info(f"     Train samples:  {metrics['n_training_samples']}")
    logger.info(f"     Test samples:   {metrics['n_test_samples']}")

    if 'per_class' in metrics:
        logger.info(f"\n  🎯 Per-Class Performance:")
        logger.info(f"     {'Class':<6} {'Precision':>10} {'Recall':>10} {'F1-Score':>10}")
        logger.info(f"     {'-'*6} {'-'*10} {'-'*10} {'-'*10}")
        for cls, m in metrics['per_class'].items():
            logger.info(f"     {cls:<6} {m['precision']:>10.4f} {m['recall']:>10.4f} {m['f1']:>10.4f}")

    if 'confusion_matrix' in metrics:
        logger.info(f"\n  📊 Confusion Matrix:")
        labels = ['ML', 'WT', 'DWM', 'CCS']
        cm = metrics['confusion_matrix']
        logger.info(f"     {'':>6} " + " ".join(f"{l:>6}" for l in labels))
        for i, row in enumerate(cm):
            logger.info(f"     {labels[i]:>6} " + " ".join(f"{v:>6}" for v in row))

    # ── Step 4: Evaluation ──
    logger.info(f"\n{'─' * 70}")
    logger.info("🧪 Running evaluation on fresh held-out test set...")
    eval_results = await evaluate_model_accuracy()
    
    logger.info(f"  Overall accuracy: {eval_results.get('accuracy', 0):.4f}")
    
    if 'per_class_accuracy' in eval_results:
        logger.info(f"\n  Per-Class Accuracy:")
        for cls, acc in eval_results['per_class_accuracy'].items():
            bar = '█' * int(acc * 20)
            logger.info(f"     {cls}: {bar} {acc:.4f}")

    logger.info(f"\n{'=' * 70}")
    logger.info("✅ Training complete!")
    logger.info(f"   Models saved to: app/ml/models/saved/")
    logger.info("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())