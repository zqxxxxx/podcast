from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from podcast_pipeline.schemas import EditSegment


@dataclass(frozen=True)
class ChunkPlan:
    chunk_id: str
    start: float
    end: float


def format_timestamp(seconds: float) -> str:
    milliseconds = int(round((seconds - int(seconds)) * 1000))
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    if milliseconds == 1000:
        total_seconds += 1
        milliseconds = 0
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
    return f"{hours:02}:{minutes:02}:{secs:02}.{milliseconds:03}"


def parse_timestamp(value: str) -> float:
    hours_text, minutes_text, seconds_text = value.split(":")
    seconds = float(seconds_text)
    return round((int(hours_text) * 3600) + (int(minutes_text) * 60) + seconds, 3)


def build_chunk_plan(
    total_seconds: float,
    chunk_seconds: int = 1800,
    overlap_seconds: int = 5,
) -> list[ChunkPlan]:
    chunks: list[ChunkPlan] = []
    start = 0.0
    index = 0
    while start < total_seconds:
        end = min(start + chunk_seconds, total_seconds)
        chunks.append(ChunkPlan(chunk_id=f"chunk_{index:03}", start=round(start, 3), end=round(end, 3)))
        if end >= total_seconds:
            break
        start = max(0.0, end - overlap_seconds)
        index += 1
    return chunks


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=True, text=True, capture_output=True)


def ffprobe_duration(audio_path: Path) -> float:
    result = run_command(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(audio_path),
        ]
    )
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])


def extract_chunk(source: Path, destination: Path, start: float, end: float) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    run_command(
        [
            "ffmpeg",
            "-y",
            "-ss",
            format_timestamp(start),
            "-to",
            format_timestamp(end),
            "-i",
            str(source),
            "-acodec",
            "pcm_s16le",
            "-ar",
            "48000",
            str(destination),
        ]
    )


def write_concat_file(segment_paths: list[Path], concat_file: Path) -> None:
    concat_file.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"file '{path.as_posix()}'" for path in segment_paths]
    concat_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def assemble_segments(
    source: Path,
    segments: list[EditSegment],
    work_dir: Path,
    output_path: Path,
) -> None:
    work_dir.mkdir(parents=True, exist_ok=True)
    segment_paths: list[Path] = []
    for index, segment in enumerate(segments):
        segment_path = work_dir / f"segment_{index:04}.wav"
        extract_chunk(source, segment_path, segment.start, segment.end)
        segment_paths.append(segment_path)
    concat_file = work_dir / "concat.txt"
    write_concat_file(segment_paths, concat_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    run_command(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-c",
            "copy",
            str(output_path),
        ]
    )
