from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = ROOT / "artifacts" / "model.joblib"
FEATURES = ["tenure_months", "monthly_fee", "contract", "internet_service", "support_calls"]


def train(data_path=ROOT / "data" / "churn_v2.csv", model_path=MODEL_PATH):
    df = pd.read_csv(data_path)
    X_train, X_test, y_train, y_test = train_test_split(
        df[FEATURES], df["churn"], test_size=0.2, random_state=42, stratify=df["churn"]
    )
    preprocessing = ColumnTransformer([
        ("num", StandardScaler(), ["tenure_months", "monthly_fee", "support_calls"]),
        ("cat", OneHotEncoder(handle_unknown="ignore"), ["contract", "internet_service"]),
    ])
    model = Pipeline([
        ("prep", preprocessing),
        ("clf", LogisticRegression(max_iter=1000, random_state=42)),
    ])
    model.fit(X_train, y_train)
    probabilities = model.predict_proba(X_test)[:, 1]
    model_path = Path(model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    print(f"F1: {f1_score(y_test, probabilities > 0.5):.3f}")
    print(f"AUC: {roc_auc_score(y_test, probabilities):.3f}")
    print(f"Saved: {model_path}")
    return model


if __name__ == "__main__":
    train()
