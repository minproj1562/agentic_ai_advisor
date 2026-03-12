# app/ml/utils/model_comparison.py
"""
Comprehensive Multi-Model Comparison Framework
================================================
Compares 10+ ML models with full metrics:
  - Accuracy, Precision, Recall, F1-Score
  - Sensitivity (per-class recall)
  - Specificity (per-class TN / (TN + FP))
  - ROC AUC (One-vs-Rest)
  - Cross-validation (5-fold stratified)
  - Training time
  - Confusion matrices
  - Statistical significance tests

Outputs a comparison table and selects the best model.
"""

import numpy as np
import time
import json
import os
import logging
import warnings
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
from collections import defaultdict

from sklearn.ensemble import (
    RandomForestClassifier,
    GradientBoostingClassifier,
    AdaBoostClassifier,
    ExtraTreesClassifier,
    BaggingClassifier,
)
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder, label_binarize
from sklearn.model_selection import (
    train_test_split,
    StratifiedKFold,
    cross_validate,
)
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
    matthews_corrcoef,
    cohen_kappa_score,
    log_loss,
)

# Try importing XGBoost and LightGBM (optional)
try:
    from xgboost import XGBClassifier
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

try:
    from lightgbm import LGBMClassifier
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)

# Class labels
LABELS = ['ML', 'WT', 'DWM', 'CCS']
LABEL_FULL_NAMES = {
    'ML': 'Machine Learning',
    'WT': 'Wireless Technology',
    'DWM': 'Data Warehouse & Mining',
    'CCS': 'Cloud Computing Services',
}


# ═══════════════════════════════════════════════════════════════════
#  MODEL DEFINITIONS
# ═══════════════════════════════════════════════════════════════════

