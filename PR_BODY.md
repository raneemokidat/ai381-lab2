## Change

Refactor the churn notebook into a training module and validated FastAPI service. Add meaningful tests, a non-root multi-stage Docker image, and PR checks plus main-only build, smoke test, Trivy scan and GHCR publication by commit SHA.

## Verify before merge

- [ ] Local Ruff and pytest pass.
- [ ] Docker answers /health and /predict.
- [ ] Container becomes healthy and runs as UID 10001.
- [ ] PR lint-and-test passes.
- [ ] main requires a PR and passing lint-and-test.

## Verify after merge

- [ ] Main CI including Trivy passes.
- [ ] GHCR tag matches the merged source commit.
- [ ] Actual digest recorded from the run summary.
- [ ] README badge is green.
