# Podcast Production Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a command-line AI podcast production pipeline that turns a 3-hour Chinese interview recording plus an outline into calibrated demos, an approved editing style guide, a 50-55 minute rough cut, post-production handoff files, and publishing assets.

**Architecture:** Use a small Python package with focused modules for config, schemas, audio utilities, transcription, LLM-driven content decisions, demo calibration, assembly, and publishing assets. Keep external audio cleanup as documented handoff files in version one, while making all AI and ffmpeg stages restartable through inspectable intermediate JSON/Markdown files.

**Tech Stack:** Python 3.13, OpenAI Python SDK, ffmpeg/ffprobe, PyYAML, pytest, standard-library dataclasses/subprocess/json/pathlib.

---

## Implementation Notes

The current workspace is not a git repository. Do not add mandatory `git commit` steps unless the user initializes git later. Use verification checkpoints instead.

Create English project documents under `docs/`. Create Chinese reading copies under `C:\work\Vibe2\用于阅读` when adding or updating project documents, but do not read from that Chinese folder unless the user explicitly asks.

Use `whisper-1` as the default timestamped transcription model because the OpenAI API reference documents `verbose_json` and segment/word timestamp granularities for audio transcriptions. Keep the model configurable. Use one OpenAI wrapper file so future API changes are localized.

Version one intentionally supports manual Cleanvoice/Auphonic handoff instead of API automation.

---

## File Structure

Create this structure:

```text
C:\work\Vibe2\
  pyproject.toml
  README.md
  config.example.yaml
  podcast_pipeline\
    __init__.py
    __main__.py
    cli.py
    config.py
    schemas.py
    audio.py
    llm.py
    transcribe.py
    content_map.py
    demo.py
    style.py
    edit_decision.py
    assemble.py
    publish_assets.py
    postproduction.py
    prompts\
      content_map.md
      demo_selection.md
      demo_feedback.md
      style_freeze.md
      final_edit_decision.md
      shownotes.md
  inputs\
    audio\
    outline.md
  outputs\
    transcript\
    content_map\
    demos\
    style\
    postproduction\
  tests\
    fixtures\
    test_config.py
    test_schemas.py
    test_audio.py
    test_transcribe.py
    test_content_map.py
    test_demo.py
    test_style.py
    test_edit_decision.py
    test_publish_assets.py
    test_cli.py
```

---

### Task 1: Project Skeleton And Tooling

**Files:**
- Create: `C:\work\Vibe2\pyproject.toml`
- Create: `C:\work\Vibe2\README.md`
- Create: `C:\work\Vibe2\config.example.yaml`
- Create: `C:\work\Vibe2\podcast_pipeline\__init__.py`
- Create: `C:\work\Vibe2\podcast_pipeline\__main__.py`
- Create: `C:\work\Vibe2\podcast_pipeline\cli.py`
- Create: `C:\work\Vibe2\inputs\outline.md`
- Create: output/input directories listed above
- Test: `C:\work\Vibe2\tests\test_cli.py`

- [ ] **Step 1: Create the package directories**

Run:

```powershell
New-Item -ItemType Directory -Force -Path `
  .\podcast_pipeline\prompts, `
  .\inputs\audio, `
  .\outputs\transcript, `
  .\outputs\content_map, `
  .\outputs\demos, `
  .\outputs\style, `
  .\outputs\postproduction, `
  .\tests\fixtures | Out-Null
```

Expected: directories exist with no error.

- [ ] **Step 2: Write `pyproject.toml`**

```toml
[project]
name = "podcast-production-pipeline"
version = "0.1.0"
description = "AI-assisted Chinese podcast editing pipeline"
requires-python = ">=3.13"
dependencies = [
  "openai>=1.0.0",
  "PyYAML>=6.0.0"
]

[project.optional-dependencies]
dev = [
  "pytest>=8.0.0"
]

[project.scripts]
podcast-pipeline = "podcast_pipeline.cli:main"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

- [ ] **Step 3: Write `podcast_pipeline/__init__.py`**

```python
"""AI-assisted Chinese podcast production pipeline."""

__version__ = "0.1.0"
```

- [ ] **Step 4: Write `podcast_pipeline/__main__.py`**

```python
from podcast_pipeline.cli import main

if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Write a minimal `cli.py` with a smoke-testable entrypoint**

```python
from __future__ import annotations

import argparse
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="podcast-pipeline")
    parser.add_argument("--version", action="store_true", help="Show package version.")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("doctor", help="Check local requirements.")
    return parser


def run_doctor() -> int:
    print("podcast-pipeline: initial doctor check")
    print(f"workspace: {Path.cwd()}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.version:
        from podcast_pipeline import __version__

        print(__version__)
        return 0
    if args.command == "doctor":
        return run_doctor()
    parser.print_help()
    return 0
```

- [ ] **Step 6: Write `tests/test_cli.py`**

```python
from podcast_pipeline.cli import main


def test_main_version(capsys):
    exit_code = main(["--version"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "0.1.0" in captured.out


def test_main_help(capsys):
    exit_code = main([])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "podcast-pipeline" in captured.out
```

- [ ] **Step 7: Run the smoke test**

Run:

```powershell
python -m pytest tests/test_cli.py -q
```

Expected: `2 passed`.

---

### Task 2: Configuration And Schemas

**Files:**
- Create: `C:\work\Vibe2\podcast_pipeline\config.py`
- Create: `C:\work\Vibe2\podcast_pipeline\schemas.py`
- Modify: `C:\work\Vibe2\config.example.yaml`
- Test: `C:\work\Vibe2\tests\test_config.py`
- Test: `C:\work\Vibe2\tests\test_schemas.py`

- [ ] **Step 1: Write `config.example.yaml`**

```yaml
project:
  name: chinese-podcast-episode
  workspace: .

inputs:
  audio: inputs/audio/raw_episode.wav
  outline: inputs/outline.md

outputs:
  root: outputs

openai:
  api_key_env: OPENAI_API_KEY
  transcription_model: whisper-1
  text_model: ${OPENAI_TEXT_MODEL}

editing:
  language: zh
  final_min_minutes: 50
  final_max_minutes: 55
  demo_min_minutes: 6
  demo_max_minutes: 10
  demo_candidate_min_minutes: 12
  demo_candidate_max_minutes: 18
  min_segment_seconds: 20
  crossfade_ms: 80
  conservative_semantic_cuts: true

postproduction:
  cleanvoice_mode: manual_light_cleanup
  auphonic_mode: manual_mastering
  adobe_podcast_mode: fallback_only
```

- [ ] **Step 2: Write `config.py`**

