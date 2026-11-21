"""Fill MODEL_SELECTION.md from the three real MLflow runs.

Run after: python -m src.train.train_mlflow
This avoids copying wrong scores/run IDs into the lab report by hand.
"""

import os
from pathlib import Path

import mlflow
from promote import LATENCY_BUDGET_MS, MIN_GAIN

BATCH = os.getenv("BATCH", os.getenv("GIT_SHA", "local")[:7])
WHY = {
    "logreg": "Simple baseline; usually fast and small.",
    "random_forest": "Tests whether combining many trees helps.",
    "gradient_boosting": "Tests whether boosting improves predictions.",
}


def main() -> None:
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
    runs = mlflow.search_runs(
        experiment_names=["churn"], filter_string=f"tags.batch = '{BATCH}'", output_format="list"
    )
    if not runs:
        raise SystemExit(f"No MLflow runs for batch {BATCH}. Train the candidates first.")

    # A new batch has one run of each model. The report uses those real recorded values.
    unique = {}
    for run in runs:
        unique.setdefault(run.data.params["model"], run)
    candidates = list(unique.values())
    valid = [r for r in candidates if r.data.metrics.get("p95_latency_ms", 1e9) <= LATENCY_BUDGET_MS]
    if not valid:
        raise SystemExit("No candidate is within the latency budget; check the MLflow results.")
    winner = max(valid, key=lambda r: r.data.metrics["f1"])
    winner_name = winner.data.params["model"]

    rows = []
    for run in candidates:
        name = run.data.params["model"]
        m = run.data.metrics
        slices = {k: v for k, v in m.items() if k.startswith("f1_contract_")}
        weakest = min(slices.items(), key=lambda x: x[1]) if slices else ("not logged", float("nan"))
        slice_name = weakest[0].replace("f1_contract_", "")
        rows.append(
            f"| {name} | {WHY.get(name, 'Candidate for comparison.')} | {m['auc']:.4f} | "
            f"{m['f1']:.4f} | {slice_name}: {weakest[1]:.4f} | "
            f"{m['p95_latency_ms']:.2f} | {m['size_kb']:.1f} | `{run.info.run_id}` |"
        )

    other = [r for r in candidates if r.info.run_id != winner.info.run_id]
    best_other = max(other, key=lambda r: r.data.metrics["f1"]) if other else None
    comparison = ""
    if best_other is not None:
        comparison = (
            f"The next highest F1 was {best_other.data.metrics['f1']:.4f} "
            f"({best_other.data.params['model']}). "
        )

    content = f"""# AI381 Lab 3 - Model selection

## The problem
We predict whether a customer might leave the company (churn). Missing a customer who is likely to
leave means the company may not contact them in time. A false alarm can waste the support team's time.

## My three candidates
I used the same train/test split (80/20, random_state=42, stratified) for a fair comparison.
The scores below come from **MLflow batch `{BATCH}`**, not estimated values.

| Candidate | Why I tried it | AUC | F1 | Weakest contract slice (F1) | p95 (ms) | Size (KB) | MLflow run ID |
|---|---|---:|---:|---|---:|---:|---|
{chr(10).join(rows)}

## Champion decision
I selected **{winner_name}** because it has the highest F1 among the models within the latency budget.
Its F1 is **{winner.data.metrics['f1']:.4f}**, p95 is **{winner.data.metrics['p95_latency_ms']:.2f} ms**,
and its size is **{winner.data.metrics['size_kb']:.1f} KB**. {comparison}
I did not choose only by accuracy: I also checked the weakest contract group, prediction time and memory size.
Trade-off: a model can be better overall and still miss more customers in one small contract group.
I would check this group again with more samples before a real production release.

## Promotion rules
- **p95 latency budget: {LATENCY_BUDGET_MS:.0f} ms.** A single customer request should not wait too long;
  this limit gives some room for the GitHub runner to be slower than my laptop.
- **Minimum F1 gain: {MIN_GAIN:.3f} points.** I do not want to replace a working model for a tiny improvement.
  If the new model is worse, equal, or too slow, the gate says BLOCKED.
- If there is no champion, the best candidate inside the latency budget becomes the first champion.

## Data reproducibility and limitations
I recorded the SHA-256 fingerprint of the training CSV, model parameters, metrics, input/output
signature, Git commit and MLflow run ID. A different data hash means the underlying data changed.
I used one fixed test split; results could change with fresh customer data or different contract group sizes.
"""
    Path("MODEL_SELECTION.md").write_text(content, encoding="utf-8")
    print(f"Updated MODEL_SELECTION.md from {len(candidates)} real MLflow runs.")
    print(f"Selected by F1 within {LATENCY_BUDGET_MS:.0f} ms: {winner_name} ({winner.info.run_id})")


if __name__ == "__main__":
    main()
