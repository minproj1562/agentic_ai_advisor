# Saved ML Models - Academic Advisor

## Overview

This directory contains trained machine learning models for the **Elective Recommendation System**.
The models predict which elective (ML, WT, DWM, CCS) best matches a student's profile based on
their academic performance, declared interests, and project portfolio.

## Model Files

| File | Description | Size |
|------|-------------|------|
| `rf_clf.joblib` | RandomForest Classifier (200 trees, depth 12) | ~2-5 MB |
| `knn_clf.joblib` | K-Nearest Neighbors Classifier (k=5) | ~1-2 MB |
| `scaler.joblib` | StandardScaler for feature normalization | ~5 KB |
| `label_enc.joblib` | LabelEncoder for class labels | ~2 KB |
| `meta.json` | Training metadata and configuration | ~1 KB |

## Labels (Elective Classes)

| Label | Code | Elective Name | Pair |
|-------|------|---------------|------|
| `ML` | ITPEC5012 | Machine Learning | Pair 1 |
| `WT` | ITPEC5013 | Wireless Technology | Pair 1 |
| `DWM` | ITPEC5014 | Data Warehouse & Mining | Pair 2 |
| `CCS` | ITPEC5015 | Cloud Computing Services | Pair 2 |

## Training Data

### Primary: Synthetic Data
- **Source**: `app/ml/utils/training.py` → `STUDENT_ARCHETYPES`
- **Generator**: `generate_training_dataset(n_samples_per_class=150)`
- **Total samples**: 600 (150 per class)

#### Student Archetypes

| Type | Description | Strong Subjects | Weak Subjects |
|------|-------------|-----------------|---------------|
| ML | AI/ML Enthusiast | Python, Math III/IV, AI, DSA | Embedded, IoT |
| WT | Embedded/IoT Enthusiast | Networks, Embedded, IoT | Python, Math |
| DWM | Data Analytics Enthusiast | DBMS, DSA, Python | Embedded, Networks |
| CCS | Cloud/DevOps Enthusiast | Networks, OS, Full Stack | Math, AI |

### Secondary: Real Feedback Data (Optional)
- **Source**: MongoDB `recommendation_feedback` collection
- **Positive feedback** (rating ≥ 4): Confirms the elective recommendation
- **Negative feedback** (rating ≤ 2): Rejects the recommendation
- **Weighting**: Feedback samples weighted 3x vs synthetic

## Feature Engineering

**Total feature dimension: 35**

### Academic Features (18)
```python
CANONICAL_SUBJECTS = [
    "Engineering Mathematics-III", "Engineering Mathematics-IV",
    "Data Structures and Algorithms", "Database Management Systems",
    "Digital Logic & Design", "Operating Systems", "Computer Networks",
    "Microcontroller & Embedded Systems", "Software Engineering",
    "Python", "C++", "Java", "Automata Theory", 
    "Design & Analysis of Algorithms", "Artificial Intelligence", 
    "Cryptography & Network Security", "Full Stack Development", "IoT"
]
# Each normalized to 0-1 range (mark/100)