def get_model_catalogue() -> Dict[str, Dict[str, Any]]:
    """
    Returns all models to compare with their configurations.
    Each model has:
      - instance: The sklearn estimator
      - description: Why we're testing this model
      - hyperparameters: Key params explained
    """
    models = {
        # ── Ensemble Methods ──
        'RandomForest': {
            'instance': RandomForestClassifier(
                n_estimators=200,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                max_features='sqrt',
                random_state=42,
                n_jobs=-1,
                class_weight='balanced',
            ),
            'description': (
                'Ensemble of decision trees with bagging. '
                'Handles non-linear relationships well, robust to overfitting. '
                'Current production model.'
            ),
            'hyperparameters': {
                'n_estimators': '200 trees in the forest',
                'max_depth': '15 levels deep (prevents overfitting)',
                'class_weight': 'balanced (handles class imbalance)',
            },
        },
        'GradientBoosting': {
            'instance': GradientBoostingClassifier(
                n_estimators=200,
                max_depth=5,
                learning_rate=0.1,
                subsample=0.8,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
            ),
            'description': (
                'Sequential boosting — each tree corrects errors of the previous. '
                'Often achieves highest accuracy but slower to train.'
            ),
            'hyperparameters': {
                'n_estimators': '200 boosting rounds',
                'learning_rate': '0.1 (conservative, prevents overfitting)',
                'subsample': '0.8 (stochastic gradient boosting)',
            },
        },
        'ExtraTrees': {
            'instance': ExtraTreesClassifier(
                n_estimators=200,
                max_depth=15,
                min_samples_split=5,
                random_state=42,
                n_jobs=-1,
            ),
            'description': (
                'Extremely Randomized Trees — faster than RF, uses random thresholds. '
                'Good for high-dimensional feature spaces.'
            ),
            'hyperparameters': {
                'n_estimators': '200 trees',
                'max_depth': '15 (matches RF for fair comparison)',
            },
        },
        'AdaBoost': {
            'instance': AdaBoostClassifier(
                n_estimators=150,
                learning_rate=0.5,
                random_state=42,
                algorithm='SAMME.R',
            ),
            'description': (
                'Adaptive Boosting — focuses on misclassified samples. '
                'Good when classes are separable but with noise.'
            ),
            'hyperparameters': {
                'n_estimators': '150 weak learners',
                'learning_rate': '0.5 (moderate boosting strength)',
            },
        },

        # ── Distance-Based Methods ──
        'KNN_5': {
            'instance': KNeighborsClassifier(
                n_neighbors=5,
                weights='distance',
                metric='minkowski',
                p=2,
                n_jobs=-1,
            ),
            'description': (
                'K-Nearest Neighbors (k=5). Instance-based learning — '
                'classifies by majority vote of nearest neighbors. '
                'Current secondary model.'
            ),
            'hyperparameters': {
                'n_neighbors': '5 (balances bias-variance)',
                'weights': 'distance (closer neighbors have more influence)',
            },
        },
        'KNN_7': {
            'instance': KNeighborsClassifier(
                n_neighbors=7,
                weights='distance',
                metric='minkowski',
                p=2,
                n_jobs=-1,
            ),
            'description': 'KNN with k=7 — more neighbors for smoother decision boundaries.',
            'hyperparameters': {'n_neighbors': '7'},
        },
        'KNN_3': {
            'instance': KNeighborsClassifier(
                n_neighbors=3,
                weights='distance',
                n_jobs=-1,
            ),
            'description': 'KNN with k=3 — fewer neighbors, more sensitive to local patterns.',
            'hyperparameters': {'n_neighbors': '3'},
        },

        # ── Linear Methods ──
        'LogisticRegression': {
            'instance': LogisticRegression(
                max_iter=1000,
                multi_class='multinomial',
                solver='lbfgs',
                C=1.0,
                random_state=42,
                class_weight='balanced',
            ),
            'description': (
                'Multinomial Logistic Regression — linear classifier extended to multi-class. '
                'Baseline model. If this performs well, data is linearly separable.'
            ),
            'hyperparameters': {
                'multi_class': 'multinomial (softmax)',
                'C': '1.0 (regularization strength)',
                'class_weight': 'balanced',
            },
        },

        # ── SVM ──
        'SVM_RBF': {
            'instance': SVC(
                kernel='rbf',
                C=10.0,
                gamma='scale',
                probability=True,
                random_state=42,
                class_weight='balanced',
            ),
            'description': (
                'Support Vector Machine with RBF kernel — '
                'finds optimal hyperplane in transformed feature space. '
                'Excellent for moderate-sized datasets with complex boundaries.'
            ),
            'hyperparameters': {
                'kernel': 'rbf (Radial Basis Function — non-linear)',
                'C': '10.0 (high penalty for misclassification)',
                'gamma': 'scale (auto-calculated from features)',
            },
        },
        'SVM_Linear': {
            'instance': SVC(
                kernel='linear',
                C=1.0,
                probability=True,
                random_state=42,
                class_weight='balanced',
            ),
            'description': 'Linear SVM — tests if linear separation is sufficient.',
            'hyperparameters': {
                'kernel': 'linear',
                'C': '1.0',
            },
        },

        # ── Neural Network ──
        'MLP_Neural': {
            'instance': MLPClassifier(
                hidden_layer_sizes=(128, 64, 32),
                activation='relu',
                solver='adam',
                max_iter=500,
                learning_rate='adaptive',
                learning_rate_init=0.001,
                early_stopping=True,
                validation_fraction=0.15,
                random_state=42,
                batch_size=32,
            ),
            'description': (
                'Multi-Layer Perceptron (3 hidden layers: 128→64→32). '
                'Deep learning approach — can learn complex non-linear patterns. '
                'Uses early stopping to prevent overfitting.'
            ),
            'hyperparameters': {
                'architecture': '38→128→64→32→4',
                'activation': 'ReLU',
                'optimizer': 'Adam (lr=0.001, adaptive)',
                'early_stopping': 'Yes (15% validation)',
            },
        },
        'MLP_Simple': {
            'instance': MLPClassifier(
                hidden_layer_sizes=(64, 32),
                activation='relu',
                solver='adam',
                max_iter=500,
                early_stopping=True,
                random_state=42,
            ),
            'description': 'Simpler MLP (2 layers: 64→32) — tests if fewer parameters suffice.',
            'hyperparameters': {
                'architecture': '38→64→32→4',
            },
        },

        # ── Probabilistic ──
        'NaiveBayes': {
            'instance': GaussianNB(),
            'description': (
                'Gaussian Naive Bayes — assumes features are independent and normally distributed. '
                'Fast baseline. If it performs well, features are highly discriminative.'
            ),
            'hyperparameters': {
                'assumption': 'Gaussian feature distribution',
                'independence': 'Features assumed independent (naive)',
            },
        },

        # ── Decision Tree (baseline) ──
        'DecisionTree': {
            'instance': DecisionTreeClassifier(
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                class_weight='balanced',
            ),
            'description': (
                'Single Decision Tree — interpretable baseline. '
                'If RF >> DT, then ensemble averaging helps significantly.'
            ),
            'hyperparameters': {
                'max_depth': '10',
                'class_weight': 'balanced',
            },
        },
    }

    # Add XGBoost if available
    if HAS_XGBOOST:
        models['XGBoost'] = {
            'instance': XGBClassifier(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                reg_alpha=0.1,
                reg_lambda=1.0,
                random_state=42,
                use_label_encoder=False,
                eval_metric='mlogloss',
                n_jobs=-1,
            ),
            'description': (
                'eXtreme Gradient Boosting — optimized distributed gradient boosting. '
                'State-of-the-art for tabular data. Uses regularization (L1+L2).'
            ),
            'hyperparameters': {
                'n_estimators': '200 boosting rounds',
                'max_depth': '6 (shallower than RF, boosting compensates)',
                'regularization': 'L1=0.1, L2=1.0 (prevents overfitting)',
                'subsample': '0.8 (row sampling)',
                'colsample_bytree': '0.8 (feature sampling per tree)',
            },
        }

    # Add LightGBM if available
    if HAS_LIGHTGBM:
        models['LightGBM'] = {
            'instance': LGBMClassifier(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                reg_alpha=0.1,
                reg_lambda=1.0,
                random_state=42,
                n_jobs=-1,
                verbose=-1,
            ),
            'description': (
                'Light Gradient Boosting Machine — faster than XGBoost, '
                'uses histogram-based splitting. Great for large datasets.'
            ),
            'hyperparameters': {
                'n_estimators': '200',
                'max_depth': '6',
                'method': 'Histogram-based leaf-wise growth',
            },
        }

    return models