```python
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ProjectConfig:
    name: str
    workspace: Path
    audio_path: Path
    outline_path: Path
    outputs_root: Path
    openai_api_key_env: str
    transcription_model: str
    text_model: str
    language: str
    final_min_seconds: int
    final_max_seconds: int
    demo_min_seconds: int
    demo_max_seconds: int
    demo_candidate_min_seconds: int
    demo_candidate_max_seconds: int
    min_segment_seconds: int
    crossfade_ms: int
    conservative_semantic_cuts: bool
    cleanvoice_mode: str
    auphonic_mode: str
    adobe_podcast_mode: str


def _expand_env(value: str) -> str:
    if value.startswith("${") and value.endswith("}"):
        env_name = value[2:-1]
        resolved = os.getenv(env_name)
        if not resolved:
            raise ValueError(f"Environment variable {env_name} is required.")
        return resolved
    return value


def _minutes_to_seconds(value: int | float) -> int:
    return int(float(value) * 60)


def load_config(path: str | Path) -> ProjectConfig:
    config_path = Path(path)
    data: dict[str, Any] = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    workspace = (config_path.parent / data["project"].get("workspace", ".")).resolve()

    audio_path = (workspace / data["inputs"]["audio"]).resolve()
    outline_path = (workspace / data["inputs"]["outline"]).resolve()
    outputs_root = (workspace / data["outputs"]["root"]).resolve()

    editing = data["editing"]
    postproduction = data["postproduction"]
    openai = data["openai"]

    return ProjectConfig(
        name=data["project"]["name"],
        workspace=workspace,
        audio_path=audio_path,
        outline_path=outline_path,
        outputs_root=outputs_root,
        openai_api_key_env=openai.get("api_key_env", "OPENAI_API_KEY"),
        transcription_model=openai.get("transcription_model", "whisper-1"),
        text_model=_expand_env(openai["text_model"]),
        language=editing.get("language", "zh"),
        final_min_seconds=_minutes_to_seconds(editing["final_min_minutes"]),
        final_max_seconds=_minutes_to_seconds(editing["final_max_minutes"]),
        demo_min_seconds=_minutes_to_seconds(editing["demo_min_minutes"]),
        demo_max_seconds=_minutes_to_seconds(editing["demo_max_minutes"]),
        demo_candidate_min_seconds=_minutes_to_seconds(editing["demo_candidate_min_minutes"]),
        demo_candidate_max_seconds=_minutes_to_seconds(editing["demo_candidate_max_minutes"]),
        min_segment_seconds=int(editing.get("min_segment_seconds", 20)),
        crossfade_ms=int(editing.get("crossfade_ms", 80)),
        conservative_semantic_cuts=bool(editing.get("conservative_semantic_cuts", True)),
        cleanvoice_mode=postproduction["cleanvoice_mode"],
        auphonic_mode=postproduction["auphonic_mode"],
        adobe_podcast_mode=postproduction["adobe_podcast_mode"],
    )
```

- [ ] **Step 3: Write `schemas.py`**

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TranscriptSegment:
    start: float
    end: float
    text: str
    speaker: str | None = None
    chunk_id: str | None = None


@dataclass(frozen=True)
class ContentBlock:
    start: float
    end: float
    topic: str
    outline_relation: str
    summary: str
    highlight_score: int
    deletion_score: int
    notes: str


@dataclass(frozen=True)
class EditSegment:
    start: float
    end: float
    reason: str
    source: str = "raw"
    labels: list[str] = field(default_factory=list)


def segment_duration(segment: TranscriptSegment | ContentBlock | EditSegment) -> float:
    return round(segment.end - segment.start, 3)


def total_edit_duration(segments: list[EditSegment]) -> float:
    return round(sum(segment_duration(segment) for segment in segments), 3)


def validate_time_range(start: float, end: float, label: str) -> None:
    if start < 0:
        raise ValueError(f"{label} start must be non-negative.")
    if end <= start:
        raise ValueError(f"{label} end must be greater than start.")


def validate_edit_segments(segments: list[EditSegment]) -> None:
    previous_start = -1.0
    for index, segment in enumerate(segments):
        validate_time_range(segment.start, segment.end, f"segment {index}")
        if segment.start < previous_start:
            raise ValueError("Edit segments must be sorted by source start time.")
        if not segment.reason.strip():
            raise ValueError(f"segment {index} requires a reason.")
        previous_start = segment.start


def transcript_segment_from_dict(data: dict[str, Any]) -> TranscriptSegment:
    return TranscriptSegment(
        start=float(data["start"]),
        end=float(data["end"]),
        text=str(data["text"]),
        speaker=data.get("speaker"),
        chunk_id=data.get("chunk_id"),
    )


def edit_segment_from_dict(data: dict[str, Any]) -> EditSegment:
    labels = data.get("labels") or []
    if not isinstance(labels, list):
        raise ValueError("labels must be a list.")
    return EditSegment(
        start=float(data["start"]),
        end=float(data["end"]),
        reason=str(data["reason"]),
        source=str(data.get("source", "raw")),
        labels=[str(label) for label in labels],
    )


def edit_segment_to_dict(segment: EditSegment) -> dict[str, Any]:
    return {
        "start": segment.start,
        "end": segment.end,
        "duration": segment_duration(segment),
        "reason": segment.reason,
        "source": segment.source,
        "labels": segment.labels,
    }
```

- [ ] **Step 4: Write config tests**

```python
from pathlib import Path

import pytest

from podcast_pipeline.config import load_config


