from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from openai import OpenAI


class LLMClient:
    def __init__(self, model: str, api_key_env: str = "OPENAI_API_KEY") -> None:
        api_key = os.getenv(api_key_env)
        if not api_key:
            raise ValueError(f"{api_key_env} is required.")
        self.model = model
        self.client = OpenAI(api_key=api_key)

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        response = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            text={"format": {"type": "json_object"}},
        )
        return json.loads(response.output_text)


def load_prompt(name: str) -> str:
    prompt_path = Path(__file__).parent / "prompts" / name
    return prompt_path.read_text(encoding="utf-8")
