from __future__ import annotations

import json
import re
import time
from http.client import RemoteDisconnected
from pathlib import Path
from typing import Any
from urllib import error, request

from openai import OpenAI

from podcast_pipeline.runtime_env import get_env_value

_THINKING_BLOCK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


def _loads_json_from_model_content(content: str) -> dict[str, Any]:
    content_without_thinking = _THINKING_BLOCK_RE.sub("", content).strip()
    try:
        parsed = json.loads(content_without_thinking)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        for index, char in enumerate(content_without_thinking):
            if char not in "{[":
                continue
            try:
                parsed, _ = decoder.raw_decode(content_without_thinking[index:])
                break
            except json.JSONDecodeError:
                continue
        else:
            raise
    if not isinstance(parsed, dict):
        raise ValueError("LLM response must be a JSON object.")
    return parsed


class LLMClient:
    def __init__(self, model: str, api_key_env: str = "OPENAI_API_KEY") -> None:
        api_key = get_env_value(api_key_env)
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


class MiniMaxChatLLM:
    def __init__(self, model: str, api_key: str, base_url: str, max_retries: int = 2) -> None:
        self.model = model
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
        }
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = request.Request(
            f"{self.base_url}/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        for attempt in range(self.max_retries + 1):
            try:
                with request.urlopen(req, timeout=180) as response:
                    raw = json.loads(response.read().decode("utf-8"))
                break
            except (RemoteDisconnected, TimeoutError, error.URLError):
                if attempt == self.max_retries:
                    raise
                time.sleep(2**attempt)
        content = raw["choices"][0]["message"]["content"]
        return _loads_json_from_model_content(content)


def build_llm_client(config: Any):
    provider = getattr(config, "llm_provider", "minimax")
    if provider == "minimax":
        api_key_env = getattr(config, "llm_api_key_env", "MINIMAX_API_KEY")
        api_key = get_env_value(api_key_env)
        if not api_key:
            raise ValueError(f"{api_key_env} is required.")
        return MiniMaxChatLLM(
            getattr(config, "llm_model", "MiniMax-M2.7"),
            api_key,
            getattr(config, "llm_base_url", "https://api.minimax.io/v1"),
        )
    if provider == "openai":
        if not getattr(config, "openai_enabled", False):
            raise ValueError("OpenAI provider is disabled in config.")
        return LLMClient(getattr(config, "text_model", "gpt-5.5"), getattr(config, "openai_api_key_env", "OPENAI_API_KEY"))
    raise ValueError(f"Unsupported LLM provider: {provider}")


def load_prompt(name: str) -> str:
    prompt_path = Path(__file__).parent / "prompts" / name
    return prompt_path.read_text(encoding="utf-8")
