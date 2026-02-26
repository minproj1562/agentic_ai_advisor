# academic-advisor/academic-advisor-backend/app/ml/utils/training.py
"""
Training utilities for the recommendation model
Realistic synthetic data based on FCRIT IT curriculum
Real feedback-based retraining pipeline
"""

import numpy as np
import random
import logging
from typing import List, Dict, Any
from datetime import datetime
from app.models.recommendation import RecommendationType
from app.ml.models.recommendation_engine import (
    recommendation_engine,
    ALL_SUBJECTS,
    INTEREST_AREAS,
    SUBJECT_WEIGHTS,
    INTEREST_ELECTIVE_MAP,
    PROJECT_SKILL_MAP,
    CANONICAL_SUBJECTS,
)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════
#  REALISTIC FCRIT CURRICULUM-BASED SYNTHETIC DATA
# ═══════════════════════════════════════════════════════════════════

# Realistic mark distributions per student archetype
STUDENT_ARCHETYPES = {
    'ML': {
        'description': 'AI/ML enthusiast - strong in math and Python',
        'strong_subjects': {
            'Python': (78, 95),
            'Engineering Mathematics-III': (70, 90),
            'Engineering Mathematics-IV': (65, 88),
            'Data Structures and Algorithms': (72, 92),
            'Artificial Intelligence': (80, 98),
            'Database Management Systems': (65, 85),
            'Java': (60, 80),
        },
        'weak_subjects': {
            'Microcontroller & Embedded Systems': (40, 65),
            'Digital Logic & Design': (45, 65),
            'IoT': (40, 60),
        },
        'neutral_subjects': {
            'Operating Systems': (55, 75),
            'Computer Networks': (50, 70),
            'Software Engineering': (55, 75),
            'Automata Theory': (55, 78),
            'Design & Analysis of Algorithms': (60, 82),
            'Cryptography & Network Security': (50, 70),
            'C++': (55, 75),
            'Full Stack Development': (50, 75),
        },
        'interests': [
            'Artificial Intelligence & Machine Learning',
            'Data Science & Analytics',
        ],
        'optional_interests': [
            'Web Development',
            'Cloud & Distributed Systems',
        ],
        'project_keywords': [
            'python', 'tensorflow', 'pytorch', 'machine learning',
            'deep learning', 'nlp', 'data science', 'sklearn',
            'neural network', 'pandas', 'numpy', 'classification',
        ],
        'languages': ['Python', 'R'],
        'frameworks': ['TensorFlow', 'PyTorch', 'Scikit-learn', 'Flask'],
    },
    'WT': {
        'description': 'Embedded/IoT enthusiast - strong in hardware and networks',
        'strong_subjects': {
            'Computer Networks': (75, 95),
            'Microcontroller & Embedded Systems': (78, 95),
            'IoT': (80, 98),
            'Digital Logic & Design': (70, 88),
            'Operating Systems': (65, 82),
            'C++': (65, 85),
        },
        'weak_subjects': {
            'Python': (40, 60),
            'Engineering Mathematics-III': (40, 62),
            'Engineering Mathematics-IV': (38, 60),
            'Artificial Intelligence': (40, 60),
        },
        'neutral_subjects': {
            'Data Structures and Algorithms': (55, 75),
            'Database Management Systems': (50, 70),
            'Software Engineering': (50, 70),
            'Java': (50, 70),
            'Automata Theory': (45, 68),
            'Design & Analysis of Algorithms': (50, 72),
            'Cryptography & Network Security': (55, 75),
            'Full Stack Development': (45, 65),
        },
        'interests': [
            'Network & Wireless Systems',
            'Mobile & IoT Development',
        ],
        'optional_interests': [
            'Cloud & Distributed Systems',
        ],
        'project_keywords': [
            'arduino', 'raspberry pi', 'iot', 'embedded', 'sensor',
            'wireless', 'bluetooth', 'mqtt', 'microcontroller',
            'esp32', 'lora', 'rfid',
        ],
        'languages': ['C', 'C++', 'Python'],
        'frameworks': ['Arduino', 'ESP-IDF', 'FreeRTOS'],
    },
    'DWM': {
        'description': 'Data analytics enthusiast - strong in databases and stats',
        'strong_subjects': {
            'Database Management Systems': (78, 95),
            'Data Structures and Algorithms': (70, 88),
            'Python': (68, 85),
            'Engineering Mathematics-IV': (65, 82),
            'Java': (60, 80),
        },
        'weak_subjects': {
            'Microcontroller & Embedded Systems': (40, 60),
            'Digital Logic & Design': (42, 62),
            'IoT': (40, 58),
            'Computer Networks': (45, 65),
        },
        'neutral_subjects': {
            'Engineering Mathematics-III': (55, 75),
            'Operating Systems': (55, 72),
            'Software Engineering': (55, 75),
            'Automata Theory': (50, 70),
            'Design & Analysis of Algorithms': (55, 75),
            'Cryptography & Network Security': (48, 68),
            'C++': (50, 70),
            'Full Stack Development': (50, 70),
            'Artificial Intelligence': (55, 75),
        },
        'interests': [
            'Data Science & Analytics',
            'Artificial Intelligence & Machine Learning',
        ],
        'optional_interests': [
            'Web Development',
        ],
        'project_keywords': [
            'sql', 'mongodb', 'data warehouse', 'etl', 'hadoop',
            'spark', 'data mining', 'analytics', 'tableau',
            'power bi', 'data pipeline', 'pandas',
        ],
        'languages': ['Python', 'SQL', 'R'],
        'frameworks': ['Pandas', 'Apache Spark', 'Tableau'],
    },
    'CCS': {
        'description': 'Cloud/DevOps enthusiast - strong in systems and web',
        'strong_subjects': {
            'Computer Networks': (72, 90),
            'Operating Systems': (75, 92),
            'Full Stack Development': (78, 95),
            'Software Engineering': (70, 88),
            'Database Management Systems': (65, 82),
            'Python': (60, 80),
        },
        'weak_subjects': {
            'Engineering Mathematics-III': (40, 60),
            'Engineering Mathematics-IV': (38, 58),
            'Microcontroller & Embedded Systems': (42, 60),
            'Artificial Intelligence': (42, 62),
        },
        'neutral_subjects': {
            'Data Structures and Algorithms': (58, 78),
            'Digital Logic & Design': (48, 68),
            'Java': (55, 75),
            'Automata Theory': (45, 65),
            'Design & Analysis of Algorithms': (50, 72),
            'Cryptography & Network Security': (55, 75),
            'C++': (50, 70),
            'IoT': (45, 65),
        },
        'interests': [
            'Cloud & Distributed Systems',
            'Web Development',
        ],
        'optional_interests': [
            'Network & Wireless Systems',
            'Data Science & Analytics',
        ],
        'project_keywords': [
            'aws', 'azure', 'docker', 'kubernetes', 'cloud',
            'devops', 'terraform', 'serverless', 'microservices',
            'ci/cd', 'react', 'node', 'rest api', 'fullstack',
        ],
        'languages': ['JavaScript', 'Python', 'Go'],
        'frameworks': ['React', 'Node.js', 'Docker', 'Kubernetes'],
    },
}


