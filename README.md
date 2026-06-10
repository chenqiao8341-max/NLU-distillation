# NLU Distillation

这个目录用于把分散在 `nlu-bert`、`nlu-server`、`LLaMA-Factory` 里的本地 NLU 小模型工作收拢到一个项目下。

当前阶段的核心目标不是立刻锁定模型，而是先把数据、任务、模型候选、实验记录和后续 pipeline 接口整理清楚，方便比较：

- ModernBERT / encoder NER：适合确定性槽位抽取，如作者、机构。
- 0.8B 级别生成式小模型：适合低成本 SFT 和速度优先路线。
- 4B 级别生成式小模型：适合更复杂的多槽位、多任务输出。

## 当前已知进展

来源：`/home/qiao/work/aaa-work.md`

- `/home/qiao/work/nlu-bert`
  - 已完成 ModernBERT 作者和机构 NER 工程。
  - 包含 BIO 数据准备、训练、推理、作者英文变体补齐和离线评测。
  - 当前训练数据来自 `/home/qiao/work/nlu-server/eval/作者和机构_互联网扩展3k.json`。
- `/home/qiao/work/nlu-server`
  - 已完成本地 NLU 测评框架。
  - 支持 `data_type`、`作者和机构`、`机构和国家`、`时间和if值` 等任务。
  - 输出 json、md、csv、xlsx 报告。
- `/home/qiao/work/LLaMA-Factory`
  - 已有 `Qwen3.5-0.8B` 和 `Qwen3.5-4B` 的 NLU 作者/机构 LoRA SFT 配置。
  - 训练配置位于 `/home/qiao/work/LLaMA-Factory/my_configs/`。

## 新项目结构

```text
NLU-distillation/
  nlu-data/                    # 当前生产抽取原始数据，暂不移动
  data/
    raw/                       # 后续统一放原始数据或软链接
    samples/                   # 小样本观察集
    processed/                 # 清洗、规范化后的中间数据
    splits/                    # train/valid/test 切分
    annotations/               # 人工标注或校对数据
  tasks/                       # 按任务类型沉淀 schema、样例和处理说明
  models/                      # 按模型路线沉淀配置、适配脚本和说明
  configs/                     # 任务注册表、模型注册表、运行模板
  pipelines/                   # 后续流程化入口
  experiments/                 # 训练过程、wandb/tensorboard 本地目录
  reports/                     # 评测报告和模型对比表
  scripts/                     # 项目级脚本入口
  src/nlu_distillation/        # 后续 Python 包代码
  docs/                        # 设计文档和迁移记录
```

## 数据现状

当前已有：

- `nlu-data/100case.jsonl`
  - 从生产数据中抽取的前 100 条样本，用于观察 schema 和任务分布。
- `nlu-data/knows_nlu_20260101_20260603.jsonl`
  - 从生产环境提取的大规模 NLU 数据。
  - 当前文件较大，暂不复制到 `data/raw/`。

对 `100case.jsonl` 的快速观察：

- 高频数据源：`PAPER_EN`、`GUIDE`、`PAPER_CN`、`TRIAL`、`MEETING`。
- 高频字段：`topics`、`keyword`、`expand_topics`、`expand_keywords`、`rewritten_question`。
- 可拆分任务：数据源分类、主题/关键词抽取与扩展、query 改写与翻译、作者/机构、机构/国家、时间/IF、临床试验槽位、期刊/研究类型。

## 候选任务

任务注册表见 `configs/task_registry.yaml`，目录见 `tasks/`。

建议优先级：

1. `author_org`
   - 已有 BERT 工程和 3k 标注数据，是最适合先迁移的确定性任务。
2. `data_type`
   - 输出空间较小，适合作为 0.8B/4B SFT 的轻量对比任务。
3. `time_if`
   - 规则、分类、数值抽取混合，适合验证小模型边界。
4. `topic_keyword`
   - 生产数据覆盖最多，但需要先定义监督信号和评测口径。
5. `trial_slots`
   - 字段多、结构化强，建议在 4B 路线上优先验证。

## 候选模型路线

模型注册表见 `configs/model_registry.yaml`。

- `modernbert_ner`
  - 先迁移作者/机构抽取。
  - 适合作为速度和稳定性 baseline。
- `qwen3_5_0_8b_sft`
  - 用 LLaMA-Factory 做 LoRA SFT。
  - 重点观察低成本小模型能否覆盖简单结构化任务。
- `qwen3_5_4b_sft`
  - 用 LLaMA-Factory 做 LoRA SFT。
  - 重点覆盖多任务和复杂槽位。


