from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from podcast_pipeline.llm import load_prompt


class JsonLLM(Protocol):
    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        ...


def ingest_demo_feedback(llm: JsonLLM, feedback_text: str, output_path: Path) -> Path:
    result = llm.generate_json(load_prompt("demo_feedback.md"), feedback_text)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def freeze_style(
    llm: JsonLLM,
    approved_demo_edl_path: Path,
    feedback_paths: list[Path],
    output_dir: Path,
) -> Path:
    feedback_payloads = [path.read_text(encoding="utf-8") for path in feedback_paths]
    user_prompt = (
        "Approved demo EDL:\n"
        f"{approved_demo_edl_path.read_text(encoding='utf-8')}\n\n"
        "Feedback history:\n"
        + "\n\n".join(feedback_payloads)
    )
    result = llm.generate_json(load_prompt("style_freeze.md"), user_prompt)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "edit_style_guide.md").write_text(
        result["style_guide_markdown"],
        encoding="utf-8",
    )
    (output_dir / "selection_rules.json").write_text(
        json.dumps(result["selection_rules"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "cutting_rules.json").write_text(
        json.dumps(result["cutting_rules"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_dir / "edit_style_guide.md"
