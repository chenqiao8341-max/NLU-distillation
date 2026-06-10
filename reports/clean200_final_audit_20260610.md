# clean200 0.8B / 4B Final Audit - 2026-06-10

## Run completion

- Remote 0.8B five-task train/merge/eval completed. Latest synced reports are in `/home/qiao/work/NLU-distillation/reports/clean200_remote_0_8b/`.
- Local 4B five-task train/merge/eval completed. Latest reports are in `/home/qiao/work/NLU-distillation/reports/clean200/merged/`.
- Remote high-max targeted re-eval completed for `author_org` and `org_country`; merged dirs were deleted after eval.
- Local high-max targeted re-eval completed for `author_org` and `topic_keywords`.
- No current local or remote `serve_transformers_openai`, `eval_local_openai`, or pipeline processes remain.

## Report freshness

Remote 0.8B:
- `author_org`: 2026-06-10 09:43:27 local synced mtime, high-max re-eval.
- `org_country`: 2026-06-10 09:45:13 local synced mtime, high-max re-eval.
- `data_type`: 2026-06-10 08:02:07.
- `time_if`: 2026-06-10 08:06:20.
- `topic_keywords`: 2026-06-10 08:08:34.

Local 4B:
- `author_org`: 2026-06-10 10:02:28, high-max re-eval.
- `topic_keywords`: 2026-06-10 10:09:34, high-max re-eval.
- `data_type`: 2026-06-10 08:51:40.
- `org_country`: 2026-06-10 08:55:39.
- `time_if`: 2026-06-10 09:04:26.

## JSON/output audit

All 10 reports parse as JSON and contain `total_samples=200` with 200 samples.
No empty raw outputs, no `<think>`, no markdown code fences, and no long non-JSON garbage prefixes were found.
Current serve logs show no MISSING/UNEXPECTED architecture mismatch and no Traceback/Exception/error in current eval logs.

Residual model-output issues after high-max re-eval:

- 4B `author_org`: 18/200 samples still finish with `length`; 182/200 raw outputs are directly valid JSON.
- 0.8B `author_org`: 27/200 samples still finish with `length`; 172/200 raw outputs are directly valid JSON.
- 4B `topic_keywords`: 1/200 sample still finishes with `length`; 199/200 raw outputs are directly valid JSON.
- 0.8B `org_country`: 1/200 sample still finishes with `length`; 199/200 raw outputs are directly valid JSON.

The service passes request `max_tokens` through to `generate(max_new_tokens=req.max_tokens)`, so these residual truncations are not caused by the evaluator ignoring the max-token parameter. Manual sample inspection shows real model-output pathologies: repeated `author_name英文变体` values in `author_org`, repeated keys/content in one `topic_keywords` sample, and one `org_country` sample with extra `原因/reason` text.

## Paths

- Local 4B reports: `/home/qiao/work/NLU-distillation/reports/clean200/merged/`
- Synced remote 0.8B reports: `/home/qiao/work/NLU-distillation/reports/clean200_remote_0_8b/`
- Local manual high-max logs: `/home/qiao/work/NLU-distillation/experiments/logs/clean200/4b/manual_rerun_highmax/`
- Remote manual high-max logs: `/home/chenqr/work/NLU-distillation/experiments/logs/clean200/0.8b/manual_rerun_highmax/`
