from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from podcast_pipeline.schemas import EditSegment

OPENAI_AUDIO_UPLOAD_LIMIT_BYTES = 25 * 1024 * 1024
TRANSCRIPTION_AUDIO_BITRATE_KBPS = 64


@dataclass(frozen=True)
class ChunkPlan:
    chunk_id: str
    start: float
    end: float


def _read_windows_registry_path() -> str:
    if os.name != "nt":
        return ""
    try:
        import winreg
    except ImportError:
        return ""

    values: list[str] = []
    locations = [
        (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
        (winreg.HKEY_CURRENT_USER, r"Environment"),
    ]
    for root, subkey in locations:
        try:
            with winreg.OpenKey(root, subkey) as key:
                value, _ = winreg.QueryValueEx(key, "Path")
                values.append(os.path.expandvars(value))
        except OSError:
            continue
    return os.pathsep.join(values)


def refresh_path_from_persistent_environment() -> None:
    registry_path = _read_windows_registry_path()
    if not registry_path:
        return
    merged: list[str] = []
    seen: set[str] = set()
    for path_value in (os.environ.get("PATH", ""), registry_path):
        for entry in path_value.split(os.pathsep):
            entry = entry.strip()
            if not entry:
                continue
            key = os.path.normcase(os.path.normpath(entry.strip('"')))
            if key in seen:
                continue
            seen.add(key)
            merged.append(entry)
    os.environ["PATH"] = os.pathsep.join(merged)


def audio_tool_paths() -> dict[str, str | None]:
    refresh_path_from_persistent_environment()
    return {name: shutil.which(name) for name in ("ffmpeg", "ffprobe")}


def missing_audio_tools() -> list[str]:
    return [name for name, path in audio_tool_paths().items() if path is None]


def require_audio_tools() -> None:
    missing = missing_audio_tools()
    if missing:
        names = ", ".join(missing)
        raise RuntimeError(f"Missing audio tools: {names}. Install ffmpeg and ensure it is on PATH.")


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
    require_audio_tools()
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
    require_audio_tools()
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


def create_silence_chunk(destination: Path, duration: float) -> None:
    require_audio_tools()
    destination.parent.mkdir(parents=True, exist_ok=True)
    run_command(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=channel_layout=stereo:sample_rate=48000",
            "-t",
            f"{duration:.3f}",
            "-acodec",
            "pcm_s16le",
            "-ar",
            "48000",
            str(destination),
        ]
    )


def estimated_transcription_chunk_bytes(
    duration_seconds: float,
    bitrate_kbps: int = TRANSCRIPTION_AUDIO_BITRATE_KBPS,
) -> int:
    # AAC container overhead is small, but keep a little margin for safety.
    return int((duration_seconds * bitrate_kbps * 1000 / 8) * 1.05)


def extract_transcription_chunk(source: Path, destination: Path, start: float, end: float) -> None:
    require_audio_tools()
    duration = end - start
    estimated_bytes = estimated_transcription_chunk_bytes(duration)
    if estimated_bytes >= OPENAI_AUDIO_UPLOAD_LIMIT_BYTES:
        raise RuntimeError(
            "Transcription chunk is expected to exceed the OpenAI audio upload limit. "
            "Use a shorter chunk duration or lower bitrate."
        )
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
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-c:a",
            "aac",
            "-b:a",
            f"{TRANSCRIPTION_AUDIO_BITRATE_KBPS}k",
            str(destination),
        ]
    )
    if destination.exists() and destination.stat().st_size >= OPENAI_AUDIO_UPLOAD_LIMIT_BYTES:
        raise RuntimeError(
            f"Transcription chunk {destination} is too large for upload "
            f"({destination.stat().st_size} bytes)."
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
        if segment.source == "silence":
            create_silence_chunk(segment_path, segment.end - segment.start)
        else:
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
