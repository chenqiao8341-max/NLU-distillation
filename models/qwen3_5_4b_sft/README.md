# Qwen3.5 4B SFT

Legacy training config:

- `/home/qiao/work/LLaMA-Factory/my_configs/qwen3.5_4b_base_lora_sft_nlu_author_org.yaml`

Base model:

- `/home/qiao/models/Qwen/Qwen3.5-4B`

Initial role:

- Stronger SFT candidate for unified NLU JSON output.
- Good candidate for `topic_keyword`, `trial_slots`, and `query_rewrite` after schema is fixed.

Tracking:

- Existing config has `plot_loss: true`.
- Switch `report_to: none` to `wandb` or `tensorboard` when visualization is needed.
