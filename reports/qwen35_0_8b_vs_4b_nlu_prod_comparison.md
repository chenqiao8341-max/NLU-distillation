# Qwen3.5 0.8B vs 4B NLU prod comparison

- 4B `作者和机构` was rerun after increasing generation budget and fixing parser recovery for complete scalar fields in truncated JSON-prefix cases.
- This pass scanned all five merged 4B reports for thinking markers, `finish_reason=length`, invalid JSON/XML shape, and token ceilings.
- Clear truncation/thinking residue was found only in old `机构和国家` and `时间和if值` reports, so those two tasks were re-evaluated and overwritten with `max_tokens=256`, `--stop-after-first-json`, and thinking disabled.

## Overall metrics

| task | samples_0.8B | samples_4B | 4B_errors | F1_0.8B | F1_4B | delta_F1 | EM_0.8B | EM_4B | delta_EM | Null_0.8B | Null_4B | 4B_thinking | 4B_length | 4B_max_tokens | 4B_nonempty_gold_empty_pred |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 作者和机构 | 111 | 111 | 0 | 0.3704 | 0.7933 | 0.4229 | 0.2214 | 0.5182 | 0.2968 | 0.8860 | 0.9781 | 0 | 0 | 188 | 2 |
| data_type | 310 | 310 | 0 | 0.7356 | 0.8600 | 0.1244 | 0.7241 | 0.8600 | 0.1359 | 0.9582 | 0.9886 | 0 | 0 | 10 | 4 |
| 机构和国家 | 235 | 235 | 0 | 0.1240 | 0.6522 | 0.5282 | 0.1198 | 0.6304 | 0.5106 | 0.5182 | 0.9636 | 0 | 0 | 29 | 0 |
| 时间和if值 | 235 | 235 | 0 | 0.2410 | 0.7273 | 0.4862 | 0.1928 | 0.5545 | 0.3617 | 0.6935 | 0.9976 | 0 | 0 | 40 | 9 |
| topic和keywords | 183 | 183 | 0 | 0.5019 | 0.4406 | -0.0613 | 0.3579 | 0.2813 | -0.0766 | 0.0000 | 0.3043 | 0 | 0 | 119 | 54 |
| 五类宏平均 | 1074 | 1074 | 0 | 0.3946 | 0.6947 | 0.3001 | 0.3232 | 0.5689 | 0.2457 | 0.6112 | 0.8464 | 0 | 0 | 188 | 69 |

## Output-shape scan

| task | 4B JSON-like outputs | 4B XML-like outputs | 4B invalid shape | 4B length finishes | 4B thinking | note |
| --- | --- | --- | --- | --- | --- | --- |
| 作者和机构 | 111 | 0 | 0 | 0 | 0 | Expected JSON. |
| data_type | 310 | 0 | 0 | 0 | 0 | Expected JSON. |
| 机构和国家 | 235 | 0 | 0 | 0 | 0 | Expected JSON. |
| 时间和if值 | 235 | 0 | 0 | 0 | 0 | Expected JSON. |
| topic和keywords | 100 | 83 | 0 | 0 | 0 | Expected XML, but model emitted mixed JSON/XML; evaluator parsed both. |

## Report paths

- 作者和机构: 0.8B `reports/merged/qwen35_0_8b_nlu_prod_author_org.json`; 4B `reports/merged/qwen35_4b_nlu_prod_author_org.json`
- data_type: 0.8B `reports/merged/qwen35_0_8b_nlu_prod_data_type.json`; 4B `reports/merged/qwen35_4b_nlu_prod_data_type.json`
- 机构和国家: 0.8B `reports/merged/qwen35_0_8b_nlu_prod_org_country.json`; 4B `reports/merged/qwen35_4b_nlu_prod_org_country.json`
- 时间和if值: 0.8B `reports/merged/qwen35_0_8b_nlu_prod_time_if.json`; 4B `reports/merged/qwen35_4b_nlu_prod_time_if.json`
- topic和keywords: 0.8B `reports/merged/qwen35_0_8b_nlu_prod_topic_keywords.json`; 4B `reports/merged/qwen35_4b_nlu_prod_topic_keywords.json`

## Notes

- Current five 4B reports all have zero request errors, zero thinking markers, zero `finish_reason=length`, and no invalid JSON/XML shape detected by the scan.
- `topic和keywords` still has mixed JSON/XML output style despite being parseable; this is a format-following issue rather than a truncation issue.
