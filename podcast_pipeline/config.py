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
    openai_config = data["openai"]

    return ProjectConfig(
        name=data["project"]["name"],
        workspace=workspace,
        audio_path=audio_path,
        outline_path=outline_path,
        outputs_root=outputs_root,
        openai_api_key_env=openai_config.get("api_key_env", "OPENAI_API_KEY"),
        transcription_model=openai_config.get("transcription_model", "whisper-1"),
        text_model=_expand_env(openai_config["text_model"]),
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