def _random_mark(low: int, high: int) -> float:
    """Generate a realistic mark with slight gaussian noise."""
    mean = (low + high) / 2
    std = (high - low) / 4
    mark = random.gauss(mean, std)
    return round(max(20, min(100, mark)), 1)


def generate_synthetic_sample(label: str, noise_level: float = 0.3) -> Dict[str, Any]:
    """Generate a realistic synthetic training sample for FCRIT IT curriculum."""
    archetype = STUDENT_ARCHETYPES[label]
    marks = {}
    interests = []
    projects = []

    # Generate marks based on archetype with realistic distributions
    for subj, (low, high) in archetype['strong_subjects'].items():
        marks[subj] = _random_mark(low, high)

    for subj, (low, high) in archetype['weak_subjects'].items():
        marks[subj] = _random_mark(low, high)

    for subj, (low, high) in archetype['neutral_subjects'].items():
        marks[subj] = _random_mark(low, high)

    # Add noise: sometimes strong students are weak in their area (makes it realistic)
    if random.random() < noise_level:
        # Randomly weaken one strong subject
        strong_subjs = list(archetype['strong_subjects'].keys())
        if strong_subjs:
            weak_target = random.choice(strong_subjs)
            marks[weak_target] = _random_mark(40, 60)

    # Add noise: sometimes students have unexpected strengths
    if random.random() < noise_level * 0.5:
        weak_subjs = list(archetype['weak_subjects'].keys())
        if weak_subjs:
            strong_target = random.choice(weak_subjs)
            marks[strong_target] = _random_mark(65, 85)

    # Generate interests
    interests = list(archetype['interests'])
    for opt_interest in archetype['optional_interests']:
        if random.random() < 0.4:
            interests.append(opt_interest)

    # Add random unrelated interest sometimes (noise)
    if random.random() < noise_level * 0.3:
        all_interests = list(INTEREST_AREAS)
        remaining = [i for i in all_interests if i not in interests]
        if remaining:
            interests.append(random.choice(remaining))

    # Generate realistic projects
    n_projects = random.choices([1, 2, 3, 4, 5], weights=[15, 30, 30, 15, 10])[0]
    keywords = archetype['project_keywords']
    languages = archetype['languages']
    frameworks = archetype['frameworks']

    project_templates = [
        '{lang} based {domain} application',
        '{domain} system using {framework}',
        'Automated {domain} tool',
        '{domain} analysis and visualization',
        'Real-time {domain} monitoring system',
    ]

    for i in range(n_projects):
        proj_keywords = random.sample(keywords, min(random.randint(2, 5), len(keywords)))
        proj_lang = random.sample(languages, min(2, len(languages)))
        proj_framework = random.sample(frameworks, min(2, len(frameworks)))

        title_template = random.choice(project_templates)
        title = title_template.format(
            lang=proj_lang[0] if proj_lang else 'Python',
            domain=proj_keywords[0] if proj_keywords else 'software',
            framework=proj_framework[0] if proj_framework else 'custom tools',
        )

        projects.append({
            'title': title.title(),
            'description': f'A project involving {", ".join(proj_keywords[:3])}. '
                          f'Built using {", ".join(proj_lang)}.',
            'programming_languages': proj_lang,
            'frameworks': proj_framework,
            'tools': [],
            'technologies': proj_keywords[:4],
            'extracted_skills': proj_keywords + proj_lang,
            'is_team_project': random.random() > 0.4,
            'complexity_score': round(random.uniform(0.3, 0.95), 2),
            'github_url': f'https://github.com/student/project-{i+1}' if random.random() > 0.3 else None,
            'demo_url': f'https://demo.example.com/{i+1}' if random.random() > 0.7 else None,
        })

    return {
        'marks': marks,
        'interests': interests,
        'projects': projects,
        'label': label,
        'source': 'synthetic',
    }


