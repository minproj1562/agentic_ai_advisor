# academic-advisor/academic-advisor-backend/scripts/train_models.py
"""
Enhanced Training Script with configurable dataset size
Run: python -m scripts.train_models
     python -m scripts.train_models --samples 2000
     python -m scripts.train_models --samples 2000 --test-size 0.2
"""

import asyncio
import sys
import os
import logging
import argparse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description='Train recommendation models')
    parser.add_argument(
        '--samples', '-n',
        type=int,
        default=1250,
        help='Number of samples PER CLASS (default: 1250, total = samples × 4)'
    )
    parser.add_argument(
        '--test-size', '-t',
        type=float,
        default=0.2,
        help='Test set proportion (default: 0.2 = 20%%)'
    )
    parser.add_argument(
        '--no-feedback',
        action='store_true',
        help='Skip loading feedback data from MongoDB'
    )
    parser.add_argument(
        '--export-data',
        action='store_true',
        help='Export generated training data to JSON file'
    )
    return parser.parse_args()


async def main():
    args = parse_args()
    
    total_samples = args.samples * 4  # 4 classes
    test_samples = int(total_samples * args.test_size)
    train_samples = total_samples - test_samples
    
    logger.info("=" * 70)
    logger.info("Academic Advisor - Enhanced Model Training Script")
    logger.info("=" * 70)
    logger.info(f"")
    logger.info(f"📊 CONFIGURATION:")
    logger.info(f"   Samples per class: {args.samples}")
    logger.info(f"   Total samples:     {total_samples}")
    logger.info(f"   Training set:      {train_samples} ({(1-args.test_size)*100:.0f}%)")
    logger.info(f"   Test set:          {test_samples} ({args.test_size*100:.0f}%)")
    logger.info(f"")

    # Try to connect to DB for feedback data (optional)
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
            
            # Count existing feedback
            feedback_count = await RecommendationFeedback.count()
            logger.info(f"✅ Connected to MongoDB")
            logger.info(f"   Existing feedback records: {feedback_count}")
        except Exception as e:
            logger.warning(f"⚠️ Could not connect to MongoDB: {e}")
            logger.info("   Training with synthetic data only...")
    else:
        logger.info("⏭️ Skipping MongoDB (--no-feedback flag)")

    # Import training functions
    from app.ml.utils.training import (
        train_recommendation_model,
        evaluate_model_accuracy,
        generate_training_dataset
    )

    # Optionally export the generated data
    if args.export_data:
        import json
        logger.info(f"\n📁 Exporting training data...")
        dataset = generate_training_dataset(n_samples_per_class=args.samples)
        
        export_path = os.path.join(
            os.path.dirname(__file__),
            f"training_data_{total_samples}_samples.json"
        )
        with open(export_path, 'w') as f:
            json.dump(dataset, f, indent=2)
        logger.info(f"   Exported to: {export_path}")

    # Train the model
    logger.info(f"\n🚀 Starting training...")
    metrics = await train_recommendation_model(
        n_synthetic=args.samples,
        include_feedback=db_connected,
        test_size=args.test_size,
    )

    # Display results
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
    logger.info(f"")

    if 'per_class' in metrics:
        logger.info(f"  🎯 Per-Class Performance:")
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

    # Evaluate on held-out test set
    logger.info("\n" + "─" * 70)
    logger.info("🧪 Running evaluation on held-out test set...")
    eval_results = await evaluate_model_accuracy()
    
    logger.info(f"\n  📊 Evaluation Results:")
    logger.info(f"     Overall accuracy: {eval_results.get('accuracy', 0):.4f} ({eval_results.get('accuracy', 0)*100:.2f}%)")
    
    if 'per_class_accuracy' in eval_results:
        logger.info(f"\n  🎯 Per-Class Accuracy:")
        for cls, acc in eval_results['per_class_accuracy'].items():
            bar = '█' * int(acc * 20)
            logger.info(f"     {cls}: {bar} {acc:.4f}")

    logger.info("\n" + "=" * 70)
    logger.info("✅ Training complete!")
    logger.info(f"   Models saved to: app/ml/models/saved/")
    logger.info("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())