# Public dashboard data

This directory contains the minimal derived dataset required for the public Demand Signal dashboard. It is limited to the 20 items selected by cumulative shipment volume and the five columns used by the UI: item code, item name, demand pattern, month, and shipment value.

The original source CSV and its additional fields are intentionally excluded. `commax_evaluation.json` is the schema-versioned three-fold, six-month rolling validation result used by the dashboard. Demand patterns are recalculated using only each fold's training history. Its 80% and 90% prediction intervals use split conformal absolute residuals from only the three origins preceding each evaluated origin.