def generate_training_dataset(n_samples_per_class: int = 150) -> List[Dict[str, Any]]:
    """Generate balanced synthetic training dataset with FCRIT curriculum."""
    dataset = []
    labels = ['ML', 'WT', 'DWM', 'CCS']

    for label in labels:
        for i in range(n_samples_per_class):
            # Vary noise level to create diverse samples
            noise = random.uniform(0.1, 0.5)
            sample = generate_synthetic_sample(label, noise_level=noise)
            dataset.append(sample)

    random.shuffle(dataset)
    logger.info(f"Generated {len(dataset)} synthetic training samples ({n_samples_per_class} per class)")
    return dataset


async def collect_feedback_training_data() -> List[Dict[str, Any]]:
    """
    Collect training data from REAL user feedback.
    Uses the full student context stored with each feedback record.
    """
    training_data = []

    try:
        from app.models.recommendation import RecommendationFeedback

        # Positive feedback (rating >= 4) = student agrees this elective fits them
        positive_feedback = await RecommendationFeedback.find(
            RecommendationFeedback.rating >= 4,
            RecommendationFeedback.recommendation_type == RecommendationType.ELECTIVE,
        ).to_list()

        # Negative feedback (rating <= 2) = student disagrees
        negative_feedback = await RecommendationFeedback.find(
            RecommendationFeedback.rating <= 2,
            RecommendationFeedback.recommendation_type == RecommendationType.ELECTIVE,
        ).to_list()

        # Map recommendation_id back to label
        label_map = {
            'ITPEC5012': 'ML', 'Machine Learning': 'ML', 'ML': 'ML',
            'ITPEC5013': 'WT', 'Wireless Technology': 'WT', 'WT': 'WT',
            'ITPEC5014': 'DWM', 'Data Warehouse and Mining': 'DWM', 'DWM': 'DWM',
            'ITPEC5015': 'CCS', 'Cloud Computing Services': 'CCS', 'CCS': 'CCS',
        }

        for fb in positive_feedback:
            label = label_map.get(fb.recommendation_id) or label_map.get(fb.item_name)
            if not label:
                continue

            # Use REAL student data stored in feedback
            if fb.student_marks and len(fb.student_marks) > 0:
                # Build projects from skills
                project_skills = fb.student_project_skills or []
                fake_projects = []
                if project_skills:
                    fake_projects.append({
                        'title': 'Student Project',
                        'description': ' '.join(project_skills[:5]),
                        'programming_languages': [s for s in project_skills if s in ['Python', 'Java', 'JavaScript', 'C++', 'C', 'Go', 'R']],
                        'frameworks': [s for s in project_skills if s.lower() not in ['python', 'java', 'javascript']],
                        'tools': [],
                        'technologies': project_skills[:6],
                        'extracted_skills': project_skills,
                        'is_team_project': False,
                        'complexity_score': 0.6,
                        'github_url': None,
                        'demo_url': None,
                    })

                training_data.append({
                    'marks': fb.student_marks,
                    'interests': fb.student_interests or [],
                    'projects': fake_projects,
                    'label': label,
                    'source': 'feedback_positive',
                })

        # Negative feedback: create training samples for OTHER labels
        for fb in negative_feedback:
            rejected_label = label_map.get(fb.recommendation_id) or label_map.get(fb.item_name)
            if not rejected_label or not fb.student_marks:
                continue

            # The student rejected this label, so assign to other labels
            other_labels = [l for l in ['ML', 'WT', 'DWM', 'CCS'] if l != rejected_label]
            if other_labels and len(fb.student_marks) > 0:
                # Pick the most likely alternative (we don't know for sure, so pick randomly)
                alt_label = random.choice(other_labels)
                project_skills = fb.student_project_skills or []
                fake_projects = []
                if project_skills:
                    fake_projects.append({
                        'title': 'Student Project',
                        'description': ' '.join(project_skills[:5]),
                        'programming_languages': [],
                        'frameworks': [],
                        'tools': [],
                        'technologies': project_skills[:4],
                        'extracted_skills': project_skills,
                        'is_team_project': False,
                        'complexity_score': 0.5,
                        'github_url': None,
                        'demo_url': None,
                    })

                training_data.append({
                    'marks': fb.student_marks,
                    'interests': fb.student_interests or [],
                    'projects': fake_projects,
                    'label': alt_label,
                    'source': 'feedback_negative',
                })

        logger.info(f"Collected {len(training_data)} real samples from feedback "
                    f"(positive: {len(positive_feedback)}, negative: {len(negative_feedback)})")

    except Exception as e:
        logger.error(f"Error collecting feedback data: {e}", exc_info=True)

    return training_data


