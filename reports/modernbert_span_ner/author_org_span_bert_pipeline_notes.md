# 作者和机构 Span-BERT 数据与推理说明

本文说明当前 `author_org` span 数据集、ModernBERT 训练目标、BERT 原始推理输出，以及业务字段后处理方式。

相关脚本：

- `scripts/prepare_author_org_span.py`
- `scripts/train_eval_modernbert_author_org_span.py`
- `scripts/eval_author_org_span_bert_business.py`

相关产物：

- span 数据集：`data/processed/author_org/span/`
- 训练模型：`experiments/modernbert_span_ner/author_org/`
- test 集报告：`reports/modernbert_span_ner/author_org_modernbert_span_ner.md`
- 业务集报告：`reports/modernbert_span_ner/author_org_business_eval_spanbert_20260609.md`
- 业务集明细：`reports/modernbert_span_ner/author_org_business_eval_spanbert_20260609_details.jsonl`

## Span 数据集具体怎么构造的

当前 span 数据集是从已有字符级 BIO 数据转换出来的，来源是：

```text
data/processed/author_org/bio/
```

输出到：

```text
data/processed/author_org/span/
```

每条 BIO 原始数据包含：

```json
{
  "text": "龚建平教授发表的rct研究最终结论是什么",
  "char_labels": ["B-AUTHOR", "I-AUTHOR", "I-AUTHOR", "..."],
  "author_name": "龚建平",
  "author_name英文变体": "...",
  "author_institution": ""
}
```

转换脚本按字符标签扫描 `char_labels`：

- 遇到 `B-AUTHOR` 开始一个作者 span。
- 连续的 `I-AUTHOR` 并入同一个作者 span。
- 遇到 `B-INSTITUTION` 开始一个机构 span。
- 连续的 `I-INSTITUTION` 并入同一个机构 span。
- 遇到 `O` 或新实体类型时关闭当前 span。

转换后的 span 数据格式：

```json
{
  "text": "龚建平教授发表的rct研究最终结论是什么",
  "task": "作者和机构",
  "entities": [
    {
      "start": 0,
      "end": 3,
      "text": "龚建平",
      "label": "AUTHOR",
      "field": "author_name"
    }
  ],
  "author_name": "龚建平",
  "author_name英文变体": "...",
  "author_institution": ""
}
```

字段含义：

- `start`：实体在原文中的字符起始位置，左闭。
- `end`：实体在原文中的字符结束位置，右开。
- `text`：`text[start:end]` 的原文片段。
- `label`：模型学习的实体类型，目前是 `AUTHOR` 或 `INSTITUTION`。
- `field`：实体对应的业务字段，`AUTHOR -> author_name`，`INSTITUTION -> author_institution`。

`author_name英文变体` 不作为 BERT 模型直接抽取目标。它保留在数据里用于业务输出对齐，实际推理时由作者名后处理规则生成。

当前统计：

```text
all rows: 3968
positive rows: 1956
empty rows: 2012
AUTHOR spans: 3508
INSTITUTION spans: 590
```

其中有 661 个实体起始位置在第 256 个字符之后，所以新版训练使用 `max_length=512` 和 `stride=128`，避免旧 256 截断直接丢掉长文本后半段实体。

## BERT 模型从数据集学到什么

虽然数据集的 canonical 格式是 span，但当前 ModernBERT 训练仍使用 token classification head。训练时会把 span 临时转换成 token 级 BIO 标签。

模型标签列表：

```json
[
  "O",
  "B-AUTHOR",
  "I-AUTHOR",
  "B-INSTITUTION",
  "I-INSTITUTION"
]
```

训练时的转换流程：

1. 从 `entities` 还原字符级标签：
   - `AUTHOR` span 转成 `B-AUTHOR/I-AUTHOR`
   - `INSTITUTION` span 转成 `B-INSTITUTION/I-INSTITUTION`
   - 其他字符为 `O`

2. 用 ModernBERT tokenizer 对 `text` 分词，并拿到每个 token 对应的原文 offset。

