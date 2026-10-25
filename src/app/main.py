from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field

ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = ROOT / "artifacts" / "model.joblib"
FEATURES = ["tenure_months", "monthly_fee", "contract", "internet_service", "support_calls"]


class Customer(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    tenure_months: int = Field(ge=0)
    monthly_fee: float = Field(ge=0, allow_inf_nan=False)
    contract: Literal["month-to-month", "one-year", "two-year"]
    internet_service: Literal["dsl", "fiber", "none"]
    support_calls: int = Field(ge=0)


class Prediction(BaseModel):
    churn_probability: float = Field(ge=0, le=1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.model = joblib.load(MODEL_PATH)
    yield
    del app.state.model


app = FastAPI(title="AI381 Churn API", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict", response_model=Prediction)
def predict(customer: Customer):
    frame = pd.DataFrame([customer.model_dump()], columns=FEATURES)
    probability = float(app.state.model.predict_proba(frame)[0, 1])
    return Prediction(churn_probability=round(probability, 3))
