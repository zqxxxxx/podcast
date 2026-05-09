from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from podcast_pipeline.llm import load_prompt


class JsonLLM(Protocol):
    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        ...


def build_content_map(
    llm: JsonLLM,
    transcript_path: Path,
    outline_path: Path,
    output_path: Path,
) -> Path:
    transcript_text = transcript_path.read_text(encoding="utf-8")
    outline_text = outline_path.read_text(encoding="utf-8")
    system_prompt = load_prompt("content_map.md")
    user_prompt = (
        "Interview outline:\n"
        f"{outline_text}\n\n"
        "Transcript JSON:\n"
        f"{transcript_text}\n"
    )
    result = llm.generate_json(system_prompt, user_prompt)
    if "blocks" not in result or not isinstance(result["blocks"], list):
        raise ValueError("Content map result must contain a blocks list.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path
