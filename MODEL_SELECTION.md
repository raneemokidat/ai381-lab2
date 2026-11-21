# AI381 Lab 3 - Model selection

## The problem
We predict whether a customer might leave the company (churn). Missing a customer who is likely to
leave means the company may not contact them in time. A false alarm can waste the support team's time.

## My three candidates
I used the same train/test split (80/20, random_state=42, stratified) for a fair comparison.
The scores below come from **MLflow batch `local`**, not estimated values.

| Candidate | Why I tried it | AUC | F1 | Weakest contract slice (F1) | p95 (ms) | Size (KB) | MLflow run ID |
|---|---|---:|---:|---|---:|---:|---|
| gradient_boosting | Tests whether boosting improves predictions. | 0.7443 | 0.5227 | two-year: 0.1818 | 1.33 | 141.5 | `e767671638d04ba1a7db1dbf3ff1b356` |
| random_forest | Tests whether combining many trees helps. | 0.7319 | 0.5114 | two-year: 0.0000 | 3.77 | 2304.4 | `365e4f680e41494193930a79049dc1f5` |
| logreg | Simple baseline; usually fast and small. | 0.7918 | 0.5868 | two-year: 0.1818 | 1.25 | 3.6 | `1ca7db2626ee4182a7ef458b6935b6df` |

## Champion decision
I selected **logreg** because it has the highest F1 among the models within the latency budget.
Its F1 is **0.5868**, p95 is **1.25 ms**,
and its size is **3.6 KB**. The next highest F1 was 0.5227 (gradient_boosting).
I did not choose only by accuracy: I also checked the weakest contract group, prediction time and memory size.
Trade-off: a model can be better overall and still miss more customers in one small contract group.
I would check this group again with more samples before a real production release.

## Promotion rules
- **p95 latency budget: 25 ms.** A single customer request should not wait too long;
  this limit gives some room for the GitHub runner to be slower than my laptop.
- **Minimum F1 gain: 0.010 points.** I do not want to replace a working model for a tiny improvement.
  If the new model is worse, equal, or too slow, the gate says BLOCKED.
- If there is no champion, the best candidate inside the latency budget becomes the first champion.

## Data reproducibility and limitations
I recorded the SHA-256 fingerprint of the training CSV, model parameters, metrics, input/output
signature, Git commit and MLflow run ID. A different data hash means the underlying data changed.
I used one fixed test split; results could change with fresh customer data or different contract group sizes.
