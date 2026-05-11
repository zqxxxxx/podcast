from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from podcast_pipeline.llm import load_prompt

DEFAULT_MAX_CHUNK_SECONDS = 10 * 60
DEFAULT_MAX_CHUNK_CHARS = 20_000


class JsonLLM(Protocol):
    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        ...


def _compact_transcript_json(segments: list[dict]) -> str:
    return json.dumps({"segments": segments}, ensure_ascii=False, separators=(",", ":"))


def _chunk_segments(
    segments: list[dict],
    max_chunk_seconds: int = DEFAULT_MAX_CHUNK_SECONDS,
    max_chunk_chars: int = DEFAULT_MAX_CHUNK_CHARS,
) -> list[list[dict]]:
    chunks: list[list[dict]] = []
    current: list[dict] = []
    for segment in segments:
        if not current:
            current = [segment]
            continue
        proposed = [*current, segment]
        proposed_duration = float(proposed[-1]["end"]) - float(proposed[0]["start"])
        proposed_chars = len(_compact_transcript_json(proposed))
        if proposed_duration > max_chunk_seconds or proposed_chars > max_chunk_chars:
            chunks.append(current)
            current = [segment]
        else:
            current = proposed
    if current:
        chunks.append(current)
    return chunks


def _build_user_prompt(outline_text: str, chunk: list[dict], chunk_index: int, chunk_count: int) -> str:
    return (
        "Interview outline:\n"
        f"{outline_text}\n\n"
        f"Transcript JSON chunk {chunk_index} of {chunk_count}:\n"
        f"{_compact_transcript_json(chunk)}\n\n"
        "Return content-map blocks only for this transcript chunk."
    )


def build_content_map(
    llm: JsonLLM,
    transcript_path: Path,
    outline_path: Path,
    output_path: Path,
    max_chunk_seconds: int = DEFAULT_MAX_CHUNK_SECONDS,
    max_chunk_chars: int = DEFAULT_MAX_CHUNK_CHARS,
) -> Path:
    transcript = json.loads(transcript_path.read_text(encoding="utf-8"))
    outline_text = outline_path.read_text(encoding="utf-8")
    system_prompt = load_prompt("content_map.md")
    chunks = _chunk_segments(
        transcript.get("segments", []),
        max_chunk_seconds=max_chunk_seconds,
        max_chunk_chars=max_chunk_chars,
    )
    blocks = []
    chunk_dir = output_path.parent / "chunks"
    chunk_dir.mkdir(parents=True, exist_ok=True)
    for index, chunk in enumerate(chunks, start=1):
        chunk_path = chunk_dir / f"chunk_{index:03d}.json"
        if chunk_path.exists():
            result = json.loads(chunk_path.read_text(encoding="utf-8"))
            print(f"content-map chunk {index}/{len(chunks)} cached", flush=True)
        else:
            user_prompt = _build_user_prompt(outline_text, chunk, index, len(chunks))
            result = llm.generate_json(system_prompt, user_prompt)
            chunk_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"content-map chunk {index}/{len(chunks)} generated", flush=True)
        if "blocks" not in result or not isinstance(result["blocks"], list):
            raise ValueError("Content map result must contain a blocks list.")
        blocks.extend(result["blocks"])
    blocks.sort(key=lambda item: float(item.get("start", 0)))
    result = {"blocks": blocks, "chunk_count": len(chunks)}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path
