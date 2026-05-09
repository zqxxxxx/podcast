from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from podcast_pipeline.llm import load_prompt


class JsonLLM(Protocol):
    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        ...


def create_publishing_assets(
    llm: JsonLLM,
    transcript_path: Path,
    final_edl_path: Path,
    output_dir: Path,
) -> Path:
    user_prompt = (
        "Final transcript or transcript source:\n"
        f"{transcript_path.read_text(encoding='utf-8')}\n\n"
        "Final EDL:\n"
        f"{final_edl_path.read_text(encoding='utf-8')}\n"
    )
    result = llm.generate_json(load_prompt("shownotes.md"), user_prompt)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "shownotes.md").write_text(result["shownotes_markdown"], encoding="utf-8")
    (output_dir / "publishing_assets.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_dir / "shownotes.md"
