# Portfolio roadmap

## P0: resolve before making the repository public

- Confirm that the Commax-derived notebook data and outputs are approved for public use. If not, replace them with an anonymized dataset and remove sensitive notebook outputs and Git history.
- Make a clean clone produce a usable forecast. Provide a small pre-trained demo model or a deterministic bootstrap command and test it end to end.
- Validate prediction inputs: positive IDs, `start_date <= end_date`, and a bounded forecast horizon.
- Fix the chart confidence interval so it fills only the lower-to-upper range.
- Promote models by an explicit MLflow alias or stage after evaluation instead of serving the latest run.

## P1: prove engineering and ML quality

- Add rolling-origin backtests and compare Prophet with seasonal-naive and moving-average baselines.
- Report WAPE or MASE, RMSE, interval coverage, and results by SKU/store segment.
- Align offline evaluation inputs with the production API contract, especially promotion schedules.
- Lock Python dependencies and record the dataset hash, model signature, input example, parameters, and code revision in MLflow.
- Add prediction API, validation, MLflow failure, and model-loading integration tests.
- Add frontend lint, build, unit, accessibility, and browser smoke tests to CI.
- Add container health checks, readiness checks, restart policies, non-root users, and immutable image tags.
- Monitor forecast error, drift, data quality, model version, p95 latency, and error rate with alerts.

## P2: make the portfolio easy to evaluate

- Add a 30-second demo GIF, architecture diagram, live demo link, CI badge, and benchmark table to the README.
- Explain the business decision supported by the forecast and quantify the expected operational impact.
- Show historical demand and forecast together, expose model version and generated time, and provide a table or CSV alternative to the chart.
- Replace manual API types with OpenAPI-generated types and runtime response validation.
- Add a model card and data card covering intended use, limitations, leakage risks, and data licensing.

## Completion criteria

- A reviewer can clone the repository and get one successful prediction in under ten minutes.
- CI blocks merges when backend tests, frontend checks, image builds, or dependency scans fail.
- Every reported model metric is reproducible from a versioned dataset and time-based split.
- No private or employer-owned data is present without explicit permission.
