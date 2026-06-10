# trial_slots Schema

## Input

- `query`: 用户原始问题。
- `data_sources`: 数据源列表，通常包含 `TRIAL` 时更可能有临床试验槽位。

## Target

- `trial_acronyms`
- `trial_diseases`
- `trial_diseases_en`
- `trial_interventions`
- `trial_interventions_en`
- `trial_locations`
- `trial_locations_en`
- `trial_outcome_measure`
- `trial_outcome_measure_en`
- `trial_phases`
- `trial_sponsors`
- `trial_sponsors_en`
- `trial_study_types`

## Notes

建议从 `data_sources` 包含 `TRIAL` 的子集开始训练和评估。