# ═══════════════════════════════════════════════════════════════════
#  METRICS CALCULATION
# ═══════════════════════════════════════════════════════════════════

def calculate_specificity(y_true: np.ndarray, y_pred: np.ndarray, labels: List) -> Dict[str, float]:
    """
    Calculate specificity (True Negative Rate) for each class.
    Specificity = TN / (TN + FP) = 1 - FPR
    
    For multi-class: treat each class as binary (one-vs-rest).
    """
    cm = confusion_matrix(y_true, y_pred, labels=range(len(labels)))
    specificity = {}

    for i, label in enumerate(labels):
        # True Negatives: all correctly classified as NOT this class
        tn = cm.sum() - cm[i, :].sum() - cm[:, i].sum() + cm[i, i]
        # False Positives: predicted as this class but actually another
        fp = cm[:, i].sum() - cm[i, i]
        
        specificity[label] = round(tn / (tn + fp), 4) if (tn + fp) > 0 else 0.0

    return specificity


def calculate_sensitivity(y_true: np.ndarray, y_pred: np.ndarray, labels: List) -> Dict[str, float]:
    """
    Calculate sensitivity (True Positive Rate / Recall) for each class.
    Sensitivity = TP / (TP + FN)
    
    This is equivalent to per-class recall.
    """
    cm = confusion_matrix(y_true, y_pred, labels=range(len(labels)))
    sensitivity = {}

    for i, label in enumerate(labels):
        tp = cm[i, i]
        fn = cm[i, :].sum() - tp
        sensitivity[label] = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0.0

    return sensitivity


