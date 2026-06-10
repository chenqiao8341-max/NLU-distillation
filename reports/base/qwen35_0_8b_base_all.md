# qwen-3.5-0.8b local NLU evaluation

- base_url: http://127.0.0.1:8000/v1
- generated_at: 2026-06-08T13:55:17
- total_samples: 1074

## Overall

```json
{
  "Average-EM": 0.15328134970136648,
  "Average-Partial": 0.19390445537748127,
  "Average-F1": 0.20371117136491285,
  "Null-accuracy": 0.19852732793522265
}
```

## 作者和机构

- samples: 111

```json
{
  "author-institution-EM": 0.15306122448979592,
  "author-institution-Partial": 0.16326530612244897,
  "author-institution-Precision": 0.14285714285714285,
  "author-institution-Recall": 0.14285714285714285,
  "author-institution-F1": 0.14285714285714285,
  "author-name-EM": 0.8260869565217391,
  "author-name-Partial": 0.8695652173913043,
  "author-name-Precision": 0.8260869565217391,
  "author-name-Recall": 0.8260869565217391,
  "author-name-F1": 0.8260869565217391,
  "author-name英文变体-EM": 0.0,
  "author-name英文变体-Partial": 0.0,
  "author-name英文变体-Precision": 0.5111111111111111,
  "author-name英文变体-Recall": 0.14987654320987653,
  "author-name英文变体-F1": 0.22783068783068786,
  "Average-EM": 0.2804232804232804,
  "Average-Partial": 0.2962962962962963,
  "Average-F1": 0.3293776769967246,
  "Null-accuracy": 0.631578947368421
}
```

## 机构和国家

- samples: 235

```json
{
  "国家-EM": 0.04680851063829787,
  "国家-Partial": 0.04680851063829787,
  "国家-Precision": 0.04680851063829787,
  "国家-Recall": 0.04680851063829787,
  "国家-F1": 0.04680851063829787,
  "机构名称-EM": 0.06930693069306931,
  "机构名称-Partial": 0.0891089108910891,
  "机构名称-Precision": 0.08168316831683169,
  "机构名称-Recall": 0.07541254125412541,
  "机构名称-F1": 0.07708628005657708,
  "Average-EM": 0.057208237986270026,
  "Average-Partial": 0.06636155606407322,
  "Average-F1": 0.06080418437397843,
  "Null-accuracy": 0.075
}
```

## 时间和if值

- samples: 235

```json
{
  "filter-end-datetime-EM": 0.042735042735042736,
  "filter-end-datetime-Partial": 0.042735042735042736,
  "filter-end-datetime-Precision": 0.042735042735042736,
  "filter-end-datetime-Recall": 0.042735042735042736,
  "filter-end-datetime-F1": 0.042735042735042736,
  "filter-end-if-EM": 0.0,
  "filter-end-if-Partial": 0.0,
  "filter-end-if-Precision": 0.0,
  "filter-end-if-Recall": 0.0,
  "filter-end-if-F1": 0.0,
  "filter-start-datetime-EM": 0.07692307692307693,
  "filter-start-datetime-Partial": 0.07692307692307693,
  "filter-start-datetime-Precision": 0.22863247863247863,
  "filter-start-datetime-Recall": 0.22863247863247863,
  "filter-start-datetime-F1": 0.22863247863247863,
  "filter-start-if-EM": 0.029914529914529916,
  "filter-start-if-Partial": 0.029914529914529916,
  "filter-start-if-Precision": 0.029914529914529916,
  "filter-start-if-Recall": 0.029914529914529916,
  "filter-start-if-F1": 0.029914529914529916,
  "Average-EM": 0.04985754985754986,
  "Average-Partial": 0.04985754985754986,
  "Average-F1": 0.10042735042735043,
  "Null-accuracy": 0.2860576923076923
}
```

## data_type

- samples: 310

```json
{
  "data-type-EM": 0.11935483870967742,
  "data-type-Partial": 0.12258064516129032,
  "data-type-Precision": 0.12258064516129032,
  "data-type-Recall": 0.12096774193548387,
  "data-type-F1": 0.12150537634408601,
  "Average-EM": 0.11935483870967742,
  "Average-Partial": 0.12258064516129032,
  "Average-F1": 0.12150537634408601,
  "Null-accuracy": 0.0
}
```

## topic和keywords

- samples: 183

```json
{
  "keywords-EM": 0.15846994535519127,
  "keywords-Partial": 0.3333333333333333,
  "keywords-Precision": 0.3591898690259346,
  "keywords-Recall": 0.3058808222742649,
  "keywords-F1": 0.3048234552332913,
  "topics-EM": 0.36065573770491804,
  "topics-Partial": 0.5355191256830601,
  "topics-Precision": 0.4703670539253953,
  "topics-Recall": 0.6211293260473588,
  "topics-F1": 0.5080590821315584,
  "Average-EM": 0.25956284153005466,
  "Average-Partial": 0.4344262295081967,
  "Average-F1": 0.40644126868242486,
  "Null-accuracy": 0.0
}
```
