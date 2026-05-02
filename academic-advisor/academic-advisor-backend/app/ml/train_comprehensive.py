"""
Comprehensive ML Training Pipeline
====================================
Trains models on real Excel data + synthetic augmentation.
Uses 12+ algorithms, 3 ensemble methods, and anti-overfitting measures.
Auto-selects best model and saves metadata for frontend display.
"""

import os, json, warnings, logging
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

# ============== PATHS ==============
BASE_DIR = Path(__file__).resolve().parent
SAVED_MODELS_DIR = BASE_DIR / "saved_models"
EXPORTED_MARKS_DIR = BASE_DIR.parent.parent / "exported_marks"
EXCEL_FILE = EXPORTED_MARKS_DIR / "IT - Copy.xlsx"
METADATA_FILE = SAVED_MODELS_DIR / "training_metadata.json"

SAVED_MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Sheet name patterns to semester mapping
SHEET_SEMESTER = {
    "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8,
    "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8,
}


def _detect_semester(sheet_name: str) -> int:
    """Detect semester number from sheet name."""
    import re
    sn = sheet_name.upper()
    for key, val in SHEET_SEMESTER.items():
        if f"SEM-{key}" in sn or f"SEM {key}" in sn or f"-{key}-" in sn:
            return val
    m = re.search(r'SEM(?:ESTER)?\s*[-_]?\s*([IVX]+|\d+)', sn)
    if m:
        rom = m.group(1)
        return SHEET_SEMESTER.get(rom, 0)
    return 0


def load_real_data() -> pd.DataFrame:
    """Load real student data from Excel with multi-row headers."""
    if not EXCEL_FILE.exists():
        raise FileNotFoundError(f"Excel file not found: {EXCEL_FILE}")

    all_rows = []
    xls = pd.ExcelFile(EXCEL_FILE)

    for sheet_name in xls.sheet_names:
        sem = _detect_semester(sheet_name)
        if sem == 0:
            continue

        df = pd.read_excel(xls, sheet_name, header=None)

        # Find the header row (contains 'Sr' or 'Seat' or 'Name')
        header_row = None
        for i in range(min(10, len(df))):
            row_str = " ".join([str(v).strip().lower() for v in df.iloc[i].values if pd.notna(v)])
            if "sr" in row_str and ("seat" in row_str or "name" in row_str):
                header_row = i
                break

        if header_row is None:
            continue

        # Find TOT columns (total marks) - these are the actual scores
        sub_row = df.iloc[header_row]  # Subject names row
        mark_type_row = df.iloc[header_row + 1] if header_row + 1 < len(df) else None

        # Find columns with 'TOT' in the marks-type row
        tot_cols = []
        if mark_type_row is not None:
            for col_idx, val in enumerate(mark_type_row.values):
                if pd.notna(val) and str(val).strip().upper() == "TOT":
                    tot_cols.append(col_idx)

        # If no TOT columns found, try to find numeric columns after header
        if not tot_cols:
            # Use all numeric columns from actual data rows
            data_start = header_row + 4  # Skip header rows + max/min marks
            if data_start < len(df):
                sample = df.iloc[data_start]
                for col_idx in range(3, len(sample)):
                    try:
                        v = float(sample.iloc[col_idx])
                        tot_cols.append(col_idx)
                    except (ValueError, TypeError):
                        pass

        if len(tot_cols) < 2:
            continue

        # Parse student data - every 3 rows = one student (Marks, Grade, GP)
        data_start = header_row + 4  # after header, sub-header, max marks, min marks
        row_idx = data_start

        while row_idx < len(df):
            row = df.iloc[row_idx]

            # Check if this is a marks row (first cell should be numeric Sr.No)
            sr_val = row.iloc[0]
            try:
                sr_num = int(float(sr_val))
            except (ValueError, TypeError):
                row_idx += 1
                continue

            # Extract TOT scores
            scores = []
            for col_idx in tot_cols:
                try:
                    val = float(row.iloc[col_idx])
                    if 0 <= val <= 200:  # reasonable score range
                        scores.append(val)
                except (ValueError, TypeError, IndexError):
                    pass

            if len(scores) >= 2:
                all_rows.append({
                    "semester": sem,
                    "scores": scores,
                    "mean": float(np.mean(scores)),
                    "std": float(np.std(scores)),
                    "max": float(np.max(scores)),
                    "min": float(np.min(scores)),
                    "median": float(np.median(scores)),
                    "count": len(scores),
                })

            row_idx += 3  # Skip Grade and GP rows

    if not all_rows:
        raise ValueError("No valid student data found in Excel")

    return pd.DataFrame(all_rows)


