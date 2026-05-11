from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from openai import OpenAI

from podcast_pipeline.audio import ChunkPlan, build_chunk_plan, extract_transcription_chunk, ffprobe_duration
from podcast_pipeline.config import ProjectConfig
from podcast_pipeline.runtime_env import get_env_value
from podcast_pipeline.schemas import TranscriptSegment


def _normalize_text(value: str) -> str:
    return " ".join(value.strip().split())


def merge_chunk_segments(
    chunk_payloads: list[dict[str, Any]],
    duplicate_window_seconds: float = 6,
) -> list[TranscriptSegment]:
    merged: list[TranscriptSegment] = []
    seen_recent: list[TranscriptSegment] = []
    for payload in chunk_payloads:
        offset = float(payload["offset"])
        chunk_id = str(payload["chunk_id"])
        for raw_segment in payload["segments"]:
            text = _normalize_text(str(raw_segment.get("text", "")))
            if not text:
                continue
            start = round(offset + float(raw_segment["start"]), 3)
            end = round(offset + float(raw_segment["end"]), 3)
            is_duplicate = any(
                _normalize_text(previous.text) == text
                and abs(previous.start - start) <= duplicate_window_seconds
                for previous in seen_recent
            )
            if is_duplicate:
                continue
            segment = TranscriptSegment(
                start=start,
                end=end,
                text=text,
                speaker=raw_segment.get("speaker"),
                chunk_id=chunk_id,
            )
            merged.append(segment)
            seen_recent = (seen_recent + [segment])[-20:]
    return sorted(merged, key=lambda item: (item.start, item.end))


def transcript_segments_to_json(segments: list[TranscriptSegment]) -> list[dict[str, Any]]:
    return [
        {
            "start": segment.start,
            "end": segment.end,
            "text": segment.text,
            "speaker": segment.speaker,
            "chunk_id": segment.chunk_id,
        }
        for segment in segments
    ]


def transcribe_audio_file(
    client: OpenAI,
    audio_path: Path,
    model: str,
    language: str,
) -> dict[str, Any]:
    with audio_path.open("rb") as audio_file:
        result = client.audio.transcriptions.create(
            model=model,
            file=audio_file,
            language=language,
            response_format="verbose_json",
            timestamp_granularities=["segment"],
        )
    if hasattr(result, "model_dump"):
        return result.model_dump()
    if isinstance(result, dict):
        return result
    return json.loads(result.json())


def create_transcript(config: ProjectConfig, chunk_seconds: int = 1800) -> Path:
    api_key = get_env_value(config.openai_api_key_env)
    if not api_key:
        raise ValueError(f"{config.openai_api_key_env} is required.")
    client = OpenAI(api_key=api_key)
    total_seconds = ffprobe_duration(config.audio_path)
    chunk_plans: list[ChunkPlan] = build_chunk_plan(total_seconds, chunk_seconds=chunk_seconds)
    chunk_dir = config.outputs_root / "transcript" / "chunks"
    raw_payloads: list[dict[str, Any]] = []

    for chunk in chunk_plans:
        chunk_audio = chunk_dir / f"{chunk.chunk_id}.m4a"
        chunk_json = chunk_dir / f"{chunk.chunk_id}.json"
        if not chunk_json.exists():
            extract_transcription_chunk(config.audio_path, chunk_audio, chunk.start, chunk.end)
            payload = transcribe_audio_file(client, chunk_audio, config.transcription_model, config.language)
            chunk_json.parent.mkdir(parents=True, exist_ok=True)
            chunk_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        else:
            payload = json.loads(chunk_json.read_text(encoding="utf-8"))
        raw_payloads.append(
            {
                "chunk_id": chunk.chunk_id,
                "offset": chunk.start,
                "segments": payload.get("segments", []),
            }
        )

    merged = merge_chunk_segments(raw_payloads)
    output_path = config.outputs_root / "transcript" / "transcript.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps({"segments": transcript_segments_to_json(merged)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_path
