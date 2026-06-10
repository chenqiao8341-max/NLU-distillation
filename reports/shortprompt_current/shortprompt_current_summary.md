# Short Prompt Current Eval Summary

- generated_at: 2026-06-10T17:37:29
- dataset_dir: `/home/qiao/work/nlu-server/eval`
- evaluator: `scripts/eval_local_openai_shortprompt.py`
- samples_per_report: 200

| task | model | Average-F1 | Average-EM | Average-Partial | Null-accuracy | report |
|---|---:|---:|---:|---:|---:|---|
| 作者和机构 | qwen35-0.8b-author-org | 0.2794 | 0.1084 | 0.1647 | 0.9512 | `qwen35_0_8b_nlu_prod_author_org_shortprompt_current.json` |
| 作者和机构 | qwen35-4b-author-org | 0.8391 | 0.5492 | 0.8730 | 0.9648 | `qwen35_4b_nlu_prod_author_org_shortprompt_current.json` |
| data_type | qwen35-0.8b-data-type | 0.8350 | 0.8235 | 0.8235 | 0.9800 | `qwen35_0_8b_nlu_prod_data_type_shortprompt_current.json` |
| data_type | qwen35-4b-data-type | 0.7217 | 0.7100 | 0.7200 | 1.0000 | `qwen35_4b_nlu_prod_data_type_shortprompt_current.json` |
| 机构和国家 | qwen35-0.8b-org-country | 0.6435 | 0.6250 | 0.6458 | 0.8533 | `qwen35_0_8b_nlu_prod_org_country_shortprompt_current.json` |
| 机构和国家 | qwen35-4b-org-country | 0.7218 | 0.6894 | 0.7197 | 0.8933 | `qwen35_4b_nlu_prod_org_country_shortprompt_current.json` |
| 时间和if值 | qwen35-0.8b-time-if | 0.7697 | 0.7377 | 0.7377 | 0.9883 | `qwen35_0_8b_nlu_prod_time_if_shortprompt_current.json` |
| 时间和if值 | qwen35-4b-time-if | 0.8227 | 0.7983 | 0.7983 | 0.9927 | `qwen35_4b_nlu_prod_time_if_shortprompt_current.json` |
| topic和keywords | qwen35-0.8b-topic-keywords | 0.1992 | 0.1250 | 0.2147 | 0.4211 | `qwen35_0_8b_nlu_prod_topic_keywords_shortprompt_current.json` |
| topic和keywords | qwen35-4b-topic-keywords | 0.0439 | 0.0288 | 0.0625 | 0.9187 | `qwen35_4b_nlu_prod_topic_keywords_shortprompt_current.json` |
