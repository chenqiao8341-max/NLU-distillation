# Office Server NLU Setup

Remote alias: `办公室`

Remote workspace:

```text
/home/chenqr/work/NLU-distillation
/home/chenqr/work/LLaMA-Factory
/home/chenqr/models
/home/chenqr/logs
```

## Environment

Training uses:

```text
/home/chenqr/.myenv
```

vLLM uses an isolated environment:

```text
/home/chenqr/vllm-env
```

This avoids changing the LLaMA-Factory training torch/CUDA stack.

## Scripts

```bash
~/work/NLU-distillation/scripts/remote/install_vllm_0_9_2.sh
~/work/NLU-distillation/scripts/remote/download_qwen35_models.sh
~/work/NLU-distillation/scripts/remote/start_vllm_qwen35_0_8b.sh
~/work/NLU-distillation/scripts/remote/train_nlu_lora.sh
~/work/NLU-distillation/scripts/remote/launch_two_nlu_trainings.sh
~/work/NLU-distillation/scripts/remote/smoke_check_remote.sh
```

## Model Download

```bash
ssh 办公室 '~/work/NLU-distillation/scripts/remote/download_qwen35_models.sh'
```

Expected local model paths:

```text
/home/chenqr/models/Qwen/Qwen3.5-0.8B
/home/chenqr/models/Qwen/Qwen3.5-4B
```

## vLLM Service

```bash
ssh 办公室 'CUDA_VISIBLE_DEVICES=0 nohup ~/work/NLU-distillation/scripts/remote/start_vllm_qwen35_0_8b.sh > ~/logs/vllm_qwen35_0_8b.log 2>&1 &'
```

Check:

```bash
ssh 办公室 'tail -100 ~/logs/vllm_qwen35_0_8b.log'
```

## Training

Single task:

```bash
ssh 办公室 '~/work/NLU-distillation/scripts/remote/train_nlu_lora.sh my_configs/qwen3.5_0.8b_lora_sft_nlu_data_type_prod.yaml 0'
```

Two GPUs:

```bash
ssh 办公室 '~/work/NLU-distillation/scripts/remote/launch_two_nlu_trainings.sh'
```

Custom two-GPU run:

```bash
ssh 办公室 '~/work/NLU-distillation/scripts/remote/launch_two_nlu_trainings.sh my_configs/qwen3.5_0.8b_lora_sft_nlu_time_if_prod.yaml my_configs/qwen3.5_4b_lora_sft_nlu_topic_keywords_prod.yaml'
```

Logs:

```bash
ssh 办公室 'ls -lt ~/logs/nlu-train | head'
```