async def train_recommendation_model(
    n_synthetic: int = 1250,
    include_feedback: bool = True,
    test_size: float = 0.2,
) -> Dict[str, Any]:
    """
    Main training pipeline.
    Combines realistic synthetic data with real user feedback.
    
    Args:
        n_synthetic: Number of samples per class (total = n_synthetic × 4)
        include_feedback: Whether to include MongoDB feedback data  
        test_size: Proportion of data for testing (default 0.2 = 20%)
        
    Returns:
        Dictionary containing training metrics
    """
    logger.info("=" * 60)
    logger.info("Starting model training pipeline...")
    logger.info(f"  Samples per class: {n_synthetic}")
    logger.info(f"  Total synthetic: {n_synthetic * 4}")
    logger.info(f"  Test size: {test_size * 100:.0f}%")
    logger.info("=" * 60)

    # 1. Generate synthetic data
    synthetic_data = generate_training_dataset(n_synthetic)

    # 2. Collect feedback data
    feedback_data = []
    if include_feedback:
        try:
            feedback_data = await collect_feedback_training_data()
        except Exception as e:
            logger.warning(f"Could not collect feedback data (DB may not be connected): {e}")

    # 3. Combine datasets (feedback data is weighted more heavily)
    weighted_feedback = feedback_data * 3 if feedback_data else []
    training_data = synthetic_data + weighted_feedback

    logger.info(f"Total training samples: {len(training_data)} "
               f"(synthetic: {len(synthetic_data)}, feedback: {len(feedback_data)}, "
               f"weighted feedback: {len(weighted_feedback)})")

    # 4. Train the model
    try:
        metrics = recommendation_engine.train(training_data, test_size=test_size)
        
        logger.info(f"Training completed successfully!")
        logger.info(f"  Accuracy: {metrics['accuracy']:.4f}")
        logger.info(f"  F1 (weighted): {metrics['f1_weighted']:.4f}")
        logger.info(f"  Cross-val: {metrics['cross_val_mean']:.4f} ± {metrics['cross_val_std']:.4f}")

        # 5. Store training data points for reference
        try:
            from app.models.recommendation import TrainingDataPoint

            store_count = min(50, len(training_data))
            for sample in random.sample(training_data, store_count):
                data_point = TrainingDataPoint(
                    student_features=recommendation_engine.extract_features(
                        sample['marks'],
                        sample['interests'],
                        sample['projects'],
                    ).tolist(),
                    marks=sample['marks'],
                    interests={i: 1.0 for i in sample['interests']} if isinstance(sample['interests'], list) else sample['interests'],
                    project_skills=[s for p in sample['projects'] for s in p.get('extracted_skills', [])],
                    label=sample['label'],
                    source=sample.get('source', 'synthetic'),
                )
                await data_point.insert()
        except Exception as e:
            logger.warning(f"Failed to store training data points: {e}")

        return metrics

    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)
        raise


