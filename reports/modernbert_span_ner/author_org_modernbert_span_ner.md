# ModernBERT Span NER - author_org

- model_path: /home/chenqr/models/BERT/ModernBERT-base
- model_dir: /home/chenqr/work/NLU-distillation/experiments/modernbert_span_ner/author_org
- span_dir: /home/chenqr/work/NLU-distillation/data/processed/author_org/span
- generated_at: 2026-06-09T06:51:58
- train_rows: 3176
- valid_rows: 396
- test_rows: 396
- max_length: 512
- stride: 128

## Span Metrics

```json
{
  "entity_precision": 0.43568464730290457,
  "entity_recall": 0.6092843326885881,
  "entity_f1": 0.5080645161290323,
  "entity_true_count": 517,
  "entity_pred_count": 723,
  "entity_tp_count": 315,
  "by_entity": {
    "AUTHOR": {
      "tp": 254,
      "pred": 603,
      "true": 447,
      "precision": 0.42122719734660036,
      "recall": 0.5682326621923938,
      "f1": 0.4838095238095239
    },
    "INSTITUTION": {
      "tp": 61,
      "pred": 120,
      "true": 70,
      "precision": 0.5083333333333333,
      "recall": 0.8714285714285714,
      "f1": 0.6421052631578947
    }
  }
}
```

## Field Metrics

```json
{
  "author_name": {
    "tp": 389,
    "pred": 562,
    "true": 442,
    "exact_match": 267,
    "rows": 396,
    "precision": 0.6921708185053381,
    "recall": 0.8800904977375565,
    "f1": 0.7749003984063745,
    "exact_match_rate": 0.6742424242424242
  },
  "author_institution": {
    "tp": 51,
    "pred": 95,
    "true": 62,
    "exact_match": 353,
    "rows": 396,
    "precision": 0.5368421052631579,
    "recall": 0.8225806451612904,
    "f1": 0.6496815286624203,
    "exact_match_rate": 0.8914141414141414
  },
  "macro_f1": 0.7122909635343975
}
```