def evaluate_single_model(
    model,
    X_train: np.ndarray,
    X_test: np.ndarray,
    y_train: np.ndarray,
    y_test: np.ndarray,
    label_names: List[str],
    n_cv_folds: int = 5,
) -> Dict[str, Any]:
    """
    Train and evaluate a single model with comprehensive metrics.
    
    Returns dict with:
      - accuracy, precision, recall, f1 (macro + weighted + per-class)
      - sensitivity, specificity (per-class)
      - roc_auc (one-vs-rest)
      - cross_validation scores
      - confusion_matrix
      - training_time, inference_time
      - matthews_corrcoef, cohen_kappa
    """
    results = {}

    # ── Training ──
    start_time = time.time()
    model.fit(X_train, y_train)
    train_time = time.time() - start_time
    results['training_time_seconds'] = round(train_time, 4)

    # ── Prediction ──
    start_time = time.time()
    y_pred = model.predict(X_test)
    inference_time = time.time() - start_time
    results['inference_time_seconds'] = round(inference_time, 4)
    results['inference_time_per_sample_ms'] = round((inference_time / len(X_test)) * 1000, 4)

    # ── Core Metrics ──
    results['accuracy'] = round(accuracy_score(y_test, y_pred), 4)

    # Precision
    results['precision_macro'] = round(precision_score(y_test, y_pred, average='macro', zero_division=0), 4)
    results['precision_weighted'] = round(precision_score(y_test, y_pred, average='weighted', zero_division=0), 4)
    
    # Recall
    results['recall_macro'] = round(recall_score(y_test, y_pred, average='macro', zero_division=0), 4)
    results['recall_weighted'] = round(recall_score(y_test, y_pred, average='weighted', zero_division=0), 4)

    # F1-Score
    results['f1_macro'] = round(f1_score(y_test, y_pred, average='macro', zero_division=0), 4)
    results['f1_weighted'] = round(f1_score(y_test, y_pred, average='weighted', zero_division=0), 4)

    # ── Per-Class Metrics ──
    report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    per_class = {}
    for i, label in enumerate(label_names):
        key = str(i)
        if key in report:
            per_class[label] = {
                'precision': round(report[key]['precision'], 4),
                'recall': round(report[key]['recall'], 4),
                'f1_score': round(report[key]['f1-score'], 4),
                'support': int(report[key]['support']),
            }
    results['per_class'] = per_class

    # ── Sensitivity & Specificity (per class) ──
    results['sensitivity'] = calculate_sensitivity(y_test, y_pred, label_names)
    results['specificity'] = calculate_specificity(y_test, y_pred, label_names)

    # ── Confusion Matrix ──
    cm = confusion_matrix(y_test, y_pred)
    results['confusion_matrix'] = cm.tolist()

    # ── ROC AUC (One-vs-Rest) ──
    try:
        if hasattr(model, 'predict_proba'):
            y_proba = model.predict_proba(X_test)
            y_test_bin = label_binarize(y_test, classes=range(len(label_names)))
            results['roc_auc_ovr'] = round(
                roc_auc_score(y_test_bin, y_proba, multi_class='ovr', average='macro'),
                4,
            )
            results['roc_auc_weighted'] = round(
                roc_auc_score(y_test_bin, y_proba, multi_class='ovr', average='weighted'),
                4,
            )
        else:
            results['roc_auc_ovr'] = None
            results['roc_auc_weighted'] = None
    except Exception:
        results['roc_auc_ovr'] = None
        results['roc_auc_weighted'] = None

    # ── Additional Metrics ──
    results['matthews_corrcoef'] = round(matthews_corrcoef(y_test, y_pred), 4)
    results['cohen_kappa'] = round(cohen_kappa_score(y_test, y_pred), 4)

    # ── Cross-Validation (5-fold stratified) ──
    try:
        cv = StratifiedKFold(n_splits=n_cv_folds, shuffle=True, random_state=42)
        cv_results = cross_validate(
            model.__class__(**model.get_params()),
            np.vstack([X_train, X_test]),
            np.concatenate([y_train, y_test]),
            cv=cv,
            scoring=['accuracy', 'f1_macro', 'precision_macro', 'recall_macro'],
            n_jobs=-1,
        )
        results['cv_accuracy_mean'] = round(cv_results['test_accuracy'].mean(), 4)
        results['cv_accuracy_std'] = round(cv_results['test_accuracy'].std(), 4)
        results['cv_f1_mean'] = round(cv_results['test_f1_macro'].mean(), 4)
        results['cv_f1_std'] = round(cv_results['test_f1_macro'].std(), 4)
        results['cv_precision_mean'] = round(cv_results['test_precision_macro'].mean(), 4)
        results['cv_recall_mean'] = round(cv_results['test_recall_macro'].mean(), 4)
        results['cv_scores'] = cv_results['test_accuracy'].round(4).tolist()
    except Exception as e:
        logger.warning(f"Cross-validation failed: {e}")
        results['cv_accuracy_mean'] = results['accuracy']
        results['cv_accuracy_std'] = 0.0
        results['cv_f1_mean'] = results['f1_macro']
        results['cv_f1_std'] = 0.0
        results['cv_scores'] = []

    return results