def test_load_config_expands_paths_and_minutes(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_TEXT_MODEL", "test-text-model")
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
project:
  name: test
  workspace: .
inputs:
  audio: inputs/audio/raw.wav
  outline: inputs/outline.md
outputs:
  root: outputs
openai:
  api_key_env: OPENAI_API_KEY
  transcription_model: whisper-1
  text_model: ${OPENAI_TEXT_MODEL}
editing:
  language: zh
  final_min_minutes: 50
  final_max_minutes: 55
  demo_min_minutes: 6
  demo_max_minutes: 10
  demo_candidate_min_minutes: 12
  demo_candidate_max_minutes: 18
  min_segment_seconds: 20
  crossfade_ms: 80
  conservative_semantic_cuts: true
postproduction:
  cleanvoice_mode: manual_light_cleanup
  auphonic_mode: manual_mastering
  adobe_podcast_mode: fallback_only
""",
        encoding="utf-8",
    )
    config = load_config(config_file)
    assert config.workspace == tmp_path.resolve()
    assert config.audio_path == (tmp_path / "inputs/audio/raw.wav").resolve()
    assert config.text_model == "test-text-model"
    assert config.final_min_seconds == 3000
    assert config.demo_max_seconds == 600


def test_load_config_requires_text_model_env(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_TEXT_MODEL", raising=False)
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        Path("config.example.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="OPENAI_TEXT_MODEL"):
        load_config(config_file)
```

- [ ] **Step 5: Write schema tests**

```python
import pytest

from podcast_pipeline.schemas import (
    EditSegment,
    edit_segment_from_dict,
    total_edit_duration,
    validate_edit_segments,
)


def test_validate_edit_segments_requires_sorted_segments():
    segments = [
        EditSegment(start=10, end=20, reason="later"),
        EditSegment(start=5, end=8, reason="earlier"),
    ]
    with pytest.raises(ValueError, match="sorted"):
        validate_edit_segments(segments)


def test_total_edit_duration():
    segments = [
        EditSegment(start=0, end=10, reason="opening"),
        EditSegment(start=20, end=35.5, reason="story"),
    ]
    assert total_edit_duration(segments) == 25.5


def test_edit_segment_from_dict_defaults_source_and_labels():
    segment = edit_segment_from_dict({"start": 1, "end": 2, "reason": "keep"})
    assert segment.source == "raw"
    assert segment.labels == []
```

- [ ] **Step 6: Run tests**

Run:

```powershell
python -m pytest tests/test_config.py tests/test_schemas.py -q
```

Expected: all tests pass.

---

### Task 3: Audio Utilities

**Files:**
- Create: `C:\work\Vibe2\podcast_pipeline\audio.py`
- Test: `C:\work\Vibe2\tests\test_audio.py`

- [ ] **Step 1: Write failing tests for timestamp formatting and chunk planning**

```python
from podcast_pipeline.audio import ChunkPlan, build_chunk_plan, format_timestamp, parse_timestamp


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
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```powershell
python -m pytest tests/test_audio.py -q
```

Expected: FAIL because `podcast_pipeline.audio` does not exist.

- [ ] **Step 3: Implement `audio.py`**

```python
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
```

- [ ] **Step 4: Run audio tests**

Run:

```powershell
python -m pytest tests/test_audio.py -q
```

Expected: `2 passed`.

- [ ] **Step 5: Add a doctor check for ffmpeg and ffprobe**

Modify `cli.py`:

```python
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="podcast-pipeline")
    parser.add_argument("--version", action="store_true", help="Show package version.")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("doctor", help="Check local requirements.")
    return parser


def run_doctor() -> int:
    print(f"workspace: {Path.cwd()}")
    missing = []
    for executable in ("ffmpeg", "ffprobe"):
        resolved = shutil.which(executable)
        if resolved:
            print(f"{executable}: {resolved}")
        else:
            print(f"{executable}: missing")
            missing.append(executable)
    if missing:
        print("Install missing audio tools before running assembly commands.")
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.version:
        from podcast_pipeline import __version__

        print(__version__)
        return 0
    if args.command == "doctor":
        return run_doctor()
    parser.print_help()
    return 0
```

- [ ] **Step 6: Update CLI test for doctor output**

```python
from podcast_pipeline.cli import main


def test_main_version(capsys):
    exit_code = main(["--version"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "0.1.0" in captured.out


def test_main_help(capsys):
    exit_code = main([])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "podcast-pipeline" in captured.out


def test_doctor_reports_workspace(capsys):
    exit_code = main(["doctor"])
    captured = capsys.readouterr()
    assert exit_code in (0, 1)
    assert "workspace:" in captured.out
```

- [ ] **Step 7: Run CLI and audio tests**

Run:

```powershell
python -m pytest tests/test_cli.py tests/test_audio.py -q
```

Expected: all tests pass.

---

### Task 4: Transcription Pipeline

**Files:**
- Create: `C:\work\Vibe2\podcast_pipeline\transcribe.py`
- Modify: `C:\work\Vibe2\podcast_pipeline\cli.py`
- Test: `C:\work\Vibe2\tests\test_transcribe.py`

- [ ] **Step 1: Write tests for merging chunk-relative timestamps**

```python
from podcast_pipeline.transcribe import merge_chunk_segments


def test_merge_chunk_segments_adds_chunk_offsets_and_drops_overlap_duplicates():
    chunks = [
        {
            "chunk_id": "chunk_000",
            "offset": 0,
            "segments": [
                {"start": 0, "end": 4, "text": "开场"},
                {"start": 1796, "end": 1800, "text": "重叠句"},
            ],
        },
        {
            "chunk_id": "chunk_001",
            "offset": 1795,
            "segments": [
                {"start": 0, "end": 4, "text": "重叠句"},
                {"start": 10, "end": 15, "text": "新内容"},
            ],
        },
    ]
    merged = merge_chunk_segments(chunks, duplicate_window_seconds=6)
    assert [segment.text for segment in merged] == ["开场", "重叠句", "新内容"]
    assert merged[-1].start == 1805
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```powershell
python -m pytest tests/test_transcribe.py -q
```

Expected: FAIL because `transcribe.py` does not exist.

- [ ] **Step 3: Implement `transcribe.py`**

```python
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from openai import OpenAI

from podcast_pipeline.audio import ChunkPlan, build_chunk_plan, extract_chunk, ffprobe_duration
from podcast_pipeline.config import ProjectConfig
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
    api_key = os.getenv(config.openai_api_key_env)
    if not api_key:
        raise ValueError(f"{config.openai_api_key_env} is required.")
    client = OpenAI(api_key=api_key)
    total_seconds = ffprobe_duration(config.audio_path)
    chunk_plans: list[ChunkPlan] = build_chunk_plan(total_seconds, chunk_seconds=chunk_seconds)
    chunk_dir = config.outputs_root / "transcript" / "chunks"
    raw_payloads: list[dict[str, Any]] = []

    for chunk in chunk_plans:
        chunk_audio = chunk_dir / f"{chunk.chunk_id}.wav"
        chunk_json = chunk_dir / f"{chunk.chunk_id}.json"
        if not chunk_json.exists():
            extract_chunk(config.audio_path, chunk_audio, chunk.start, chunk.end)
            payload = transcribe_audio_file(client, chunk_audio, config.transcription_model, config.language)
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
```

- [ ] **Step 4: Run transcription tests**

Run:

```powershell
python -m pytest tests/test_transcribe.py -q
```

Expected: tests pass.

- [ ] **Step 5: Add CLI command for transcription**

Modify `build_parser()` in `cli.py`:

```python
    transcribe_parser = subparsers.add_parser("transcribe", help="Create timestamped transcript.")
    transcribe_parser.add_argument("--config", default="config.example.yaml")
```

Modify `main()` in `cli.py`:

```python
    if args.command == "transcribe":
        from podcast_pipeline.config import load_config
        from podcast_pipeline.transcribe import create_transcript

        output_path = create_transcript(load_config(args.config))
        print(output_path)
        return 0
```

- [ ] **Step 6: Run CLI tests again**

Run:

```powershell
python -m pytest tests/test_cli.py tests/test_transcribe.py -q
```

Expected: all tests pass.

---

### Task 5: LLM Wrapper And Prompt Templates

**Files:**
- Create: `C:\work\Vibe2\podcast_pipeline\llm.py`
- Create: prompt files under `C:\work\Vibe2\podcast_pipeline\prompts\`
- Test: add fake-client tests inside later module tests

- [ ] **Step 1: Implement one JSON-producing LLM wrapper**

```python
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from openai import OpenAI


class LLMClient:
    def __init__(self, model: str, api_key_env: str = "OPENAI_API_KEY") -> None:
        api_key = os.getenv(api_key_env)
        if not api_key:
            raise ValueError(f"{api_key_env} is required.")
        self.model = model
        self.client = OpenAI(api_key=api_key)

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        response = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            text={"format": {"type": "json_object"}},
        )
        return json.loads(response.output_text)


def load_prompt(name: str) -> str:
    prompt_path = Path(__file__).parent / "prompts" / name
    return prompt_path.read_text(encoding="utf-8")
```

- [ ] **Step 2: Create `prompts/content_map.md`**

```markdown
You are an editorial analyst for a Chinese long-form interview podcast.

Return strict JSON with this shape:
{
  "blocks": [
    {
      "start": 0.0,
      "end": 120.0,
      "topic": "topic label",
      "outline_relation": "how this relates to the outline",
      "summary": "concise Chinese summary",
      "highlight_score": 1,
      "deletion_score": 1,
      "notes": "why this block matters or can be removed"
    }
  ]
}

Scores are integers from 1 to 5.
Favor complete semantic blocks. Do not invent timestamps.
```

- [ ] **Step 3: Create `prompts/demo_selection.md`**

```markdown
You are selecting a 6-10 minute demo cut from a longer Chinese podcast interview.

Return strict JSON:
{
  "candidate_reason": "why these segments calibrate the editing style",
  "segments": [
    {
      "start": 0.0,
      "end": 60.0,
      "reason": "why this segment belongs in the demo",
      "labels": ["story"]
    }
  ]
}

The demo must include a representative blend of story, insight, host follow-up, natural transition, and pacing/silence test material when available.
Avoid using only the beginning of the episode.
Keep source timestamps from the raw audio.
```

- [ ] **Step 4: Create `prompts/demo_feedback.md`**

```markdown
You revise demo editing rules based on user feedback.

Return strict JSON:
{
  "feedback_summary": "concise summary in Chinese",
  "rule_changes": [
    "specific durable rule"
  ],
  "segments_to_prefer": [
    "specific type of segment to keep"
  ],
  "segments_to_reduce": [
    "specific type of segment to remove or shorten"
  ]
}

Transform subjective feedback into reusable editorial rules.
```

- [ ] **Step 5: Create `prompts/style_freeze.md`**

```markdown
You create a durable editing style guide for a Chinese interview podcast after the user approves a demo.

Return strict JSON:
{
  "style_guide_markdown": "# Editing Style Guide\n...",
  "selection_rules": {
    "prefer": [],
    "reduce": [],
    "target_story_to_insight_ratio": ""
  },
  "cutting_rules": {
    "pacing": "",
    "minimum_segment_seconds": 20,
    "natural_pause_policy": "",
    "chinese_filler_word_policy": ""
  }
}

Be specific enough that another AI editing pass can follow the rules without asking for clarification.
```

- [ ] **Step 6: Create `prompts/final_edit_decision.md`**

```markdown
You are making the final 50-55 minute edit decision list for a Chinese interview podcast.

Return strict JSON:
{
  "segments": [
    {
      "start": 0.0,
      "end": 120.0,
      "reason": "why this raw-audio range is kept",
      "labels": ["story", "outline-section-1"]
    }
  ],
  "total_target_reasoning": "why this edit satisfies the style guide"
}

Use raw audio timestamps. Prefer complete semantic segments. Avoid excessive micro-cuts.
```

- [ ] **Step 7: Create `prompts/shownotes.md`**

```markdown
You create Chinese publishing assets for a finished podcast episode.

Return strict JSON:
{
  "title_candidates": [],
  "summary": "",
  "chapters": [
    {"time": "00:00:00", "title": ""}
  ],
  "shownotes_markdown": "# Show Notes\n..."
}

Chapter times must refer to final episode time, not raw audio time.
```

---

### Task 6: Content Map Generation

**Files:**
- Create: `C:\work\Vibe2\podcast_pipeline\content_map.py`
- Modify: `C:\work\Vibe2\podcast_pipeline\cli.py`
- Test: `C:\work\Vibe2\tests\test_content_map.py`

- [ ] **Step 1: Write tests with a fake LLM**

```python
import json

from podcast_pipeline.content_map import build_content_map


class FakeLLM:
    def generate_json(self, system_prompt, user_prompt):
        return {
            "blocks": [
                {
                    "start": 0,
                    "end": 90,
                    "topic": "开场故事",
                    "outline_relation": "对应第一部分",
                    "summary": "嘉宾讲述背景。",
                    "highlight_score": 5,
                    "deletion_score": 1,
                    "notes": "故事性强",
                }
            ]
        }


def test_build_content_map_writes_blocks(tmp_path):
    transcript = tmp_path / "transcript.json"
    outline = tmp_path / "outline.md"
    output = tmp_path / "content_map.json"
    transcript.write_text(json.dumps({"segments": [{"start": 0, "end": 90, "text": "测试"}]}, ensure_ascii=False), encoding="utf-8")
    outline.write_text("# 大纲", encoding="utf-8")

    build_content_map(FakeLLM(), transcript, outline, output)

    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["blocks"][0]["topic"] == "开场故事"
```

- [ ] **Step 2: Implement `content_map.py`**

```python
from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from podcast_pipeline.llm import load_prompt


class JsonLLM(Protocol):
    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        ...


def build_content_map(
    llm: JsonLLM,
    transcript_path: Path,
    outline_path: Path,
    output_path: Path,
) -> Path:
    transcript_text = transcript_path.read_text(encoding="utf-8")
    outline_text = outline_path.read_text(encoding="utf-8")
    system_prompt = load_prompt("content_map.md")
    user_prompt = (
        "Interview outline:\n"
        f"{outline_text}\n\n"
        "Transcript JSON:\n"
        f"{transcript_text}\n"
    )
    result = llm.generate_json(system_prompt, user_prompt)
    if "blocks" not in result or not isinstance(result["blocks"], list):
        raise ValueError("Content map result must contain a blocks list.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path
```

- [ ] **Step 3: Add CLI command**

Add parser:

```python
    content_map_parser = subparsers.add_parser("content-map", help="Create content map.")
    content_map_parser.add_argument("--config", default="config.example.yaml")
```

Add command:

```python
    if args.command == "content-map":
        from podcast_pipeline.config import load_config
        from podcast_pipeline.content_map import build_content_map
        from podcast_pipeline.llm import LLMClient

        config = load_config(args.config)
        output_path = build_content_map(
            LLMClient(config.text_model, config.openai_api_key_env),
            config.outputs_root / "transcript" / "transcript.json",
            config.outline_path,
            config.outputs_root / "content_map" / "content_map.json",
        )
        print(output_path)
        return 0
```

- [ ] **Step 4: Run content map tests**

Run:

```powershell
python -m pytest tests/test_content_map.py -q
```

Expected: tests pass.

---

### Task 7: Demo Selection And Demo Assembly

**Files:**
- Create: `C:\work\Vibe2\podcast_pipeline\demo.py`
- Create: `C:\work\Vibe2\podcast_pipeline\assemble.py`
- Modify: `C:\work\Vibe2\podcast_pipeline\cli.py`
- Test: `C:\work\Vibe2\tests\test_demo.py`

- [ ] **Step 1: Write tests for demo duration validation**

```python
import json

import pytest

from podcast_pipeline.demo import create_demo_edl


class FakeLLM:
    def generate_json(self, system_prompt, user_prompt):
        return {
            "candidate_reason": "测试故事、观点和节奏",
            "segments": [
                {"start": 0, "end": 180, "reason": "故事", "labels": ["story"]},
                {"start": 300, "end": 540, "reason": "观点", "labels": ["insight"]},
            ],
        }


def test_create_demo_edl_writes_segments(tmp_path):
    transcript = tmp_path / "transcript.json"
    content_map = tmp_path / "content_map.json"
    output = tmp_path / "demo_v1_edit_decision_list.json"
    transcript.write_text(json.dumps({"segments": []}), encoding="utf-8")
    content_map.write_text(json.dumps({"blocks": []}), encoding="utf-8")

    create_demo_edl(FakeLLM(), transcript, content_map, output, min_seconds=360, max_seconds=600)

    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["candidate_reason"] == "测试故事、观点和节奏"
    assert len(data["segments"]) == 2


def test_create_demo_edl_rejects_too_short(tmp_path):
    class ShortLLM:
        def generate_json(self, system_prompt, user_prompt):
            return {"candidate_reason": "too short", "segments": [{"start": 0, "end": 10, "reason": "x"}]}

    transcript = tmp_path / "transcript.json"
    content_map = tmp_path / "content_map.json"
    output = tmp_path / "demo.json"
    transcript.write_text(json.dumps({"segments": []}), encoding="utf-8")
    content_map.write_text(json.dumps({"blocks": []}), encoding="utf-8")

    with pytest.raises(ValueError, match="Demo duration"):
        create_demo_edl(ShortLLM(), transcript, content_map, output, min_seconds=360, max_seconds=600)
```

- [ ] **Step 2: Implement `demo.py`**

```python
from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from podcast_pipeline.llm import load_prompt
from podcast_pipeline.schemas import edit_segment_from_dict, edit_segment_to_dict, total_edit_duration, validate_edit_segments


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
```

- [ ] **Step 3: Implement `assemble.py`**

```python
from __future__ import annotations

import json
from pathlib import Path

from podcast_pipeline.audio import assemble_segments
from podcast_pipeline.schemas import edit_segment_from_dict, total_edit_duration, validate_edit_segments


def load_edl(edl_path: Path):
    data = json.loads(edl_path.read_text(encoding="utf-8"))
    segments = [edit_segment_from_dict(item) for item in data["segments"]]
    validate_edit_segments(segments)
    return segments


def assemble_from_edl(source_audio: Path, edl_path: Path, work_dir: Path, output_path: Path) -> Path:
    segments = load_edl(edl_path)
    assemble_segments(source_audio, segments, work_dir, output_path)
    report_path = output_path.with_suffix(".report.json")
    report_path.write_text(
        json.dumps(
            {
                "source_audio": str(source_audio),
                "edl": str(edl_path),
                "output": str(output_path),
                "duration": total_edit_duration(segments),
                "segment_count": len(segments),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return output_path
```

- [ ] **Step 4: Add CLI commands `demo-edl` and `assemble-demo`**

Add parsers:

```python
    demo_parser = subparsers.add_parser("demo-edl", help="Create demo edit decision list.")
    demo_parser.add_argument("--config", default="config.example.yaml")
    demo_parser.add_argument("--version", default="v1")

    assemble_demo_parser = subparsers.add_parser("assemble-demo", help="Assemble demo audio from EDL.")
    assemble_demo_parser.add_argument("--config", default="config.example.yaml")
    assemble_demo_parser.add_argument("--version", default="v1")
```

Add command handlers:

```python
    if args.command == "demo-edl":
        from podcast_pipeline.config import load_config
        from podcast_pipeline.demo import create_demo_edl
        from podcast_pipeline.llm import LLMClient

        config = load_config(args.config)
        output_path = create_demo_edl(
            LLMClient(config.text_model, config.openai_api_key_env),
            config.outputs_root / "transcript" / "transcript.json",
            config.outputs_root / "content_map" / "content_map.json",
            config.outputs_root / "demos" / f"demo_{args.version}_edit_decision_list.json",
            config.demo_min_seconds,
            config.demo_max_seconds,
        )
        print(output_path)
        return 0

    if args.command == "assemble-demo":
        from podcast_pipeline.assemble import assemble_from_edl
        from podcast_pipeline.config import load_config

        config = load_config(args.config)
        output_path = assemble_from_edl(
            config.audio_path,
            config.outputs_root / "demos" / f"demo_{args.version}_edit_decision_list.json",
            config.outputs_root / "demos" / f"demo_{args.version}_parts",
            config.outputs_root / "demos" / f"demo_{args.version}.wav",
        )
        print(output_path)
        return 0
```

- [ ] **Step 5: Run demo tests**

Run:

```powershell
python -m pytest tests/test_demo.py -q
```

Expected: tests pass.

---

### Task 8: Feedback Ingestion And Style Freeze

**Files:**
- Create: `C:\work\Vibe2\podcast_pipeline\style.py`
- Modify: `C:\work\Vibe2\podcast_pipeline\cli.py`
- Test: `C:\work\Vibe2\tests\test_style.py`

- [ ] **Step 1: Write tests for feedback and style outputs**

```python
import json

from podcast_pipeline.style import freeze_style, ingest_demo_feedback


class FeedbackLLM:
    def generate_json(self, system_prompt, user_prompt):
        return {
            "feedback_summary": "用户希望故事更多、节奏更自然。",
            "rule_changes": ["优先保留完整故事段。"],
            "segments_to_prefer": ["故事段"],
            "segments_to_reduce": ["纯结论段"],
        }


class StyleLLM:
    def generate_json(self, system_prompt, user_prompt):
        return {
            "style_guide_markdown": "# Editing Style Guide\nPrefer complete stories.",
            "selection_rules": {"prefer": ["story"], "reduce": ["repetition"]},
            "cutting_rules": {"pacing": "natural", "minimum_segment_seconds": 20},
        }


def test_ingest_demo_feedback(tmp_path):
    output = tmp_path / "feedback.json"
    ingest_demo_feedback(FeedbackLLM(), "太碎，故事不够", output)
    data = json.loads(output.read_text(encoding="utf-8"))
    assert "故事" in data["feedback_summary"]


def test_freeze_style_writes_markdown_and_json(tmp_path):
    demo_edl = tmp_path / "demo.json"
    feedback = tmp_path / "feedback.json"
    style_dir = tmp_path / "style"
    demo_edl.write_text(json.dumps({"segments": []}), encoding="utf-8")
    feedback.write_text(json.dumps({"feedback_summary": "ok"}), encoding="utf-8")
    freeze_style(StyleLLM(), demo_edl, [feedback], style_dir)
    assert (style_dir / "edit_style_guide.md").exists()
    assert (style_dir / "selection_rules.json").exists()
    assert (style_dir / "cutting_rules.json").exists()
```

- [ ] **Step 2: Implement `style.py`**

```python
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
```

- [ ] **Step 3: Add CLI commands for feedback and style freeze**

Add parsers:

```python
    feedback_parser = subparsers.add_parser("demo-feedback", help="Ingest user feedback for a demo.")
    feedback_parser.add_argument("--config", default="config.example.yaml")
    feedback_parser.add_argument("--version", required=True)
    feedback_parser.add_argument("--feedback", required=True)

    freeze_parser = subparsers.add_parser("freeze-style", help="Freeze approved demo style.")
    freeze_parser.add_argument("--config", default="config.example.yaml")
    freeze_parser.add_argument("--approved-version", required=True)
```

Add handlers:

```python
    if args.command == "demo-feedback":
        from podcast_pipeline.config import load_config
        from podcast_pipeline.llm import LLMClient
        from podcast_pipeline.style import ingest_demo_feedback

        config = load_config(args.config)
        output_path = ingest_demo_feedback(
            LLMClient(config.text_model, config.openai_api_key_env),
            args.feedback,
            config.outputs_root / "demos" / f"demo_{args.version}_feedback.json",
        )
        print(output_path)
        return 0

    if args.command == "freeze-style":
        from podcast_pipeline.config import load_config
        from podcast_pipeline.llm import LLMClient
        from podcast_pipeline.style import freeze_style

        config = load_config(args.config)
        feedback_paths = sorted((config.outputs_root / "demos").glob("demo_*_feedback.json"))
        output_path = freeze_style(
            LLMClient(config.text_model, config.openai_api_key_env),
            config.outputs_root / "demos" / f"demo_{args.approved_version}_edit_decision_list.json",
            feedback_paths,
            config.outputs_root / "style",
        )
        print(output_path)
        return 0
```

- [ ] **Step 4: Run style tests**

Run:

```powershell
python -m pytest tests/test_style.py -q
```

Expected: tests pass.

---

### Task 9: Final Edit Decision And Rough Cut Assembly

**Files:**
- Create: `C:\work\Vibe2\podcast_pipeline\edit_decision.py`
- Modify: `C:\work\Vibe2\podcast_pipeline\cli.py`
- Test: `C:\work\Vibe2\tests\test_edit_decision.py`

- [ ] **Step 1: Write final EDL tests**

```python
import json

import pytest

from podcast_pipeline.edit_decision import create_final_edl


class FinalLLM:
    def generate_json(self, system_prompt, user_prompt):
        return {
            "segments": [
                {"start": 0, "end": 1800, "reason": "核心故事", "labels": ["story"]},
                {"start": 2400, "end": 3600, "reason": "关键观点", "labels": ["insight"]},
            ],
            "total_target_reasoning": "符合风格指南。",
        }


def test_create_final_edl_accepts_target_duration(tmp_path):
    for name in ["transcript.json", "content_map.json", "style.md", "selection.json", "cutting.json"]:
        (tmp_path / name).write_text("{}", encoding="utf-8")
    output = tmp_path / "edit_decision_list.json"
    create_final_edl(
        FinalLLM(),
        tmp_path / "transcript.json",
        tmp_path / "content_map.json",
        tmp_path / "style.md",
        tmp_path / "selection.json",
        tmp_path / "cutting.json",
        output,
        min_seconds=3000,
        max_seconds=3300,
    )
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["duration"] == 3000


def test_create_final_edl_rejects_out_of_range_duration(tmp_path):
    class ShortLLM:
        def generate_json(self, system_prompt, user_prompt):
            return {"segments": [{"start": 0, "end": 10, "reason": "too short"}]}

    for name in ["transcript.json", "content_map.json", "style.md", "selection.json", "cutting.json"]:
        (tmp_path / name).write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="Final EDL duration"):
        create_final_edl(
            ShortLLM(),
            tmp_path / "transcript.json",
            tmp_path / "content_map.json",
            tmp_path / "style.md",
            tmp_path / "selection.json",
            tmp_path / "cutting.json",
            tmp_path / "edit.json",
            min_seconds=3000,
            max_seconds=3300,
        )
```

- [ ] **Step 2: Implement `edit_decision.py`**

```python
from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from podcast_pipeline.llm import load_prompt
from podcast_pipeline.schemas import edit_segment_from_dict, edit_segment_to_dict, total_edit_duration, validate_edit_segments


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
```

- [ ] **Step 3: Add CLI commands `final-edl` and `assemble-final`**

Add parsers:

```python
    final_edl_parser = subparsers.add_parser("final-edl", help="Create final 50-55 minute EDL.")
    final_edl_parser.add_argument("--config", default="config.example.yaml")

    assemble_final_parser = subparsers.add_parser("assemble-final", help="Assemble rough cut from final EDL.")
    assemble_final_parser.add_argument("--config", default="config.example.yaml")
```

Add handlers:

```python
    if args.command == "final-edl":
        from podcast_pipeline.config import load_config
        from podcast_pipeline.edit_decision import create_final_edl
        from podcast_pipeline.llm import LLMClient

        config = load_config(args.config)
        output_path = create_final_edl(
            LLMClient(config.text_model, config.openai_api_key_env),
            config.outputs_root / "transcript" / "transcript.json",
            config.outputs_root / "content_map" / "content_map.json",
            config.outputs_root / "style" / "edit_style_guide.md",
            config.outputs_root / "style" / "selection_rules.json",
            config.outputs_root / "style" / "cutting_rules.json",
            config.outputs_root / "edit_decision_list.json",
            config.final_min_seconds,
            config.final_max_seconds,
        )
        print(output_path)
        return 0

    if args.command == "assemble-final":
        from podcast_pipeline.assemble import assemble_from_edl
        from podcast_pipeline.config import load_config

        config = load_config(args.config)
        output_path = assemble_from_edl(
            config.audio_path,
            config.outputs_root / "edit_decision_list.json",
            config.outputs_root / "rough_cut_parts",
            config.outputs_root / "rough_cut.wav",
        )
        print(output_path)
        return 0
```

- [ ] **Step 4: Run final EDL tests**

Run:

```powershell
python -m pytest tests/test_edit_decision.py -q
```

Expected: tests pass.

---

### Task 10: Postproduction Handoff And Publishing Assets

**Files:**
- Create: `C:\work\Vibe2\podcast_pipeline\postproduction.py`
- Create: `C:\work\Vibe2\podcast_pipeline\publish_assets.py`
- Modify: `C:\work\Vibe2\podcast_pipeline\cli.py`
- Test: `C:\work\Vibe2\tests\test_publish_assets.py`

- [ ] **Step 1: Implement `postproduction.py`**

```python
from __future__ import annotations

from pathlib import Path


def write_postproduction_handoff(rough_cut_path: Path, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    handoff_path = output_dir / "postproduction_handoff.md"
    handoff_path.write_text(
        f"""# Postproduction Handoff

## Input

Use this rough cut:

`{rough_cut_path}`

## Cleanvoice

Use light cleanup:

- mouth sounds: on
- heavy breaths: on
- obvious stutters: on
- long silences: conservative
- aggressive filler-word removal: off by default for Chinese speech

Export a cleaned WAV file to:

`outputs/postproduction/cleanvoice_cleaned.wav`

## Auphonic

Upload the Cleanvoice output. Use:

- loudness normalization
- speaker leveling
- light noise reduction
- MP3 export

Save the final file to:

`outputs/final_episode.mp3`

## Adobe Podcast

Use only as fallback for heavy echo or noise. Compare a short sample before processing the whole episode.
""",
        encoding="utf-8",
    )
    return handoff_path
```

- [ ] **Step 2: Write tests for shownotes asset generation**

```python
import json

from podcast_pipeline.publish_assets import create_publishing_assets


class AssetsLLM:
    def generate_json(self, system_prompt, user_prompt):
        return {
            "title_candidates": ["标题一"],
            "summary": "节目摘要",
            "chapters": [{"time": "00:00:00", "title": "开场"}],
            "shownotes_markdown": "# Show Notes\n节目摘要",
        }


def test_create_publishing_assets(tmp_path):
    transcript = tmp_path / "transcript.json"
    edl = tmp_path / "edl.json"
    output_dir = tmp_path / "outputs"
    transcript.write_text(json.dumps({"segments": []}), encoding="utf-8")
    edl.write_text(json.dumps({"segments": []}), encoding="utf-8")
    create_publishing_assets(AssetsLLM(), transcript, edl, output_dir)
    assert (output_dir / "shownotes.md").exists()
    assert (output_dir / "publishing_assets.json").exists()
```

- [ ] **Step 3: Implement `publish_assets.py`**

```python
from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from podcast_pipeline.llm import load_prompt


class JsonLLM(Protocol):
    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        ...


def create_publishing_assets(
    llm: JsonLLM,
    transcript_path: Path,
    final_edl_path: Path,
    output_dir: Path,
) -> Path:
    user_prompt = (
        "Final transcript or transcript source:\n"
        f"{transcript_path.read_text(encoding='utf-8')}\n\n"
        "Final EDL:\n"
        f"{final_edl_path.read_text(encoding='utf-8')}\n"
    )
    result = llm.generate_json(load_prompt("shownotes.md"), user_prompt)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "shownotes.md").write_text(result["shownotes_markdown"], encoding="utf-8")
    (output_dir / "publishing_assets.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_dir / "shownotes.md"
```

- [ ] **Step 4: Add CLI commands**

Add parsers:

```python
    post_parser = subparsers.add_parser("postproduction-handoff", help="Write Cleanvoice/Auphonic handoff.")
    post_parser.add_argument("--config", default="config.example.yaml")

    assets_parser = subparsers.add_parser("publishing-assets", help="Create transcript-derived publishing assets.")
    assets_parser.add_argument("--config", default="config.example.yaml")
```

Add handlers:

```python
    if args.command == "postproduction-handoff":
        from podcast_pipeline.config import load_config
        from podcast_pipeline.postproduction import write_postproduction_handoff

        config = load_config(args.config)
        output_path = write_postproduction_handoff(
            config.outputs_root / "rough_cut.wav",
            config.outputs_root / "postproduction",
        )
        print(output_path)
        return 0

    if args.command == "publishing-assets":
        from podcast_pipeline.config import load_config
        from podcast_pipeline.llm import LLMClient
        from podcast_pipeline.publish_assets import create_publishing_assets

        config = load_config(args.config)
        output_path = create_publishing_assets(
            LLMClient(config.text_model, config.openai_api_key_env),
            config.outputs_root / "transcript" / "transcript.json",
            config.outputs_root / "edit_decision_list.json",
            config.outputs_root,
        )
        print(output_path)
        return 0
```

- [ ] **Step 5: Run tests**

Run:

```powershell
python -m pytest tests/test_publish_assets.py -q
```

Expected: tests pass.

---

### Task 11: End-To-End Orchestration Commands

**Files:**
- Modify: `C:\work\Vibe2\podcast_pipeline\cli.py`
- Modify: `C:\work\Vibe2\README.md`
- Test: `C:\work\Vibe2\tests\test_cli.py`

- [ ] **Step 1: Add `next-steps` command to make the workflow explicit**

Add parser:

```python
    next_parser = subparsers.add_parser("next-steps", help="Print the recommended command order.")
    next_parser.add_argument("--config", default="config.example.yaml")
```

Add handler:

```python
    if args.command == "next-steps":
        print(
            "\n".join(
                [
                    "1. podcast-pipeline doctor",
                    "2. podcast-pipeline transcribe --config config.example.yaml",
                    "3. podcast-pipeline content-map --config config.example.yaml",
                    "4. podcast-pipeline demo-edl --config config.example.yaml --version v1",
                    "5. podcast-pipeline assemble-demo --config config.example.yaml --version v1",
                    "6. Listen to outputs/demos/demo_v1.wav and provide feedback.",
                    "7. podcast-pipeline demo-feedback --config config.example.yaml --version v1 --feedback \"...\"",
                    "8. Repeat demo-edl/assemble-demo with v2, v3 until approved.",
                    "9. podcast-pipeline freeze-style --config config.example.yaml --approved-version vN",
                    "10. podcast-pipeline final-edl --config config.example.yaml",
                    "11. podcast-pipeline assemble-final --config config.example.yaml",
                    "12. podcast-pipeline postproduction-handoff --config config.example.yaml",
                    "13. podcast-pipeline publishing-assets --config config.example.yaml",
                ]
            )
        )
        return 0
```

- [ ] **Step 2: Test `next-steps` command**

Add to `tests/test_cli.py`:

```python
def test_next_steps(capsys):
    exit_code = main(["next-steps"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "assemble-demo" in captured.out
    assert "freeze-style" in captured.out
```

- [ ] **Step 3: Write `README.md`**

````markdown
# Podcast Production Pipeline

AI-assisted workflow for turning a long Chinese interview recording and an outline into calibrated demo cuts, a 50-55 minute rough cut, postproduction handoff files, and publishing assets.

## Setup

Install Python dependencies:

```powershell
python -m pip install -e ".[dev]"
```

Install `ffmpeg` and make sure both `ffmpeg` and `ffprobe` are available on `PATH`.

Set API environment variables:

```powershell
$env:OPENAI_API_KEY="..."
$env:OPENAI_TEXT_MODEL="..."
```

## Inputs

Place the raw audio at:

```text
inputs/audio/raw_episode.wav
```

Write the interview outline at:

```text
inputs/outline.md
```

Copy and edit the config:

```powershell
Copy-Item config.example.yaml config.yaml
```

## Workflow

Print the command order:

```powershell
podcast-pipeline next-steps --config config.yaml
```

Run the main stages:

```powershell
podcast-pipeline doctor
podcast-pipeline transcribe --config config.yaml
podcast-pipeline content-map --config config.yaml
podcast-pipeline demo-edl --config config.yaml --version v1
podcast-pipeline assemble-demo --config config.yaml --version v1
```

Listen to `outputs/demos/demo_v1.wav`, provide feedback, and repeat demo versions until approved.

After approval:

```powershell
podcast-pipeline freeze-style --config config.yaml --approved-version vN
podcast-pipeline final-edl --config config.yaml
podcast-pipeline assemble-final --config config.yaml
podcast-pipeline postproduction-handoff --config config.yaml
podcast-pipeline publishing-assets --config config.yaml
```

## Postproduction

Version one uses manual Cleanvoice and Auphonic handoff. The pipeline writes exact instructions to:

```text
outputs/postproduction/postproduction_handoff.md
```
````

- [ ] **Step 4: Run CLI tests**

Run:

```powershell
python -m pytest tests/test_cli.py -q
```

Expected: all CLI tests pass.

---

### Task 12: Verification And First Real Episode Runbook

**Files:**
- Create: `C:\work\Vibe2\docs\runbooks\first-episode-runbook.md`
- Create Chinese copy: `C:\work\Vibe2\用于阅读\第一期播客运行手册.md`

- [ ] **Step 1: Create English runbook directory**

Run:

```powershell
New-Item -ItemType Directory -Force -Path .\docs\runbooks | Out-Null
```

- [ ] **Step 2: Write `docs/runbooks/first-episode-runbook.md`**

```markdown
# First Episode Runbook

## Before Running

- Put the raw audio in `inputs/audio/`.
- Put the interview outline in `inputs/outline.md`.
- Copy `config.example.yaml` to `config.yaml` and update the audio path.
- Set `OPENAI_API_KEY`.
- Set `OPENAI_TEXT_MODEL`.
- Install ffmpeg and confirm `podcast-pipeline doctor` passes.

## Demo Calibration

Run transcription, content map, demo EDL, and demo assembly.

Listen only to the demo file. Give feedback in plain Chinese. The feedback should describe pacing, content density, host/guest balance, story level, and naturalness.

Repeat demo versions until the demo feels right.

## Freeze Style

Run `freeze-style` only after the user explicitly approves a demo.

The frozen style files are the source of truth for the full edit.

## Full Episode

Run final EDL and rough cut assembly. Confirm duration is 50-55 minutes.

## Postproduction

Use the generated handoff file for Cleanvoice and Auphonic. Keep Cleanvoice conservative for Chinese filler words.

## Completion Checklist

- `outputs/demos/demo_vN.wav` exists for the approved demo.
- `outputs/style/edit_style_guide.md` exists.
- `outputs/edit_decision_list.json` exists.
- `outputs/rough_cut.wav` exists.
- `outputs/postproduction/postproduction_handoff.md` exists.
- `outputs/final_episode.mp3` exists after manual postproduction.
- `outputs/shownotes.md` exists.
```

- [ ] **Step 3: Write Chinese reading copy**

Create `C:\work\Vibe2\用于阅读\第一期播客运行手册.md` with this content:

```markdown
# 第一期播客运行手册

## 运行前

- 把原始音频放到 `inputs/audio/`。
- 把采访大纲放到 `inputs/outline.md`。
- 把 `config.example.yaml` 复制为 `config.yaml`，并更新音频路径。
- 设置 `OPENAI_API_KEY`。
- 设置 `OPENAI_TEXT_MODEL`。
- 安装 ffmpeg，并确认 `podcast-pipeline doctor` 通过。

## Demo 校准

先运行转录、内容地图、demo 剪辑清单和 demo 组装。

你只需要听 demo 文件。反馈可以直接用中文描述：节奏、信息密度、主持人/嘉宾比例、故事性和自然程度。

重复生成 demo 版本，直到你觉得风格合适。

## 冻结风格

只有在你明确确认某一版 demo 可以之后，才运行 `freeze-style`。

冻结后的风格文件就是完整正片剪辑的依据。

## 完整正片

运行最终剪辑清单和粗剪组装。确认时长在 50-55 分钟内。

## 后期处理

根据系统生成的 handoff 文件使用 Cleanvoice 和 Auphonic。中文口头禅处理要保守。

## 完成检查

- 已确认的 `outputs/demos/demo_vN.wav` 存在。
- `outputs/style/edit_style_guide.md` 存在。
- `outputs/edit_decision_list.json` 存在。
- `outputs/rough_cut.wav` 存在。
- `outputs/postproduction/postproduction_handoff.md` 存在。
- 手动后期完成后，`outputs/final_episode.mp3` 存在。
- `outputs/shownotes.md` 存在。
```

- [ ] **Step 4: Run all unit tests**

Run:

```powershell
python -m pytest -q
```

Expected: all tests pass.

- [ ] **Step 5: Run doctor**

Run:

```powershell
python -m podcast_pipeline doctor
```

Expected: prints workspace and reports whether `ffmpeg`/`ffprobe` are available. If either is missing, install ffmpeg before assembling audio.

---

## Execution Handoff

After this plan is approved, implement it in order. The safest approach is inline execution in this session because the current workspace is small and not a git repository. If the user explicitly asks for parallel agent work, split work by disjoint modules:

- Agent A: config, schemas, CLI skeleton.
- Agent B: audio, assemble, ffmpeg tests.
- Agent C: LLM-driven content map, demo, style, final EDL.
- Agent D: publishing assets, postproduction handoff, runbooks.

Do not spawn subagents unless the user explicitly asks for them.
