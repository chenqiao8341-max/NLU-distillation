# ModernBERT NER - author

- model_path: /home/qiao/models/BERT/ModernBERT-base
- model_dir: /home/qiao/work/NLU-distillation/experiments/modernbert_single_slot/author
- data_dir: /home/qiao/work/NLU-distillation/data/processed_single/author/bio
- generated_at: 2026-06-10T16:40:41
- train_samples: 3176
- valid_samples: 396
- test_samples: 200

## Test Metrics

```json
{
  "token_accuracy": 0.9935359888190077,
  "entity_precision": 0.9106382978723404,
  "entity_recall": 0.9184549356223176,
  "entity_f1": 0.9145299145299145,
  "entity_true_count": 233,
  "entity_pred_count": 235,
  "entity_tp_count": 214,
  "label_list": [
    "O",
    "B-AUTHOR",
    "I-AUTHOR"
  ],
  "by_entity": {
    "AUTHOR": {
      "tp": 214,
      "pred": 235,
      "true": 233,
      "precision": 0.9106382978723404,
      "recall": 0.9184549356223176,
      "f1": 0.9145299145299145
    }
  }
}
```

## Test Metrics By Source

```json
{
  "eval_author_org": {
    "token_accuracy": 0.9935359888190077,
    "entity_precision": 0.9106382978723404,
    "entity_recall": 0.9184549356223176,
    "entity_f1": 0.9145299145299145,
    "entity_true_count": 233,
    "entity_pred_count": 235,
    "entity_tp_count": 214,
    "label_list": [
      "O",
      "B-AUTHOR",
      "I-AUTHOR"
    ],
    "by_entity": {
      "AUTHOR": {
        "tp": 214,
        "pred": 235,
        "true": 233,
        "precision": 0.9106382978723404,
        "recall": 0.9184549356223176,
        "f1": 0.9145299145299145
      }
    }
  }
}
```