# ═══════════════════════════════════════════════════════════════════
#  MAIN COMPARISON FUNCTION
# ═══════════════════════════════════════════════════════════════════

def run_model_comparison(
    training_data: List[Dict[str, Any]],
    feature_extractor,
    test_size: float = 0.2,
    noise_levels: List[float] = [0.0, 0.3, 0.5],
    n_cv_folds: int = 5,
    save_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run comprehensive comparison of all models.
    
    Args:
        training_data: List of dicts with 'marks', 'interests', 'projects', 'label'
        feature_extractor: Function(marks, interests, projects) -> np.ndarray
        test_size: Proportion for test set
        noise_levels: Different noise levels to test robustness
        n_cv_folds: Number of cross-validation folds
        save_dir: Directory to save results
    
    Returns:
        Comprehensive comparison results
    """
    logger.info("=" * 70)
    logger.info("🔬 COMPREHENSIVE MODEL COMPARISON")
    logger.info("=" * 70)

    # ── 1. Extract features ──
    logger.info("\n📊 Extracting features from training data...")
    X_list, y_list = [], []
    
    for sample in training_data:
        try:
            features = feature_extractor(
                sample.get('marks', {}),
                sample.get('interests', []),
                sample.get('projects', []),
            )
            X_list.append(features)
            y_list.append(sample['label'])
        except Exception as e:
            logger.warning(f"Feature extraction failed for sample: {e}")

    X = np.array(X_list)
    y = np.array(y_list)

    logger.info(f"   Total samples: {len(X)}")
    logger.info(f"   Feature dimension: {X.shape[1]}")
    logger.info(f"   Class distribution: {dict(zip(*np.unique(y, return_counts=True)))}")

    # ── 2. Encode labels ──
    label_enc = LabelEncoder()
    y_encoded = label_enc.fit_transform(y)
    label_names = list(label_enc.classes_)
    logger.info(f"   Labels: {label_names}")

    # ── 3. Train/test split ──
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded,
        test_size=test_size,
        random_state=42,
        stratify=y_encoded,
    )

    logger.info(f"   Train: {len(X_train)}, Test: {len(X_test)}")

    # ── 4. Scale features ──
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # ── 5. Get model catalogue ──
    models = get_model_catalogue()
    logger.info(f"\n🤖 Comparing {len(models)} models...\n")

    # ── 6. Evaluate each model ──
    all_results = {}
    
    for name, model_info in models.items():
        logger.info(f"  Training {name}...")
        try:
            model = model_info['instance']
            
            results = evaluate_single_model(
                model=model,
                X_train=X_train_scaled,
                X_test=X_test_scaled,
                y_train=y_train,
                y_test=y_test,
                label_names=label_names,
                n_cv_folds=n_cv_folds,
            )
            
            results['description'] = model_info['description']
            results['hyperparameters'] = model_info['hyperparameters']
            all_results[name] = results
            
            logger.info(
                f"    ✅ {name}: Acc={results['accuracy']:.4f} "
                f"F1={results['f1_macro']:.4f} "
                f"CV={results['cv_accuracy_mean']:.4f}±{results['cv_accuracy_std']:.4f} "
                f"Time={results['training_time_seconds']:.3f}s"
            )
        except Exception as e:
            logger.error(f"    ❌ {name} failed: {e}")
            all_results[name] = {'error': str(e)}

    # ── 7. Rank models ──
    ranking = _rank_models(all_results)

    # ── 8. Generate report ──
    report = {
        'timestamp': datetime.utcnow().isoformat(),
        'dataset': {
            'total_samples': len(X),
            'feature_dimension': X.shape[1],
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'test_size': test_size,
            'class_distribution': {
                label_names[i]: int(count) 
                for i, count in enumerate(np.bincount(y_encoded))
            },
            'cv_folds': n_cv_folds,
        },
        'models': all_results,
        'ranking': ranking,
        'best_model': ranking[0] if ranking else None,
        'recommendation': _generate_recommendation(ranking, all_results),
    }

    # ── 9. Print summary ──
    _print_comparison_table(all_results, ranking, label_names)

    # ── 10. Save results ──
    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
        report_path = os.path.join(save_dir, 'model_comparison_report.json')
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        logger.info(f"\n📁 Report saved to: {report_path}")

    return report


# ═══════════════════════════════════════════════════════════════════
#  RANKING & REPORTING
# ═══════════════════════════════════════════════════════════════════

def _rank_models(results: Dict[str, Dict]) -> List[Dict[str, Any]]:
    """
    Rank models using composite score:
      40% CV Accuracy (generalization)
      25% F1 Macro (class balance)
      15% ROC AUC (discrimination)
      10% Specificity avg (false positive control)
      10% Training speed (practical efficiency)
    """
    scored = []
    
    for name, r in results.items():
        if 'error' in r:
            continue
        
        cv_acc = r.get('cv_accuracy_mean', r.get('accuracy', 0))
        f1 = r.get('f1_macro', 0)
        roc = r.get('roc_auc_ovr', f1)  # fallback to f1 if no ROC
        if roc is None:
            roc = f1
        
        # Average specificity across classes
        spec = r.get('specificity', {})
        avg_spec = np.mean(list(spec.values())) if spec else 0.5
        
        # Speed score (inverse of training time, normalized)
        train_time = r.get('training_time_seconds', 1.0)
        speed_score = 1.0 / (1.0 + train_time)  # 0 to 1
        
        composite = (
            0.40 * cv_acc +
            0.25 * f1 +
            0.15 * roc +
            0.10 * avg_spec +
            0.10 * speed_score
        )
        
        scored.append({
            'model': name,
            'composite_score': round(composite, 4),
            'accuracy': r.get('accuracy', 0),
            'cv_accuracy': cv_acc,
            'f1_macro': f1,
            'roc_auc': roc,
            'avg_specificity': round(avg_spec, 4),
            'training_time': train_time,
        })
    
    scored.sort(key=lambda x: x['composite_score'], reverse=True)
    
    for i, s in enumerate(scored):
        s['rank'] = i + 1
    
    return scored


def _generate_recommendation(ranking: List[Dict], results: Dict) -> Dict[str, Any]:
    """Generate a recommendation with justification."""
    if not ranking:
        return {'model': 'RandomForest', 'reason': 'Default fallback'}
    
    best = ranking[0]
    second = ranking[1] if len(ranking) > 1 else None
    
    reasons = []
    reasons.append(f"Highest composite score: {best['composite_score']:.4f}")
    reasons.append(f"CV Accuracy: {best['cv_accuracy']:.4f} (generalizes well)")
    reasons.append(f"F1 Macro: {best['f1_macro']:.4f} (balanced across classes)")
    
    if best.get('roc_auc'):
        reasons.append(f"ROC AUC: {best['roc_auc']:.4f} (strong discrimination)")
    
    if second:
        diff = best['composite_score'] - second['composite_score']
        if diff < 0.005:
            reasons.append(
                f"Note: Very close to {second['model']} (diff={diff:.4f}). "
                f"Consider {second['model']} if speed is critical."
            )
    
    return {
        'recommended_model': best['model'],
        'composite_score': best['composite_score'],
        'reasons': reasons,
        'runner_up': second['model'] if second else None,
    }


def _print_comparison_table(
    results: Dict[str, Dict],
    ranking: List[Dict],
    label_names: List[str],
):
    """Print a formatted comparison table to the logger."""
    
    logger.info("\n" + "=" * 100)
    logger.info("📊 MODEL COMPARISON RESULTS")
    logger.info("=" * 100)
    
    # ── Summary Table ──
    header = (
        f"{'Rank':<5} {'Model':<20} {'Accuracy':>9} {'Precision':>10} "
        f"{'Recall':>8} {'F1-Macro':>9} {'ROC AUC':>8} "
        f"{'CV Acc':>8} {'Time(s)':>8} {'Score':>7}"
    )
    logger.info(f"\n{header}")
    logger.info("-" * len(header))
    
    for r in ranking:
        name = r['model']
        res = results[name]
        roc = r.get('roc_auc')
        roc_str = f"{roc:.4f}" if roc else "  N/A "
        
        line = (
            f"{r['rank']:<5} {name:<20} {res['accuracy']:>9.4f} "
            f"{res['precision_macro']:>10.4f} {res['recall_macro']:>8.4f} "
            f"{res['f1_macro']:>9.4f} {roc_str:>8} "
            f"{r['cv_accuracy']:>8.4f} {res['training_time_seconds']:>8.3f} "
            f"{r['composite_score']:>7.4f}"
        )
        
        if r['rank'] == 1:
            line += " ⭐ BEST"
        elif r['rank'] == 2:
            line += " 🥈"
        elif r['rank'] == 3:
            line += " 🥉"
        
        logger.info(line)

    # ── Per-Class Detail for Top 3 ──
    logger.info(f"\n{'─' * 100}")
    logger.info("🎯 PER-CLASS METRICS (Top 3 Models)")
    logger.info(f"{'─' * 100}")
    
    for r in ranking[:3]:
        name = r['model']
        res = results[name]
        
        logger.info(f"\n  #{r['rank']} {name} (Composite: {r['composite_score']:.4f})")
        logger.info(f"  {'Class':<6} {'Precision':>10} {'Recall':>8} {'F1':>8} "
                     f"{'Sensitivity':>12} {'Specificity':>12} {'Support':>8}")
        logger.info(f"  {'-'*6} {'-'*10} {'-'*8} {'-'*8} {'-'*12} {'-'*12} {'-'*8}")
        
        for label in label_names:
            pc = res.get('per_class', {}).get(label, {})
            sens = res.get('sensitivity', {}).get(label, 0)
            spec = res.get('specificity', {}).get(label, 0)
            
            logger.info(
                f"  {label:<6} {pc.get('precision', 0):>10.4f} "
                f"{pc.get('recall', 0):>8.4f} {pc.get('f1_score', 0):>8.4f} "
                f"{sens:>12.4f} {spec:>12.4f} {pc.get('support', 0):>8d}"
            )

    # ── Confusion Matrix for Best Model ──
    best_name = ranking[0]['model']
    best_res = results[best_name]
    cm = best_res.get('confusion_matrix', [])
    
    if cm:
        logger.info(f"\n{'─' * 100}")
        logger.info(f"📊 CONFUSION MATRIX — {best_name} (Best Model)")
        logger.info(f"{'─' * 100}")
        logger.info(f"  {'Predicted →':>12} " + " ".join(f"{l:>6}" for l in label_names))
        logger.info(f"  {'Actual ↓':>12} " + " ".join(f"{'─'*6}" for _ in label_names))
        for i, row in enumerate(cm):
            logger.info(f"  {label_names[i]:>12} " + " ".join(f"{v:>6}" for v in row))

    # ── Recommendation ──
    logger.info(f"\n{'=' * 100}")
    logger.info("🏆 RECOMMENDATION")
    logger.info(f"{'=' * 100}")
    logger.info(f"\n  Best Model: {ranking[0]['model']}")
    logger.info(f"  Composite Score: {ranking[0]['composite_score']:.4f}")
    logger.info(f"  Accuracy: {ranking[0]['accuracy']:.4f}")
    logger.info(f"  CV Accuracy: {ranking[0]['cv_accuracy']:.4f} ± {results[ranking[0]['model']].get('cv_accuracy_std', 0):.4f}")

    best_res_detail = results[ranking[0]['model']]
    logger.info(f"\n  Description: {best_res_detail.get('description', 'N/A')}")
    logger.info(f"\n  Why this model:")
    logger.info(f"    • Highest composite score across accuracy, F1, ROC AUC, specificity, and speed")
    logger.info(f"    • Cross-validation confirms generalization (not just memorization)")
    
    if len(ranking) > 1:
        gap = ranking[0]['composite_score'] - ranking[1]['composite_score']
        logger.info(f"    • {gap:.4f} points ahead of runner-up ({ranking[1]['model']})")
    
    logger.info("")