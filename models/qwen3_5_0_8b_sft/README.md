# Qwen3.5 0.8B SFT

Legacy training config:

- `/home/qiao/work/LLaMA-Factory/my_configs/qwen3.5_0.8b_base_lora_sft_author_org.yaml`

Base model:

- `/home/qiao/models/Qwen/Qwen3.5-0.8B`

Initial role:

- Cheap SFT baseline.
- Good candidate for `data_type`, `author_org`, `org_country`, `time_if`.

Tracking:

- Existing config has `plot_loss: true`.
- Switch `report_to: none` to `wandb` or `tensorboard` when visualization is needed.
