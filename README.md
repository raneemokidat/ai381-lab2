# AI381 Lab 2 — Churn service

[![CI](https://github.com/raneemokidat/ai381-lab2/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/raneemokidat/ai381-lab2/actions/workflows/ci.yml)

## Start with one command

From the repository root, with Docker Desktop running:

```bash
docker compose up --build -d
```

Open http://localhost:8000/docs. Training runs during the build; no model file needs to be downloaded. Wait for startup before testing:

```bash
curl -fsS http://localhost:8000/health
curl -fsS http://localhost:8000/predict -H 'Content-Type: application/json' --data @sample_request.json
docker compose ps
docker compose exec api id
docker compose down
```

Health returns `{"status":"ok"}`. Prediction returns `{"churn_probability": <number from 0 to 1>}`. Invalid input returns HTTP 422.

## Local checks

Use Python 3.12. Windows users should use WSL2 Ubuntu.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m ruff check .
python -m pytest -q
python -m src.train.train
python -m uvicorn src.app.main:app --port 8000
```

Stop Uvicorn with Ctrl+C. Tests train the model once using a session fixture and start the FastAPI lifespan for each client.

## Model and API

The Lab 1 pipeline uses StandardScaler, OneHotEncoder and LogisticRegression on churn_v2.csv. The split is stratified 80/20 with seed 42. Training prints held-out F1 and ROC AUC. The model is recreated with the current project libraries, avoiding an old incompatible serialized model.

| Input | Validation |
| --- | --- |
| tenure_months | Integer, at least 0 |
| monthly_fee | Finite number, at least 0 |
| contract | month-to-month, one-year, two-year |
| internet_service | dsl, fiber, none |
| support_calls | Integer, at least 0 |

All fields are required; unexpected fields are rejected. The API uses monthly_fee from v2, rather than monthly_charges from v1. Valid schema does not guarantee an input is within the model's training distribution.

## Tests

The suite checks the health contract, model loading and probability shape, prediction contract, each missing field, incorrect types and categories, negative values, extra fields, a zero-valued edge case, and repeated predictions compared with the loaded model. There are 21 collected cases including parameterization. Determinism means identical input and loaded model produce identical responses; it does not promise bitwise equality across every platform.

## Container

The builder downloads wheels and trains the model. The runtime contains the API and model, without training data or tests. Both stages use the same exact Python patch, OS variant and multi-platform image digest. The final process runs as UID/GID 10001. HEALTHCHECK queries /health with Python's standard library, so curl is unnecessary inside the image. A missing model fails application startup. Health verifies availability, not drift or predictive quality.

## CI and GHCR

PRs run lint-and-test. Main pushes run that check and then build-scan-push: build, test both endpoints in the running image, verify non-root UID, scan with Trivy, and push to GHCR tagged with the full source commit SHA. Direct third-party actions are pinned to full commit SHAs. No manually stored token is needed; GitHub supplies GITHUB_TOKEN with packages: write.

Trivy fails on fixable HIGH/CRITICAL findings; unfixed findings are excluded from this gate. This is a coverage trade-off, not a clean bill of health. Resolve reported findings with dependency/base updates and rerun; do not disable the gate. Pinned dependencies still require ongoing maintenance.

After a successful main run, Actions → run → Summary shows the actual image tag and digest. A commit tag identifies source; the digest identifies exact image bytes. No digest or green badge can be supplied before a real successful publication.

```text
ghcr.io/raneemokidat/ai381-lab2:<full-commit-sha>
ghcr.io/raneemokidat/ai381-lab2@sha256:<actual-digest>
```

## Repository setup

Run `python scripts/configure.py raneemokidat` before committing to configure the badge and image examples. Follow START_HERE_AR.md to create the public repository, open a PR and protect main before merging. The badge is live and turns green only after successful CI. Set the GHCR package public if unauthenticated assessor pulls are needed; repository visibility alone may not set package visibility.

## Trade-offs

Training inside the build is simple for this small model, but slower than promoting a tracked artifact. Validation catches malformed input, not model drift. Rounded probabilities preserve the Lab 1 response but lose precision. Monitoring, authentication, experiment tracking and model promotion belong to later work.
