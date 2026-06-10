# ModernBERT NER - impact_factor

- model_path: /home/qiao/models/BERT/ModernBERT-base
- model_dir: /home/qiao/work/NLU-distillation/experiments/modernbert_single_slot/impact_factor
- data_dir: /home/qiao/work/NLU-distillation/data/processed_single/impact_factor/bio
- generated_at: 2026-06-10T16:40:59
- train_samples: 4000
- valid_samples: 500
- test_samples: 200

## Test Metrics

```json
{
  "token_accuracy": 0.9966550098829253,
  "entity_precision": 0.0,
  "entity_recall": 0.0,
  "entity_f1": 0.0,
  "entity_true_count": 9,
  "entity_pred_count": 0,
  "entity_tp_count": 0,
  "label_list": [
    "O",
    "B-IMPACT_FACTOR",
    "I-IMPACT_FACTOR"
  ],
  "by_entity": {
    "IMPACT_FACTOR": {
      "tp": 0,
      "pred": 0,
      "true": 9,
      "precision": 0.0,
      "recall": 0.0,
      "f1": 0.0
    }
  }
}
```

## Test Metrics By Source

```json
{
  "eval_time_if": {
    "token_accuracy": 0.9966550098829253,
    "entity_precision": 0.0,
    "entity_recall": 0.0,
    "entity_f1": 0.0,
    "entity_true_count": 9,
    "entity_pred_count": 0,
    "entity_tp_count": 0,
    "label_list": [
      "O",
      "B-IMPACT_FACTOR",
      "I-IMPACT_FACTOR"
    ],
    "by_entity": {
      "IMPACT_FACTOR": {
        "tp": 0,
        "pred": 0,
        "true": 9,
        "precision": 0.0,
        "recall": 0.0,
        "f1": 0.0
      }
    }
  }
}
```