3. 对每个 token，根据它覆盖的字符范围取标签：
   - 特殊 token 或空 offset 标记为 `-100`，不参与 loss。
   - token 覆盖范围里如果存在非 `O` 字符标签，就用该实体标签。
   - 否则标为 `O`。

4. 长文本启用 overflow window：
   - `max_length=512`
   - `stride=128`
   - 同一条 query 可能被切成多个重叠窗口参与训练。

因此，BERT 实际学到的是：

- 每个 token 是否属于作者、机构或背景文本。
- 作者/机构在 query 中常见的上下文模式，例如“某某教授”“某医院某医生”“某大学某课题组”。
- 中英文混合作者名、中文机构名、参考文献式英文作者名等 token 边界模式。

它没有学习生成 JSON，也没有学习直接生成英文变体。BERT 输出的是 token 标签，最终 JSON 由解码和后处理得到。

## BERT 模型对于测试集的原始输出是什么样的

BERT 和大语言模型的 `raw_output` 不一样。

大语言模型通常输出一段文本，例如：

```json
{
  "raw_output": "{\"author_name\":\"龚建平\", ...}",
  "parsed_output": {
    "author_name": "龚建平"
  }
}
```

BERT token classification 不生成文本。它对每个 token 输出一个分类 logits，解码后得到结构化 span。因此当前明细文件里的 `raw_output` 是结构化对象：

```json
{
  "sample_id": 1,
  "query": "龚建平教授发表的rct研究最终结论是什么",
  "ground_truth": {
    "author_name": "龚建平",
    "author_name英文变体": "...",
    "author_institution": ""
  },
  "raw_output": {
    "model_type": "modernbert_token_classification_span",
    "model_dir": "/home/chenqr/work/NLU-distillation/experiments/modernbert_span_ner/author_org",
    "raw_entities": [
      {
        "label": "AUTHOR",
        "field": "author_name",
        "start": 0,
        "end": 1,
        "text": "龚"
      },
      {
        "label": "AUTHOR",
        "field": "author_name",
        "start": 0,
        "end": 3,
        "text": "龚建平"
      }
    ]
  },
  "parsed_output": {
    "author_name": "龚建平",
    "author_name英文变体": "...",
    "author_institution": ""
  }
}
```

这里可以看到一个 BERT span 模型常见现象：同一位置可能出现短 span 和长 span，例如 `龚` 与 `龚建平`。这是因为 tokenizer 子词、overflow window、BIO 边界解码会产生重叠候选。当前后处理会清掉明显无效的短作者片段，所以最终 `parsed_output.author_name` 是 `龚建平`。

业务集每条样本的原始输出文件是：

```text
reports/modernbert_span_ner/author_org_business_eval_spanbert_20260609_details.jsonl
```

该文件每行一条样本，包含：

- `sample_id`
- `query`
- `ground_truth`
- `raw_output.raw_entities`
- `parsed_output`

## 我们如何后处理原始输出

当前后处理在 `scripts/eval_author_org_span_bert_business.py` 中完成。

整体流程：

```text
raw_entities -> 按 label 分组 -> 清洗作者/机构片段 -> 去重 -> 生成英文变体 -> parsed_output
```

### 1. 从 token 标签解码 raw_entities

推理时对每条 query：

1. tokenizer 编码原文，保留 offset。
2. 长文本使用 `max_length=512`、`stride=128` 生成多个窗口。
3. BERT 对每个 token 输出标签。
4. 每个窗口内按 BIO 规则合并连续 token，得到字符级 span。
5. 多窗口重复 span 用 `(label, start, end)` 去重。

得到的原始实体类似：

```json
[
  {"label": "INSTITUTION", "field": "author_institution", "start": 0, "end": 4, "text": "马赛大学"},
  {"label": "AUTHOR", "field": "author_name", "start": 4, "end": 15, "text": "Guy Magalon"}
]
```

### 2. 作者片段清洗

作者清洗函数是 `clean_author`，主要做：

