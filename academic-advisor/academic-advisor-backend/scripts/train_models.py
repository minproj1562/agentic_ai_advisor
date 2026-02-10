# academic-advisor/academic-advisor-backend/scripts/train_models.py
"""
Standalone training script
Run: python -m scripts.train_models
"""

import asyncio
import sys
import os
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def main():
    """Train the recommendation model."""
    logger.info("=" * 60)
    logger.info("Academic Advisor - Model Training Script")
    logger.info("=" * 60)

    # Try to connect to DB for feedback data (optional)
    db_connected = False
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
        logger.info("✅ Connected to MongoDB for feedback data")
    except Exception as e:
        logger.warning(f"⚠️ Could not connect to MongoDB: {e}")
        logger.info("Training with synthetic data only...")

    # Train
    from app.ml.utils.training import train_recommendation_model, evaluate_model_accuracy

    metrics = await train_recommendation_model(
        n_synthetic=200,
        include_feedback=db_connected,
    )

    logger.info("\n" + "=" * 60)
    logger.info("TRAINING RESULTS")
    logger.info("=" * 60)
    logger.info(f"  Accuracy:      {metrics['accuracy']:.4f}")
    logger.info(f"  F1 (weighted): {metrics['f1_weighted']:.4f}")
    logger.info(f"  F1 (macro):    {metrics['f1_macro']:.4f}")
    logger.info(f"  Cross-val:     {metrics['cross_val_mean']:.4f} ± {metrics['cross_val_std']:.4f}")
    logger.info(f"  Train samples: {metrics['n_training_samples']}")
    logger.info(f"  Test samples:  {metrics['n_test_samples']}")

    if 'per_class' in metrics:
        logger.info("\nPer-class metrics:")
        for cls, m in metrics['per_class'].items():
            logger.info(f"  {cls}: P={m['precision']:.3f} R={m['recall']:.3f} F1={m['f1']:.3f}")

    # Evaluate
    logger.info("\nRunning evaluation on held-out test set...")
    eval_results = await evaluate_model_accuracy()
    logger.info(f"  Evaluation accuracy: {eval_results.get('accuracy', 0):.4f}")
    if 'per_class_accuracy' in eval_results:
        for cls, acc in eval_results['per_class_accuracy'].items():
            logger.info(f"  {cls}: {acc:.4f}")

    logger.info("\n✅ Training complete! Model saved to app/ml/models/saved/")


if __name__ == "__main__":
    asyncio.run(main())