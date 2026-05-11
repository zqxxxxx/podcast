import os
from pathlib import Path

from podcast_pipeline.audio import (
    ChunkPlan,
    create_silence_chunk,
    build_chunk_plan,
    estimated_transcription_chunk_bytes,
    extract_transcription_chunk,
    format_timestamp,
    missing_audio_tools,
    parse_timestamp,
    refresh_path_from_persistent_environment,
)


def test_format_and_parse_timestamp():
    assert format_timestamp(3723.456) == "01:02:03.456"
    assert parse_timestamp("01:02:03.456") == 3723.456


def test_build_chunk_plan_uses_overlap():
    chunks = build_chunk_plan(total_seconds=3700, chunk_seconds=1800, overlap_seconds=5)
    assert chunks == [
        ChunkPlan(chunk_id="chunk_000", start=0, end=1800),
        ChunkPlan(chunk_id="chunk_001", start=1795, end=3595),
        ChunkPlan(chunk_id="chunk_002", start=3590, end=3700),
    ]


def test_missing_audio_tools_uses_tool_paths(monkeypatch):
    monkeypatch.setattr("podcast_pipeline.audio.audio_tool_paths", lambda: {"ffmpeg": "ffmpeg.exe", "ffprobe": None})
    assert missing_audio_tools() == ["ffprobe"]


def test_refresh_path_from_persistent_environment_is_idempotent(monkeypatch):
    existing = os.pathsep.join(["C:\\tools", "C:\\ffmpeg\\bin"])
    registry = os.pathsep.join(["C:\\ffmpeg\\bin", "C:\\other"])
    monkeypatch.setenv("PATH", existing)
    monkeypatch.setattr("podcast_pipeline.audio._read_windows_registry_path", lambda: registry)

    refresh_path_from_persistent_environment()
    refresh_path_from_persistent_environment()

    path_entries = [entry for entry in os.environ["PATH"].split(os.pathsep) if entry]
    assert path_entries.count("C:\\ffmpeg\\bin") == 1
    assert path_entries.count("C:\\other") == 1


def test_default_transcription_chunk_stays_below_upload_limit():
    assert estimated_transcription_chunk_bytes(duration_seconds=1800) < 25 * 1024 * 1024


def test_extract_transcription_chunk_writes_compressed_m4a(monkeypatch, tmp_path):
    captured_args = []

    def fake_run_command(args):
        captured_args.append(args)

    monkeypatch.setattr("podcast_pipeline.audio.require_audio_tools", lambda: None)
    monkeypatch.setattr("podcast_pipeline.audio.run_command", fake_run_command)

    destination = tmp_path / "chunk_000.m4a"
    extract_transcription_chunk(Path("source.m4a"), destination, start=0, end=1800)

    args = captured_args[0]
    assert args[-1] == str(destination)
    assert "-vn" in args
    assert args[args.index("-ac") + 1] == "1"
    assert args[args.index("-ar") + 1] == "16000"
    assert args[args.index("-c:a") + 1] == "aac"
    assert args[args.index("-b:a") + 1] == "64k"


def test_create_silence_chunk_uses_anullsrc(monkeypatch, tmp_path):
    captured_args = []

    def fake_run_command(args):
        captured_args.append(args)

    monkeypatch.setattr("podcast_pipeline.audio.require_audio_tools", lambda: None)
    monkeypatch.setattr("podcast_pipeline.audio.run_command", fake_run_command)

    destination = tmp_path / "silence.wav"
    create_silence_chunk(destination, duration=1.0)

    args = captured_args[0]
    assert "anullsrc=channel_layout=stereo:sample_rate=48000" in args
    assert args[args.index("-t") + 1] == "1.000"
    assert args[-1] == str(destination)