async def evaluate_model_accuracy() -> Dict[str, Any]:
    """Evaluate model on held-out test data."""
    if not recommendation_engine.is_trained:
        return {"error": "Model not trained", "accuracy": 0}

    # Generate test data (different seed/noise than training)
    test_data = generate_training_dataset(n_samples_per_class=25)

    correct = 0
    total = 0
    per_class = {label: {'correct': 0, 'total': 0} for label in ['ML', 'WT', 'DWM', 'CCS']}

    code_to_label = {
        'ITPEC5012': 'ML',
        'ITPEC5013': 'WT',
        'ITPEC5014': 'DWM',
        'ITPEC5015': 'CCS',
    }

    for sample in test_data:
        true_label = sample['label']

        recommendations = recommendation_engine.recommend_electives(
            marks=sample['marks'],
            interests=sample['interests'],
            projects=sample['projects'],
            use_ml=True,
        )

        if recommendations:
            pred_code = recommendations[0]['elective_code']
            pred_label = code_to_label.get(pred_code, '')

            if pred_label == true_label:
                correct += 1
                per_class[true_label]['correct'] += 1

        total += 1
        per_class[true_label]['total'] += 1

    accuracy = correct / total if total > 0 else 0

    return {
        "accuracy": round(accuracy, 4),
        "total_samples": total,
        "correct_predictions": correct,
        "per_class_accuracy": {
            label: round(stats['correct'] / max(stats['total'], 1), 4)
            for label, stats in per_class.items()
        },
        "timestamp": datetime.utcnow().isoformat(),
    }