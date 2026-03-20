# academic-advisor-backend/scripts/compare_models.py
"""
Run comprehensive model comparison.

Usage:
    python -m scripts.compare_models
    python -m scripts.compare_models --samples 500
    python -m scripts.compare_models --samples 1000 --hard-mode
"""

import asyncio
import sys
import os
import random
import logging
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description='Compare ML models for recommendation engine')
    parser.add_argument('--samples', '-n', type=int, default=500,
                        help='Samples per class (default: 500, total = n × 4)')
    parser.add_argument('--test-size', '-t', type=float, default=0.2,
                        help='Test set proportion (default: 0.2)')
    parser.add_argument('--cv-folds', type=int, default=5,
                        help='Cross-validation folds (default: 5)')
    parser.add_argument('--hard-mode', action='store_true',
                        help='Generate harder test cases with more overlap between classes')
    return parser.parse_args()


def generate_hard_samples(n_per_class: int = 100) -> list:
    """
    Generate deliberately HARD samples where student profiles
    overlap between classes. This tests model robustness.
    """
    from app.ml.utils.training import generate_synthetic_sample

    hard_samples = []

    for _ in range(n_per_class):
        # Student good at BOTH Python and Networks → ML or WT?
        sample = generate_synthetic_sample('ML', noise_level=0.6)
        sample['marks']['Computer Networks'] = random.uniform(75, 95)
        sample['marks']['Microcontroller & Embedded Systems'] = random.uniform(65, 85)
        hard_samples.append(sample)

        # Student good at BOTH databases and cloud → DWM or CCS?
        sample = generate_synthetic_sample('DWM', noise_level=0.6)
        sample['marks']['Full Stack Development'] = random.uniform(70, 90)
        sample['marks']['Operating Systems'] = random.uniform(70, 85)
        sample['interests'].append('Cloud & Distributed Systems')
        hard_samples.append(sample)

        # Student with mixed interests
        sample = generate_synthetic_sample('CCS', noise_level=0.6)
        sample['interests'] = ['Artificial Intelligence & Machine Learning', 'Cloud & Distributed Systems']
        sample['marks']['Python'] = random.uniform(75, 90)
        sample['marks']['Artificial Intelligence'] = random.uniform(65, 80)
        hard_samples.append(sample)

        # Student with all neutral marks (no clear preference)
        sample = generate_synthetic_sample(
            random.choice(['ML', 'WT', 'DWM', 'CCS']),
            noise_level=0.8,
        )
        for subj in sample['marks']:
            sample['marks'][subj] = random.uniform(55, 75)
        hard_samples.append(sample)

    random.shuffle(hard_samples)
    return hard_samples


async def main():
    args = parse_args()

    logger.info("=" * 80)
    logger.info("🔬 ACADEMIC ADVISOR — COMPREHENSIVE MODEL COMPARISON")
    logger.info("=" * 80)
    logger.info(f"  Samples per class: {args.samples}")
    logger.info(f"  Total samples: {args.samples * 4}")
    logger.info(f"  Test size: {args.test_size * 100:.0f}%")
    logger.info(f"  CV folds: {args.cv_folds}")
    logger.info(f"  Hard mode: {args.hard_mode}")
    logger.info("")

    from app.ml.utils.training import generate_training_dataset
    from app.ml.models.recommendation_engine import recommendation_engine
    from app.ml.utils.model_comparison import run_model_comparison

    logger.info("📦 Generating training data...")
    training_data = generate_training_dataset(n_samples_per_class=args.samples)

    if args.hard_mode:
        logger.info("🔥 Adding hard/overlapping samples...")
        hard_data = generate_hard_samples(n_per_class=args.samples // 5)
        training_data.extend(hard_data)
        logger.info(f"   Added {len(hard_data)} hard samples")
        logger.info(f"   Total: {len(training_data)} samples")

    save_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'app', 'ml', 'models', 'saved',
    )

    report = run_model_comparison(
        training_data=training_data,
        feature_extractor=recommendation_engine.extract_features,
        test_size=args.test_size,
        n_cv_folds=args.cv_folds,
        save_dir=save_dir,
    )

    best = report.get('best_model', {})
    rec = report.get('recommendation', {})

    logger.info("\n" + "=" * 80)
    logger.info("✅ COMPARISON COMPLETE")
    logger.info("=" * 80)
    logger.info(f"\n  🏆 Recommended Model: {rec.get('recommended_model', 'N/A')}")
    logger.info(f"  📊 Composite Score: {rec.get('composite_score', 0):.4f}")

    for reason in rec.get('reasons', []):
        logger.info(f"     • {reason}")

    if rec.get('runner_up'):
        logger.info(f"\n  🥈 Runner-up: {rec['runner_up']}")

    logger.info(f"\n  📁 Full report saved to: {save_dir}/model_comparison_report.json")
    logger.info("")
    logger.info("─" * 80)
    logger.info(f"To train your engine with the best model, run:")
    logger.info(f"  python -m scripts.train_models --samples {args.samples}")
    logger.info("─" * 80)


if __name__ == "__main__":
    asyncio.run(main())