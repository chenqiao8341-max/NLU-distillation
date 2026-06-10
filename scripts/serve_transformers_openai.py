#!/usr/bin/env python3
"""Minimal OpenAI-compatible chat server backed by Transformers.

This is intended for local evaluation when vLLM is unavailable. It implements
only the endpoints used by nlu-evaluator/scripts/eval_local_openai.py.
"""

from __future__ import annotations

import argparse
import time
import uuid
from typing import Any

import torch
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import (
    AutoModelForCausalLM,
    AutoModelForImageTextToText,
    AutoTokenizer,
    StoppingCriteria,
    StoppingCriteriaList,
)


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str | None = None
    messages: list[ChatMessage]
    temperature: float = 0.0
    max_tokens: int = 512


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve a local HF model with a tiny OpenAI-compatible API")
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--served-model-name", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--dtype", default="bfloat16", choices=["auto", "bfloat16", "float16", "float32"])
    parser.add_argument("--device-map", default="auto")
    parser.add_argument(
        "--stop-after-first-json",
        action="store_true",
        help="Stop generation after the first balanced JSON object. Useful for extraction evals.",
    )
    parser.add_argument(
        "--max-generation-seconds",
        type=float,
        default=60.0,
        help="Optional per-request wall-clock limit passed to transformers.generate(max_time=...).",
    )
    parser.add_argument(
        "--enable-thinking",
        action="store_true",
        help="Pass enable_thinking=True to tokenizer.apply_chat_template. Defaults to nothink.",
    )
    return parser.parse_args()


def dtype_from_name(name: str) -> torch.dtype | str:
    if name == "auto":
        return "auto"
    return {
        "bfloat16": torch.bfloat16,
        "float16": torch.float16,
        "float32": torch.float32,
    }[name]


class FirstJsonObjectCriteria(StoppingCriteria):
    def __init__(self, tokenizer: Any, prompt_length: int):
        self.tokenizer = tokenizer
        self.prompt_length = prompt_length

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs: Any) -> bool:
        generated = input_ids[0, self.prompt_length :]
        if generated.numel() == 0:
            return False
        text = self.tokenizer.decode(generated, skip_special_tokens=True)
        start = text.find("{")
        if start < 0:
            return False
        depth = 0
        in_string = False
        escaped = False
        for char in text[start:]:
            if escaped:
                escaped = False
                continue
            if char == "\\":
                escaped = True
                continue
            if char == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return True
        return False


def has_balanced_json_object(text: str) -> bool:
    start = text.find("{")
    if start < 0:
        return False
    depth = 0
    in_string = False
    escaped = False
    for char in text[start:]:
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return True
    return False


def main() -> None:
    args = parse_args()
    tokenizer = AutoTokenizer.from_pretrained(args.model_path, trust_remote_code=True)
    model_kwargs = {
        "torch_dtype": dtype_from_name(args.dtype),
        "device_map": args.device_map,
        "trust_remote_code": True,
    }
    try:
        model = AutoModelForImageTextToText.from_pretrained(args.model_path, **model_kwargs)
    except ValueError:
        model = AutoModelForCausalLM.from_pretrained(args.model_path, **model_kwargs)
    model.eval()

    app = FastAPI()

    @app.get("/v1/models")
    def models() -> dict[str, Any]:
        return {
            "object": "list",
            "data": [
                {
                    "id": args.served_model_name,
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": "local-transformers",
                }
            ],
        }

    @app.post("/v1/chat/completions")
    def chat_completions(req: ChatRequest) -> dict[str, Any]:
        messages = [{"role": msg.role, "content": msg.content} for msg in req.messages]
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=args.enable_thinking,
        )
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        do_sample = req.temperature > 0
        generation_kwargs: dict[str, Any] = {
            "max_new_tokens": req.max_tokens,
            "do_sample": do_sample,
            "pad_token_id": tokenizer.pad_token_id or tokenizer.eos_token_id,
            "eos_token_id": tokenizer.eos_token_id,
        }
        if args.stop_after_first_json:
            generation_kwargs["stopping_criteria"] = StoppingCriteriaList(
                [FirstJsonObjectCriteria(tokenizer, inputs["input_ids"].shape[-1])]
            )
        if args.max_generation_seconds:
            generation_kwargs["max_time"] = args.max_generation_seconds
        if do_sample:
            generation_kwargs["temperature"] = req.temperature
        with torch.inference_mode():
            output_ids = model.generate(**inputs, **generation_kwargs)
        new_tokens = output_ids[0, inputs["input_ids"].shape[-1] :]
        content = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
        finish_reason = "stop"
        if int(new_tokens.shape[-1]) >= req.max_tokens:
            finish_reason = "length"
        elif args.stop_after_first_json and "{" in content and not has_balanced_json_object(content):
            finish_reason = "length"
        created = int(time.time())
        return {
            "id": f"chatcmpl-{uuid.uuid4().hex}",
            "object": "chat.completion",
            "created": created,
            "model": req.model or args.served_model_name,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": finish_reason,
                }
            ],
            "usage": {
                "prompt_tokens": int(inputs["input_ids"].shape[-1]),
                "completion_tokens": int(new_tokens.shape[-1]),
                "total_tokens": int(output_ids.shape[-1]),
            },
        }

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
