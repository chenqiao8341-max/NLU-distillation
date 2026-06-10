# Span ModernBERT Author/Org Business Evaluation

- model_dir: /home/chenqr/work/NLU-distillation/experiments/modernbert_span_ner/author_org
- dataset: /home/chenqr/work/nlu-server/eval/作者和机构.json
- generated_at: 2026-06-09T07:32:01
- total_samples: 111

## Metrics

```json
{
  "author-name-EM": 0.8125,
  "author-name-Partial": 0.8333333333333334,
  "author-name-Precision": 0.8472222222222222,
  "author-name-Recall": 0.8541666666666666,
  "author-name-F1": 0.845138888888889,
  "author-name英文变体-EM": 0.6875,
  "author-name英文变体-Partial": 0.8333333333333334,
  "author-name英文变体-Precision": 0.8621794871794872,
  "author-name英文变体-Recall": 0.8312499999999999,
  "author-name英文变体-F1": 0.8392842111592111,
  "author-institution-EM": 0.7272727272727273,
  "author-institution-Partial": 0.7727272727272727,
  "author-institution-Precision": 0.75,
  "author-institution-Recall": 0.7727272727272727,
  "author-institution-F1": 0.7575757575757577,
  "Average-EM": 0.7457627118644068,
  "Average-Partial": 0.8220338983050848,
  "Average-F1": 0.8264319954997921,
  "Null-accuracy": 0.9429824561403509
}
```

## Output Files

- details_jsonl: `/home/chenqr/work/NLU-distillation/reports/modernbert_span_ner/author_org_business_eval_spanbert_20260609_details.jsonl`
- details_csv: `/home/chenqr/work/NLU-distillation/reports/modernbert_span_ner/author_org_business_eval_spanbert_20260609_details.csv`

## Notes

- `raw_output` is structured BERT span output, not generated text.
- `parsed_output` is the final business JSON fields.