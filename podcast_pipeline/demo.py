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


def create_demo_edl(
    llm: JsonLLM,
    transcript_path: Path,
    content_map_path: Path,
    output_path: Path,
    min_seconds: int,
    max_seconds: int,
) -> Path:
    system_prompt = load_prompt("demo_selection.md")
    user_prompt = (
        "Transcript JSON:\n"
        f"{transcript_path.read_text(encoding='utf-8')}\n\n"
        "Content map JSON:\n"
        f"{content_map_path.read_text(encoding='utf-8')}\n"
    )
    result = llm.generate_json(system_prompt, user_prompt)
    segments = [edit_segment_from_dict(item) for item in result.get("segments", [])]
    validate_edit_segments(segments)
    duration = total_edit_duration(segments)
    if duration < min_seconds or duration > max_seconds:
        raise ValueError(f"Demo duration {duration} is outside {min_seconds}-{max_seconds} seconds.")
    payload = {
        "candidate_reason": result.get("candidate_reason", ""),
        "duration": duration,
        "segments": [edit_segment_to_dict(segment) for segment in segments],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path