## LLaMA-Factory 快速启动

当前 `data/processed/` 下已经为五个任务生成了 SFT 数据，可以直接接入 `/home/qiao/work/LLaMA-Factory` 做 LoRA SFT。

### 任务和数据路径

```text
author_org        data/processed/author_org/sft/all.jsonl
org_country       data/processed/org_country/sft/all.jsonl
time_if           data/processed/time_if/sft/all.jsonl
data_type         data/processed/data_type/sft/all.jsonl
topic_keywords    data/processed/topic_keywords/sft/all.jsonl
```

每条数据是 Alpaca 风格：

```json
{"instruction":"...","input":"...","output":"..."}
```

### 1. 注册数据到 LLaMA-Factory

LLaMA-Factory 默认从自己的 `data/` 目录读取数据。推荐用软链接，避免复制多份数据。

```bash
cd /home/qiao/work/LLaMA-Factory

ln -sf /home/qiao/work/NLU-distillation/data/processed/author_org/sft/all.jsonl data/nlu_author_org_prod_sft.jsonl
ln -sf /home/qiao/work/NLU-distillation/data/processed/org_country/sft/all.jsonl data/nlu_org_country_prod_sft.jsonl
ln -sf /home/qiao/work/NLU-distillation/data/processed/time_if/sft/all.jsonl data/nlu_time_if_prod_sft.jsonl
ln -sf /home/qiao/work/NLU-distillation/data/processed/data_type/sft/all.jsonl data/nlu_data_type_prod_sft.jsonl
ln -sf /home/qiao/work/NLU-distillation/data/processed/topic_keywords/sft/all.jsonl data/nlu_topic_keywords_prod_sft.jsonl
```

然后在 `/home/qiao/work/LLaMA-Factory/data/dataset_info.json` 加入：

```json
{
  "nlu_author_org_prod_sft": {
    "file_name": "nlu_author_org_prod_sft.jsonl"
  },
  "nlu_org_country_prod_sft": {
    "file_name": "nlu_org_country_prod_sft.jsonl"
  },
  "nlu_time_if_prod_sft": {
    "file_name": "nlu_time_if_prod_sft.jsonl"
  },
  "nlu_data_type_prod_sft": {
    "file_name": "nlu_data_type_prod_sft.jsonl"
  },
  "nlu_topic_keywords_prod_sft": {
    "file_name": "nlu_topic_keywords_prod_sft.jsonl"
  }
}
```

### 2. 选择模型和任务

先从两条路线开始：

```text
0.8B 快速 baseline: /home/qiao/models/Qwen/Qwen3.5-0.8B
4B  效果候选:       /home/qiao/models/Qwen/Qwen3.5-4B
```

任务数据名对应：

```text
作者和机构      nlu_author_org_prod_sft
机构和国家      nlu_org_country_prod_sft
时间和if值      nlu_time_if_prod_sft
data_type       nlu_data_type_prod_sft
topic和keywords nlu_topic_keywords_prod_sft
```

### 3. 新建训练配置

可以复制已有配置再改三处：`model_name_or_path`、`dataset`、`output_dir`。

0.8B + 作者和机构：

```yaml
### model
model_name_or_path: /home/qiao/models/Qwen/Qwen3.5-0.8B
trust_remote_code: true

### method
stage: sft
do_train: true
finetuning_type: lora
lora_rank: 8
lora_target: all
additional_target: embed_tokens,lm_head

### dataset
dataset: nlu_author_org_prod_sft
template: qwen3_nothink
cutoff_len: 4096
max_samples: null
overwrite_cache: true
preprocessing_num_workers: 4
dataloader_num_workers: 2

### output
output_dir: saves/qwen3.5-0.8b/lora/nlu-author-org-prod
logging_steps: 5
save_steps: 100
plot_loss: true
overwrite_output_dir: true
save_only_model: false
report_to: none

### train
per_device_train_batch_size: 4
gradient_accumulation_steps: 4
learning_rate: 1e-4
num_train_epochs: 2.0
lr_scheduler_type: cosine
warmup_ratio: 0.03
bf16: true
gradient_checkpointing: true
ddp_timeout: 180000000
resume_from_checkpoint: null
```

4B 只需要改：

```yaml
model_name_or_path: /home/qiao/models/Qwen/Qwen3.5-4B
output_dir: saves/qwen3.5-4b/lora/nlu-author-org-prod
```

切换任务只需要改：

