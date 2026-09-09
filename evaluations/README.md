# SQLBot Adaptive evaluation harness

This directory keeps the question set separate from generated results. A run never treats SQL text equality as the main correctness signal: it compares outcome, metric/version provenance, columns and result rows with configurable ordering and numeric tolerance.

`cases.example.yaml` is a synthetic schema example. Copy it to `cases.local.yaml` for real, desensitized business cases. Keep the holdout split away from prompts, terminology, SQL samples, memories and tuning decisions.

```powershell
Set-Location D:\python\SQLBot-adaptive\backend
uv run --no-sync python ..\evaluations\run.py `
  --cases ..\evaluations\cases.example.yaml `
  --actual ..\evaluations\results.example.json `
  --report ..\evaluations\reports\example.md
```

The first real baseline still needs a read-only business datasource, a frozen data snapshot and questions reviewed by the metric owner. Store credentials outside this directory.

## Case contract

- `split`: `dev` may guide implementation; `holdout` is only for acceptance.
- `category`: use stable failure categories such as `metric`, `table_selection`, `sql`, `permission`, `context`, `ambiguity` and `refusal`.
- `expected.outcome`: `success`, `refusal` or `error`.
- `expected.metric`: optional required metric code and version.
- `expected.rows`: JSON-like records or arrays. Set `ordered: true` only when order is part of the answer.
- `float_tolerance`: absolute numeric tolerance for this case.

The adapter that calls a configured SQLBot instance will be added when a test model and datasource are available. Until then, captured results can be compared deterministically with this harness.
