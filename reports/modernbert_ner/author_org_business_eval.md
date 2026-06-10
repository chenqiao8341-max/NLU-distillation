# ModernBERT Author/Org Business Evaluation

- model_dir: /home/chenqr/work/nlu-bert/outputs/modernbert-author-org-ner
- dataset: /home/chenqr/work/nlu-server/eval/作者和机构.json
- generated_at: 2026-06-09T03:21:54
- total_samples: 111

## Metrics

```json
{
  "author-name-EM": 0.4375,
  "author-name-Partial": 0.6458333333333334,
  "author-name-Precision": 0.4763888888888889,
  "author-name-Recall": 0.5,
  "author-name-F1": 0.48194444444444445,
  "author-name英文变体-EM": 0.06818181818181818,
  "author-name英文变体-Partial": 0.11363636363636363,
  "author-name英文变体-Precision": 0.1534090909090909,
  "author-name英文变体-Recall": 0.12386363636363637,
  "author-name英文变体-F1": 0.13465007215007213,
  "author-institution-EM": 0.3333333333333333,
  "author-institution-Partial": 0.625,
  "author-institution-Precision": 0.3958333333333333,
  "author-institution-Recall": 0.4166666666666667,
  "author-institution-F1": 0.40277777777777773,
  "Average-EM": 0.27586206896551724,
  "Average-Partial": 0.4396551724137931,
  "Average-F1": 0.3338327859879584,
  "Null-accuracy": 0.9517543859649122
}
```

## Notes

- This evaluates final business fields on `nlu-server/eval/作者和机构.json`, not BIO token labels.
- `author_name英文变体` is generated after BERT extracts `author_name`.
- Empty-vs-empty cases contribute only to `Null-accuracy`; content metrics exclude both-empty cases.
