from __future__ import annotations

import json
import math
from dataclasses import replace
from pathlib import Path
from typing import Protocol

from podcast_pipeline.llm import load_prompt
from podcast_pipeline.schemas import (
    EditSegment,
    edit_segment_from_dict,
    edit_segment_to_dict,
    total_edit_duration,
    validate_edit_segments,
)

MAX_DEMO_CANDIDATE_BLOCKS = 20


class JsonLLM(Protocol):
    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        ...


def _score_block(block: dict) -> tuple[int, int, float]:
    highlight_score = int(block.get("highlight_score", 0))
    deletion_score = int(block.get("deletion_score", 5))
    duration = float(block.get("end", 0)) - float(block.get("start", 0))
    return (highlight_score, -deletion_score, duration)


def _select_candidate_blocks(blocks: list[dict], max_blocks: int = MAX_DEMO_CANDIDATE_BLOCKS) -> list[dict]:
    valid_blocks = [block for block in blocks if "start" in block and "end" in block]
    if len(valid_blocks) <= max_blocks:
        return sorted(valid_blocks, key=lambda block: float(block["start"]))

    selected: list[dict] = []
    selected_keys: set[tuple[float, float, str]] = set()
    min_start = min(float(block["start"]) for block in valid_blocks)
    max_end = max(float(block["end"]) for block in valid_blocks)
    span = max(max_end - min_start, 1)
    per_bucket = max(1, max_blocks // 4)

    def add(block: dict) -> None:
        key = (float(block["start"]), float(block["end"]), str(block.get("topic", "")))
        if key not in selected_keys and len(selected) < max_blocks:
            selected.append(block)
            selected_keys.add(key)

    for bucket_index in range(4):
        bucket_start = min_start + span * bucket_index / 4
        bucket_end = min_start + span * (bucket_index + 1) / 4
        bucket = [
            block
            for block in valid_blocks
            if bucket_start <= float(block["start"]) < bucket_end or (bucket_index == 3 and float(block["start"]) <= bucket_end)
        ]
        for block in sorted(bucket, key=_score_block, reverse=True)[:per_bucket]:
            add(block)

    for block in sorted(valid_blocks, key=_score_block, reverse=True):
        add(block)
    return sorted(selected, key=lambda block: float(block["start"]))


def _transcript_excerpts_for_blocks(segments: list[dict], blocks: list[dict]) -> list[dict]:
    excerpts = []
    for block in blocks:
        block_start = float(block["start"])
        block_end = float(block["end"])
        matching_segments = [
            segment
            for segment in segments
            if float(segment["end"]) > block_start and float(segment["start"]) < block_end
        ]
        excerpts.append(
            {
                "block_start": block_start,
                "block_end": block_end,
                "topic": block.get("topic", ""),
                "segments": matching_segments,
            }
        )
    return excerpts


def _fit_segments_to_duration(segments: list[EditSegment], min_seconds: int, max_seconds: int) -> list[EditSegment]:
    if total_edit_duration(segments) <= max_seconds:
        return segments

    unit = 10
    min_units = math.ceil(min_seconds * unit)
    max_units = math.floor(max_seconds * unit)
    target_units = round(((min_seconds + max_seconds) / 2) * unit)
    durations = [math.ceil((segment.end - segment.start) * unit) for segment in segments]
    states: dict[int, list[int]] = {0: []}
    for index, duration in enumerate(durations):
        for total, selected in list(states.items()):
            new_total = total + duration
            if new_total <= max_units and new_total not in states:
                states[new_total] = [*selected, index]

    candidates = [(total, selected) for total, selected in states.items() if total >= min_units]
    if candidates:
        _, selected_indices = min(candidates, key=lambda item: (abs(item[0] - target_units), -item[0]))
        return [segments[index] for index in selected_indices]

    for segment in segments:
        clipped_end = min(segment.end, segment.start + max_seconds)
        if clipped_end - segment.start >= min_seconds:
            return [replace(segment, end=clipped_end)]
    return segments


def create_demo_edl(
    llm: JsonLLM,
    transcript_path: Path,
    content_map_path: Path,
    output_path: Path,
    min_seconds: int,
    max_seconds: int,
) -> Path:
    system_prompt = load_prompt("demo_selection.md")
    transcript = json.loads(transcript_path.read_text(encoding="utf-8"))
    content_map = json.loads(content_map_path.read_text(encoding="utf-8"))
    candidate_blocks = _select_candidate_blocks(content_map.get("blocks", []))
    transcript_excerpts = _transcript_excerpts_for_blocks(transcript.get("segments", []), candidate_blocks)
    user_prompt = (
        f"Target duration: {min_seconds}-{max_seconds} seconds\n\n"
        "Candidate content blocks JSON:\n"
        f"{json.dumps(candidate_blocks, ensure_ascii=False, separators=(',', ':'))}\n\n"
        "Transcript excerpts for candidate blocks JSON:\n"
        f"{json.dumps(transcript_excerpts, ensure_ascii=False, separators=(',', ':'))}\n\n"
        "Select demo segments using only these source timestamps."
    )
    result = llm.generate_json(system_prompt, user_prompt)
    segments = sorted(
        [edit_segment_from_dict(item) for item in result.get("segments", [])],
        key=lambda segment: segment.start,
    )
    validate_edit_segments(segments)
    segments = _fit_segments_to_duration(segments, min_seconds, max_seconds)
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