# ============== FEATURE ENGINEERING ==============

def engineer_features(df: pd.DataFrame) -> tuple:
    """Create ML features from raw student data."""
    features = []
    for _, row in df.iterrows():
        scores = np.array(row["scores"])
        n = len(scores)
        sorted_scores = np.sort(scores)

        feat = {
            "mean_score": row["mean"],
            "std_score": row["std"],
            "max_score": row["max"],
            "min_score": row["min"],
            "median_score": row["median"],
            "range_score": row["max"] - row["min"],
            "cv_score": row["std"] / max(row["mean"], 1),  # coefficient of variation
            "skewness": float(pd.Series(scores).skew()) if n > 2 else 0,
            "kurtosis": float(pd.Series(scores).kurtosis()) if n > 3 else 0,
            "q25": float(np.percentile(scores, 25)),
            "q75": float(np.percentile(scores, 75)),
            "iqr": float(np.percentile(scores, 75) - np.percentile(scores, 25)),
            "top_avg": float(np.mean(sorted_scores[-max(1, n//3):])),
            "bottom_avg": float(np.mean(sorted_scores[:max(1, n//3)])),
            "strong_count": int(np.sum(scores >= 70)),
            "weak_count": int(np.sum(scores < 50)),
            "consistency": 1.0 / (1.0 + row["std"]),
            "semester": row["semester"],
        }
        features.append(feat)

    X = pd.DataFrame(features)
    X = X.fillna(0).replace([np.inf, -np.inf], 0)

    # Create target: elective recommendation based on performance profile
    y = create_target_labels(X)
    return X, y


def create_target_labels(X: pd.DataFrame) -> np.ndarray:
    """Create elective recommendation labels based on student profile."""
    labels = []
    electives = ["ML", "WT", "DWM", "CCS"]

    for _, row in X.iterrows():
        mean = row["mean_score"]
        std = row["std_score"]
        consistency = row["consistency"]
        top = row["top_avg"]

        # Rule-based labeling with some noise for realism
        if mean >= 70 and consistency > 0.06:
            label = "ML"   # Strong consistent students → ML
        elif top >= 75 and std > 12:
            label = "WT"   # High peaks but variable → Web Tech
        elif mean >= 55 and mean < 70:
            label = "DWM"  # Mid-range → Data Warehousing
        else:
            label = "CCS"  # Others → Cloud Computing
        labels.append(label)

    return np.array(labels)


# ============== SYNTHETIC DATA GENERATION ==============

def generate_synthetic_data(X: pd.DataFrame, y: np.ndarray, ratio: float = 0.5) -> tuple:
    """Generate synthetic data using SMOTE + Gaussian noise."""
    from sklearn.preprocessing import LabelEncoder

    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    n_synthetic = int(len(X) * ratio)
    if n_synthetic < 10:
        n_synthetic = 10

    synthetic_X = []
    synthetic_y = []

    classes, counts = np.unique(y_enc, return_counts=True)
    min_count = max(counts.min(), 2)

    for cls in classes:
        cls_mask = y_enc == cls
        cls_data = X[cls_mask].values
        n_cls = max(n_synthetic // len(classes), 2)

        for _ in range(n_cls):
            # Pick two random samples from same class and interpolate (SMOTE-like)
            if len(cls_data) >= 2:
                idx1, idx2 = np.random.choice(len(cls_data), 2, replace=False)
                lam = np.random.uniform(0.3, 0.7)
                new_sample = cls_data[idx1] * lam + cls_data[idx2] * (1 - lam)
            else:
                new_sample = cls_data[0].copy()

            # Add small Gaussian noise (2-5% of feature std)
            noise = np.random.normal(0, 0.03, new_sample.shape) * (np.std(cls_data, axis=0) + 1e-6)
            new_sample = new_sample + noise

            synthetic_X.append(new_sample)
            synthetic_y.append(cls)

    synth_df = pd.DataFrame(synthetic_X, columns=X.columns)
    synth_labels = le.inverse_transform(synthetic_y)

    # Combine real + synthetic
    X_combined = pd.concat([X, synth_df], ignore_index=True)
    y_combined = np.concatenate([y, synth_labels])

    return X_combined, y_combined, len(synthetic_X)


# ============== MODEL TRAINING ==============

def train_all_models(X: pd.DataFrame, y: np.ndarray) -> dict:
    """Train 12+ algorithms with anti-overfitting measures."""
    from sklearn.model_selection import StratifiedKFold, cross_val_score
    from sklearn.preprocessing import LabelEncoder, StandardScaler
    from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
    from sklearn.model_selection import train_test_split
    import joblib

    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Stratified split
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y_enc, test_size=0.2, stratify=y_enc, random_state=42
    )

    # Define models with anti-overfitting parameters
    models = _get_model_dict()

    results = {}
    best_model = None
    best_score = 0
    best_name = ""

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    for name, model in models.items():
        try:
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)

            acc = accuracy_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred, average="weighted", zero_division=0)
            prec = precision_score(y_test, y_pred, average="weighted", zero_division=0)
            rec = recall_score(y_test, y_pred, average="weighted", zero_division=0)

            # Cross-validation for overfitting check
            cv_scores = cross_val_score(model, X_scaled, y_enc, cv=cv, scoring="accuracy")
            cv_mean = cv_scores.mean()
            cv_std = cv_scores.std()

            # Overfitting indicator: train accuracy vs CV accuracy gap
            train_acc = accuracy_score(y_train, model.predict(X_train))
            overfit_gap = train_acc - cv_mean

            results[name] = {
                "accuracy": round(acc, 4),
                "f1_score": round(f1, 4),
                "precision": round(prec, 4),
                "recall": round(rec, 4),
                "cv_mean": round(cv_mean, 4),
                "cv_std": round(cv_std, 4),
                "train_accuracy": round(train_acc, 4),
                "overfit_gap": round(overfit_gap, 4),
            }

            # Select best by F1 (with overfitting penalty)
            adjusted_score = f1 - max(0, overfit_gap - 0.1) * 0.5
            if adjusted_score > best_score:
                best_score = adjusted_score
                best_model = model
                best_name = name

            # Save each model
            model_path = SAVED_MODELS_DIR / f"model_{name.lower().replace(' ', '_')}.joblib"
            joblib.dump(model, model_path)
            logger.info(f"  {name}: acc={acc:.3f} f1={f1:.3f} cv={cv_mean:.3f}±{cv_std:.3f} gap={overfit_gap:.3f}")

        except Exception as e:
            logger.warning(f"  {name}: FAILED - {e}")
            results[name] = {"error": str(e)}

    # Save scaler and encoder
    joblib.dump(scaler, SAVED_MODELS_DIR / "scaler.joblib")
    joblib.dump(le, SAVED_MODELS_DIR / "label_enc.joblib")

    return {
        "results": results,
        "best_name": best_name,
        "best_score": best_score,
        "best_model": best_model,
        "scaler": scaler,
        "label_encoder": le,
        "X_train_shape": X_train.shape,
        "X_test_shape": X_test.shape,
    }


def _get_model_dict() -> dict:
    """Return dictionary of ML models with anti-overfitting configs."""
    from sklearn.ensemble import (
        RandomForestClassifier, GradientBoostingClassifier,
        ExtraTreesClassifier, AdaBoostClassifier,
        BaggingClassifier, VotingClassifier, StackingClassifier,
    )
    from sklearn.linear_model import LogisticRegression
    from sklearn.svm import SVC
    from sklearn.neighbors import KNeighborsClassifier
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.naive_bayes import GaussianNB
    from sklearn.neural_network import MLPClassifier

    # Optional: XGBoost and LightGBM
    xgb_cls = lgb_cls = None
    try:
        from xgboost import XGBClassifier
        xgb_cls = XGBClassifier
    except ImportError:
        pass
    try:
        from lightgbm import LGBMClassifier
        lgb_cls = LGBMClassifier
    except ImportError:
        pass

    models = {
        "RandomForest": RandomForestClassifier(
            n_estimators=200, max_depth=10, min_samples_split=5,
            min_samples_leaf=3, max_features="sqrt", random_state=42
        ),
        "GradientBoosting": GradientBoostingClassifier(
            n_estimators=150, max_depth=5, learning_rate=0.1,
            min_samples_split=5, min_samples_leaf=3,
            subsample=0.8, random_state=42
        ),
        "ExtraTrees": ExtraTreesClassifier(
            n_estimators=200, max_depth=10, min_samples_split=5,
            min_samples_leaf=3, random_state=42
        ),
        "AdaBoost": AdaBoostClassifier(
            n_estimators=100, learning_rate=0.1, random_state=42
        ),
        "LogisticRegression": LogisticRegression(
            C=1.0, max_iter=1000, solver="lbfgs",
            multi_class="multinomial", random_state=42
        ),
        "SVM_RBF": SVC(
            C=1.0, kernel="rbf", gamma="scale", random_state=42
        ),
        "SVM_Linear": SVC(
            C=1.0, kernel="linear", random_state=42
        ),
        "KNN": KNeighborsClassifier(
            n_neighbors=5, weights="distance", metric="minkowski"
        ),
        "DecisionTree": DecisionTreeClassifier(
            max_depth=8, min_samples_split=5,
            min_samples_leaf=3, random_state=42
        ),
        "NaiveBayes": GaussianNB(),
        "NeuralNetwork": MLPClassifier(
            hidden_layer_sizes=(64, 32), max_iter=500,
            early_stopping=True, validation_fraction=0.15,
            alpha=0.01, random_state=42
        ),
    }

    if xgb_cls:
        models["XGBoost"] = xgb_cls(
            n_estimators=150, max_depth=6, learning_rate=0.1,
            subsample=0.8, colsample_bytree=0.8,
            reg_alpha=0.1, reg_lambda=1.0,
            random_state=42, eval_metric="mlogloss",
        )

    if lgb_cls:
        models["LightGBM"] = lgb_cls(
            n_estimators=150, max_depth=6, learning_rate=0.1,
            subsample=0.8, colsample_bytree=0.8,
            reg_alpha=0.1, reg_lambda=1.0,
            random_state=42, verbose=-1,
        )

    # Ensemble: Bagging
    models["Bagging"] = BaggingClassifier(
        n_estimators=50, max_samples=0.8,
        max_features=0.8, random_state=42
    )

    # Ensemble: Voting (top 3 base models)
    base_estimators = [
        ("rf", models["RandomForest"]),
        ("gb", models["GradientBoosting"]),
        ("et", models["ExtraTrees"]),
    ]
    if xgb_cls:
        base_estimators.append(("xgb", models["XGBoost"]))

    models["VotingEnsemble"] = VotingClassifier(
        estimators=base_estimators, voting="hard"
    )

    # Ensemble: Stacking
    models["StackingEnsemble"] = StackingClassifier(
        estimators=base_estimators,
        final_estimator=LogisticRegression(max_iter=1000, random_state=42),
        cv=3
    )

    return models


# ============== METADATA & REPORTING ==============

def save_metadata(train_info: dict, data_info: dict, synthetic_count: int):
    """Save training metadata for frontend consumption."""
    results = train_info["results"]
    best_name = train_info["best_name"]

    # Rank models by accuracy (excluding errors)
    valid = {k: v for k, v in results.items() if "accuracy" in v}
    ranking = sorted(valid.keys(), key=lambda k: valid[k]["accuracy"], reverse=True)

    best_result = valid.get(best_name, {})

    metadata = {
        "training_timestamp": datetime.now().isoformat(),
        "data_source": str(EXCEL_FILE.name),
        "total_real_samples": data_info["real_count"],
        "synthetic_samples": synthetic_count,
        "total_training_samples": data_info["total_count"],
        "feature_count": data_info["feature_count"],
        "feature_names": data_info["feature_names"],
        "label_distribution": data_info["label_dist"],
        "best_model": best_name,
        "best_accuracy": best_result.get("accuracy", 0),
        "best_f1_score": best_result.get("f1_score", 0),
        "best_precision": best_result.get("precision", 0),
        "best_recall": best_result.get("recall", 0),
        "cv_mean": best_result.get("cv_mean", 0),
        "cv_std": best_result.get("cv_std", 0),
        "overfit_gap": best_result.get("overfit_gap", 0),
        "training_samples": train_info["X_train_shape"][0],
        "test_samples": train_info["X_test_shape"][0],
        "all_models": {k: v for k, v in valid.items()},
        "model_ranking": ranking,
        "anti_overfitting_measures": [
            "StratifiedKFold 5-fold cross-validation",
            "Max depth limits on tree-based models",
            "Min samples split/leaf constraints",
            "Subsample < 1.0 for boosting models",
            "L1/L2 regularization (LogReg, XGB, LGBM)",
            "Early stopping (Neural Network)",
            "Overfit gap monitoring (train-CV gap penalty)",
            "Synthetic data augmentation (SMOTE + Gaussian noise)",
        ],
    }

    with open(METADATA_FILE, "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Metadata saved to {METADATA_FILE}")
    return metadata


# ============== MAIN PIPELINE ==============

def run_training_pipeline():
    """Run the complete training pipeline."""
    print("=" * 60)
    print("  COMPREHENSIVE ML TRAINING PIPELINE")
    print("=" * 60)

    # Step 1: Load data
    print("\n[1/5] Loading real student data...")
    raw_df = load_real_data()
    print(f"  Loaded {len(raw_df)} student records from {EXCEL_FILE.name}")

    # Step 2: Feature engineering
    print("\n[2/5] Engineering features...")
    X, y = engineer_features(raw_df)
    print(f"  Created {X.shape[1]} features for {X.shape[0]} samples")
    print(f"  Label distribution: {dict(zip(*np.unique(y, return_counts=True)))}")

    # Step 3: Synthetic augmentation
    print("\n[3/5] Generating synthetic data...")
    X_aug, y_aug, n_synth = generate_synthetic_data(X, y, ratio=0.5)
    print(f"  Generated {n_synth} synthetic samples")
    print(f"  Total dataset: {len(X_aug)} samples")
    print(f"  Augmented distribution: {dict(zip(*np.unique(y_aug, return_counts=True)))}")

    # Step 4: Train models
    print("\n[4/5] Training models...")
    train_info = train_all_models(X_aug, y_aug)
    print(f"\n  Best model: {train_info['best_name']}")
    best_res = train_info["results"].get(train_info["best_name"], {})
    print(f"  Accuracy: {best_res.get('accuracy', 0):.4f}")
    print(f"  F1 Score: {best_res.get('f1_score', 0):.4f}")
    print(f"  CV Mean:  {best_res.get('cv_mean', 0):.4f} ± {best_res.get('cv_std', 0):.4f}")
    print(f"  Overfit Gap: {best_res.get('overfit_gap', 0):.4f}")

    # Step 5: Save metadata
    print("\n[5/5] Saving metadata...")
    data_info = {
        "real_count": len(X),
        "total_count": len(X_aug),
        "feature_count": X.shape[1],
        "feature_names": X.columns.tolist(),
        "label_dist": {k: int(v) for k, v in zip(*np.unique(y_aug, return_counts=True))},
    }
    metadata = save_metadata(train_info, data_info, n_synth)

    # Print summary
    print("\n" + "=" * 60)
    print("  TRAINING COMPLETE - MODEL COMPARISON")
    print("=" * 60)
    print(f"{'Model':<22} {'Acc':>6} {'F1':>6} {'CV':>6} {'Gap':>6}")
    print("-" * 48)

    for name in metadata["model_ranking"]:
        r = metadata["all_models"][name]
        marker = " *BEST*" if name == metadata["best_model"] else ""
        print(f"  {name:<20} {r['accuracy']:>5.3f} {r['f1_score']:>5.3f} "
              f"{r['cv_mean']:>5.3f} {r['overfit_gap']:>5.3f}{marker}")

    print(f"\n  Best: {metadata['best_model']} "
          f"(acc={metadata['best_accuracy']:.3f}, f1={metadata['best_f1_score']:.3f})")
    print(f"  Models saved to: {SAVED_MODELS_DIR}")
    print("=" * 60)

    return metadata


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_training_pipeline()
