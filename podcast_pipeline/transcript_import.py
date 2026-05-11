from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from podcast_pipeline.schemas import TranscriptSegment, validate_time_range

TIME_RANGE_RE = re.compile(
    r"(?P<start>\d{1,2}:\d{2}:\d{2}[,.]\d{1,3})\s*-->\s*(?P<end>\d{1,2}:\d{2}:\d{2}[,.]\d{1,3})"
)
SPEAKER_RE = re.compile(r"^(?P<speaker>[^:：]{1,30})[:：]\s*(?P<text>.+)$")


@dataclass(frozen=True)
class ImportReport:
    source: Path
    output: Path
    segment_count: int
    first_start: float
    last_end: float


def parse_srt_timestamp(value: str) -> float:
    hours_text, minutes_text, seconds_text = value.replace(",", ".").split(":")
    seconds = float(seconds_text)
    return round((int(hours_text) * 3600) + (int(minutes_text) * 60) + seconds, 3)


def _normalize_text(lines: list[str]) -> str:
    return " ".join(" ".join(line.strip().split()) for line in lines if line.strip()).strip()


def _split_speaker(text: str) -> tuple[str | None, str]:
    match = SPEAKER_RE.match(text)
    if not match:
        return None, text
    speaker = match.group("speaker").strip()
    content = match.group("text").strip()
    if not content:
        return None, text
    return speaker, content


def _parse_blocks(text: str) -> list[TranscriptSegment]:
    normalized = text.replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n")
    blocks = re.split(r"\n\s*\n", normalized)
    segments: list[TranscriptSegment] = []
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        if lines[0].upper() == "WEBVTT":
            continue
        if lines[0].upper().startswith("NOTE"):
            continue
        time_index = next((index for index, line in enumerate(lines) if TIME_RANGE_RE.search(line)), None)
        if time_index is None:
            continue
        match = TIME_RANGE_RE.search(lines[time_index])
        if not match:
            continue
        transcript_text = _normalize_text(lines[time_index + 1 :])
        if not transcript_text:
            continue
        speaker, content = _split_speaker(transcript_text)
        start = parse_srt_timestamp(match.group("start"))
        end = parse_srt_timestamp(match.group("end"))
        validate_time_range(start, end, "transcript segment")
        segments.append(
            TranscriptSegment(
                start=start,
                end=end,
                text=content,
                speaker=speaker,
                chunk_id="feishu",
            )
        )
    return segments


def _validate_segments(segments: list[TranscriptSegment]) -> None:
    if not segments:
        raise ValueError("Transcript import produced no segments.")
    previous_start = -1.0
    for index, segment in enumerate(segments):
        validate_time_range(segment.start, segment.end, f"transcript segment {index}")
        if segment.start < previous_start:
            raise ValueError("Transcript segments must be sorted by start time.")
        previous_start = segment.start


def transcript_segments_to_json(segments: list[TranscriptSegment]) -> list[dict]:
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


def import_transcript_file(source_path: Path, output_path: Path) -> ImportReport:
    if source_path.suffix.lower() not in {".srt", ".vtt", ".txt"}:
        raise ValueError("Transcript import supports .srt, .vtt, and timestamped .txt files.")
    segments = _parse_blocks(source_path.read_text(encoding="utf-8-sig"))
    _validate_segments(segments)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps({"segments": transcript_segments_to_json(segments)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return ImportReport(
        source=source_path,
        output=output_path,
        segment_count=len(segments),
        first_start=segments[0].start,
        last_end=segments[-1].end,
    )
