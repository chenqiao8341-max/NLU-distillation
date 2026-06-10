# time_if Schema

## Input

- `query` or `question`: 用户原始问题。

## Target

- `publish_date_start`
- `publish_date_end`
- `trial_start_date_start`
- `trial_start_date_end`
- `if_min_value`
- `if_max_value`

## Existing Assets

- Eval data: `/home/qiao/work/nlu-server/eval/时间和if值.json`
- Production sample: `/home/qiao/work/NLU-distillation/nlu-data/100case.jsonl`

## Notes

日期和 IF 值建议保留规则 baseline，用来判断小模型是否真的带来收益。