```yaml
dataset: nlu_topic_keywords_prod_sft
output_dir: saves/qwen3.5-4b/lora/nlu-topic-keywords-prod
```

### 4. 启动训练

```bash
cd /home/qiao/work/LLaMA-Factory
/home/qiao/work/lf-env/bin/llamafactory-cli train my_configs/qwen3.5_0.8b_nlu_author_org_prod.yaml
```

4B 示例：

```bash
cd /home/qiao/work/LLaMA-Factory
/home/qiao/work/lf-env/bin/llamafactory-cli train my_configs/qwen3.5_4b_nlu_topic_keywords_prod.yaml
```

### 5. 可视化 loss

最简单先用 LLaMA-Factory 自带的 `plot_loss: true`，训练结束后看 `output_dir` 下的 loss 图。

如果要接 TensorBoard：

```yaml
report_to: tensorboard
```

然后：

```bash
cd /home/qiao/work/LLaMA-Factory
tensorboard --logdir saves
```

如果要接 wandb：

```yaml
report_to: wandb
```

并在训练前设置：

```bash
export WANDB_PROJECT=nlu-distillation
```

### 6. 导出模型

训练完成后复制旧 merge 配置，改 adapter 路径和导出路径即可。

```bash
cd /home/qiao/work/LLaMA-Factory
/home/qiao/work/lf-env/bin/llamafactory-cli export my_configs/qwen3.5_4b_nlu_topic_keywords_prod_merge.yaml
```

### 7. 评测

把导出后的模型用 vLLM/OpenAI-compatible 服务挂起来后，复用 `nlu-evaluator`：

```bash
/home/qiao/work/llm_env/bin/python /home/qiao/work/nlu-evaluator/scripts/eval_local_openai.py \
  --base-url http://127.0.0.1:8000/v1 \
  --model qwen35-4b-nlu-topic-keywords \
  --tasks topic和keywords \
  --concurrency 16 \
  --max-tokens 384 \
  --output-prefix /home/qiao/work/nlu-evaluator/reports/topic_keywords/qwen35_4b_prod
```

多任务一起评：

```bash
/home/qiao/work/llm_env/bin/python /home/qiao/work/nlu-evaluator/scripts/eval_local_openai.py \
  --base-url http://127.0.0.1:8000/v1 \
  --model qwen35-4b-nlu-all \
  --tasks 作者和机构 机构和国家 时间和if值 data_type topic和keywords \
  --concurrency 16 \
  --max-tokens 512 \
  --output-prefix /home/qiao/work/nlu-evaluator/reports/qwen35_4b_nlu_all_prod
```

### 推荐实验顺序

1. `Qwen3.5-0.8B + data_type`
   - 小、快、输出空间简单，适合验证训练链路。
2. `Qwen3.5-0.8B + author_org`
   - 和 ModernBERT 做速度/准确率对照。
3. `Qwen3.5-4B + topic和keywords`
   - 更接近真实生产复杂抽取。
4. `Qwen3.5-4B + 五任务混合`
   - 把五个 `all.jsonl` 合并成一个 multi-task SFT，再看统一模型是否稳定。

## 后续 pipeline 方向

目标命令形态可以收敛为：

```bash
python -m nlu_distillation.pipeline \
  --task author_org \
  --model modernbert_ner \
  --dataset data/splits/author_org/train.jsonl \
  --run-name author_org_modernbert_v1
```

后续 pipeline 建议拆成：

1. `inspect`
   - 读取原始 JSONL，统计字段覆盖、空值、数据源、任务候选。
2. `prepare`
   - 按任务把生产数据转成训练格式。
3. `train`
   - 根据模型路线调用 ModernBERT 训练脚本或 LLaMA-Factory。
4. `evaluate`
   - 复用 `nlu-evaluator` 口径输出报告。
5. `compare`
   - 汇总不同模型、不同任务的指标。

## 可视化方向

暂不强依赖某个工具，但目录已预留：

- `experiments/wandb/`
- `experiments/tensorboard/`

LLaMA-Factory 配置中已有 `report_to` 选项，后续可切换为 `wandb`、`tensorboard`、`swanlab` 或 `mlflow`。

## 近期建议

先做三件小而关键的事：

1. 固定 `100case.jsonl` 的字段观察报告，明确每个任务的输入输出 schema。
2. 把 `author_org` 的 ModernBERT 数据准备、训练、评测迁入本项目。
3. 用同一批评测集比较 `modernbert_ner`、`qwen3.5-0.8b`、`qwen3.5-4b`，再决定是否扩大到全任务。
