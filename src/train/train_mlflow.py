"""Lab 3: compare three churn models, recording each training run in MLflow.

This extends the student's Lab 2 repository, which uses churn_v2.csv and
monthly_fee (not monthly_charges from the separate starter).
"""

import hashlib
import json
import os
import tempfile
import time
from pathlib import Path

import joblib
import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from mlflow.models import infer_signature
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.train.train import FEATURES

DATA_FILE = os.getenv("DATA_FILE", "data/churn_v2.csv")
SLICE_COLUMN = "contract"
BATCH = os.getenv("BATCH", os.getenv("GIT_SHA", "local")[:7])

# Three genuinely different model families, not just three names.
CANDIDATES = {
    "logreg": LogisticRegression(C=1.0, max_iter=1000, random_state=42),
    "random_forest": RandomForestClassifier(
        n_estimators=150, max_depth=8, min_samples_leaf=2, random_state=42, n_jobs=1
    ),
    "gradient_boosting": GradientBoostingClassifier(
        n_estimators=100, learning_rate=0.08, max_depth=3, random_state=42
    ),
}


def preprocessing() -> ColumnTransformer:
    return ColumnTransformer([
        ("num", StandardScaler(), ["tenure_months", "monthly_fee", "support_calls"]),
        ("cat", OneHotEncoder(handle_unknown="ignore"), ["contract", "internet_service"]),
    ])


def p95_latency_ms(model, X: pd.DataFrame, n: int = 200) -> float:
    """Measure 200 individual prediction calls, including preprocessing."""
    samples = []
    for i in range(n):
        start = time.perf_counter()
        model.predict_proba(X.iloc[[i % len(X)]])
        samples.append((time.perf_counter() - start) * 1000)
    return float(np.percentile(samples, 95))


def size_kb(model) -> float:
    with tempfile.TemporaryDirectory() as temp_dir:
        model_file = Path(temp_dir) / "candidate.joblib"
        joblib.dump(model, model_file)
        return model_file.stat().st_size / 1024


def main() -> None:
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
    mlflow.set_experiment("churn")

    data_file = Path(DATA_FILE)
    data = pd.read_csv(data_file)
    required = FEATURES + ["churn"]
    missing = sorted(set(required) - set(data.columns))
    if missing:
        raise ValueError(f"Missing columns in {DATA_FILE}: {missing}")
    X, y = data[FEATURES], data["churn"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    data_hash = hashlib.sha256(data_file.read_bytes()).hexdigest()

    for name, classifier in CANDIDATES.items():
        pipeline = Pipeline([("prep", preprocessing()), ("clf", classifier)])
        pipeline.fit(X_train, y_train)
        probabilities = pipeline.predict_proba(X_test)[:, 1]
        predictions = probabilities > 0.5

        with mlflow.start_run(run_name=name) as run:
            mlflow.log_param("model", name)
            mlflow.log_params({f"clf__{key}": val for key, val in classifier.get_params().items()})
            mlflow.log_param("data_file", DATA_FILE)
            mlflow.log_param("data_sha256", data_hash)
            mlflow.set_tags({"batch": BATCH, "git_sha": os.getenv("GIT_SHA", "local")})

            metrics = {
                "auc": roc_auc_score(y_test, probabilities),
                "f1": f1_score(y_test, predictions),
                "p95_latency_ms": p95_latency_ms(pipeline, X_test),
                "size_kb": size_kb(pipeline),
            }
            for contract in sorted(X_test[SLICE_COLUMN].unique()):
                slice_mask = (X_test[SLICE_COLUMN] == contract).to_numpy()
                metrics[f"f1_contract_{contract}"] = f1_score(
                    y_test[slice_mask], predictions[slice_mask], zero_division=0
                )
            mlflow.log_metrics({key: round(float(value), 4) for key, value in metrics.items()})

            # The sklearn pyfunc model's default prediction output is the class label.
            signature = infer_signature(X_test, pipeline.predict(X_test))
            info = mlflow.sklearn.log_model(
                pipeline,
                name="model",
                signature=signature,
                input_example=X_test.head(3),
                skops_trusted_types=["sklearn.tree._tree.Tree"],
            )
            mlflow.set_tag("model_uri", info.model_uri)
            print(
                f"{name:18s} run {run.info.run_id[:8]}  AUC {metrics['auc']:.3f}  "
                f"F1 {metrics['f1']:.3f}  p95 {metrics['p95_latency_ms']:.2f} ms  "
                f"size {metrics['size_kb']:.1f} KB"
            )

    print(json.dumps({"batch": BATCH, "data_sha256": data_hash, "experiment": "churn"}))


if __name__ == "__main__":
    main()