- 去掉首尾标点、空白、项目符号。
- 去掉 query 前缀，如“请、搜索、查询、查找、列出、找到、输出”等。
- 去掉称谓和尾部描述，如“教授、医生、主任、院士、课题组、团队”等。
- 如果中文片段里混入机构关键词，尝试剥离机构前缀。
- 英文作者名只保留英文字母、空格、点、逗号、撇号、连字符组成的连续片段。
- 丢弃长度小于 2 的片段。
- 丢弃明显不是作者的词，如“负责的、牵头、讲课、搜索、查询、查找”。
- 中文片段如果仍包含明显机构关键词，则不作为作者输出。

示例：

```json
{
  "raw_entities": [
    {"label": "AUTHOR", "text": "龚"},
    {"label": "AUTHOR", "text": "龚建平"}
  ],
  "parsed author_name": "龚建平"
}
```

`龚` 因长度小于 2 被清掉，`龚建平` 保留。

### 3. 机构片段清洗

机构清洗函数是 `clean_institution`，主要做：

- 去掉首尾标点、空白、项目符号。
- 去掉 query 前缀。
- 去掉尾部动作或描述，如“作为、负责、牵头、正在、进行、发起、相关、所有、有哪些”等。
- 丢弃长度小于 2 的片段。
- 丢弃明显不是机构的短词，如“搜索、查询、查找、请、由、在”。

示例：

```json
{
  "raw_entities": [
    {"label": "INSTITUTION", "text": "马"},
    {"label": "INSTITUTION", "text": "马赛大学"}
  ],
  "parsed author_institution": "马赛大学"
}
```

`马` 因长度小于 2 被清掉，`马赛大学` 保留。

### 4. 去重和字段聚合

清洗后：

- `AUTHOR` 片段进入 `author_name`。
- `INSTITUTION` 片段进入 `author_institution`。
- 多个值按出现顺序去重。
- 多个值用中文分号 `；` 拼接。

例如：

```json
{
  "author_name": "李四",
  "author_institution": "复旦大学附属肿瘤医院"
}
```

### 5. 生成 author_name 英文变体

`author_name英文变体` 不由 BERT 输出。当前做法是：

1. BERT 先抽取 `author_name`。
2. 对每个作者名调用 `nlu-bert` 中的变体生成逻辑。
3. 结合旧 BERT 项目的 `author_variant_lexicon.json`。
4. 输出 `<variant>...</variant>` 格式。

因此，英文变体字段的错误来源通常有两类：

- BERT 抽错了作者名，导致变体基于错误名字生成。
- 作者名抽对了，但变体规则/词典与标准答案枚举顺序或覆盖范围不完全一致。

### 6. 当前后处理仍存在的问题

从业务集明细可以看到，当前后处理已经能处理大量短 span 噪声，但仍有风险：

- 英文名可能被 tokenizer 切成多个不连续 span，例如 `stephen liu` 被切成 `step` 和 `hen liu`。
- 申办方或公司名可能被误判成作者，例如 `Advent`、`默沙东`。
- 机构可能被切碎，例如 `中山大学肿瘤防治中心` 被解成 `山大学`、`肿瘤`、`瘤防治中心`。
- “主要研究中心、申办方、牵头单位”这类临床试验语境下的机构，不一定属于 author_org 业务字段，需要靠任务定义和负例数据进一步约束。

因此，当前 span-BERT 路线已经能提供可追踪的原始 span 输出，但后续要提高业务稳定性，重点不是再看 token accuracy，而是：

- 清理训练数据中作者/机构定义不一致的样本。
- 增强临床试验申办方/研究中心类负例。
- 对重叠 span 做最长优先或包含关系过滤。
- 对英文连续作者名做更稳的 token span 合并。
- 明确哪些机构语境应输出为空。

## 当前业务集结果

最新业务集：

```text
/home/chenqr/work/nlu-server/eval/作者和机构.json
```

最新报告：

```text
reports/modernbert_span_ner/author_org_business_eval_spanbert_20260609.md
```

最新核心指标：

```text
Average-F1: 0.8264
author_name-F1: 0.8451
author_name英文变体-F1: 0.8393
author_institution-F1: 0.7576
Null-accuracy: 0.9430
```

