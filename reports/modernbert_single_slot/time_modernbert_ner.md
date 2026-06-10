# ModernBERT NER - time

- model_path: /home/qiao/models/BERT/ModernBERT-base
- model_dir: /home/qiao/work/NLU-distillation/experiments/modernbert_single_slot/time
- data_dir: /home/qiao/work/NLU-distillation/data/processed_single/time/bio
- generated_at: 2026-06-10T16:40:55
- train_samples: 4000
- valid_samples: 500
- test_samples: 200

## Test Metrics

```json
{
  "token_accuracy": 0.976737114185799,
  "entity_precision": 0.8117647058823529,
  "entity_recall": 0.5847457627118644,
  "entity_f1": 0.6798029556650246,
  "entity_true_count": 118,
  "entity_pred_count": 85,
  "entity_tp_count": 69,
  "label_list": [
    "O",
    "B-TIME",
    "I-TIME"
  ],
  "by_entity": {
    "TIME": {
      "tp": 69,
      "pred": 85,
      "true": 118,
      "precision": 0.8117647058823529,
      "recall": 0.5847457627118644,
      "f1": 0.6798029556650246
    }
  }
}
```

## Test Metrics By Source

```json
{
  "eval_time_if": {
    "token_accuracy": 0.976737114185799,
    "entity_precision": 0.8117647058823529,
    "entity_recall": 0.5847457627118644,
    "entity_f1": 0.6798029556650246,
    "entity_true_count": 118,
    "entity_pred_count": 85,
    "entity_tp_count": 69,
    "label_list": [
      "O",
      "B-TIME",
      "I-TIME"
    ],
    "by_entity": {
      "TIME": {
        "tp": 69,
        "pred": 85,
        "true": 118,
        "precision": 0.8117647058823529,
        "recall": 0.5847457627118644,
        "f1": 0.6798029556650246
      }
    }
  }
}
```
