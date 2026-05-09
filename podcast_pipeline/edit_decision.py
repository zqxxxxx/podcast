from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from podcast_pipeline.llm import load_prompt
from podcast_pipeline.schemas import (
    edit_segment_from_dict,
    edit_segment_to_dict,
    total_edit_duration,
    validate_edit_segments,
)


class JsonLLM(Protocol):
    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        ...


def create_final_edl(
    llm: JsonLLM,
    transcript_path: Path,
    content_map_path: Path,
    style_guide_path: Path,
    selection_rules_path: Path,
    cutting_rules_path: Path,
    output_path: Path,
    min_seconds: int,
    max_seconds: int,
) -> Path:
    user_prompt = "\n\n".join(
        [
            "Transcript JSON:\n" + transcript_path.read_text(encoding="utf-8"),
            "Content map JSON:\n" + content_map_path.read_text(encoding="utf-8"),
            "Style guide:\n" + style_guide_path.read_text(encoding="utf-8"),
            "Selection rules:\n" + selection_rules_path.read_text(encoding="utf-8"),
            "Cutting rules:\n" + cutting_rules_path.read_text(encoding="utf-8"),
        ]
    )
    result = llm.generate_json(load_prompt("final_edit_decision.md"), user_prompt)
    segments = [edit_segment_from_dict(item) for item in result.get("segments", [])]
    validate_edit_segments(segments)
    duration = total_edit_duration(segments)
    if duration < min_seconds or duration > max_seconds:
        raise ValueError(f"Final EDL duration {duration} is outside {min_seconds}-{max_seconds} seconds.")
    payload = {
        "duration": duration,
        "total_target_reasoning": result.get("total_target_reasoning", ""),
        "segments": [edit_segment_to_dict(segment) for segment in segments],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path
