from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

DEFAULT_AUDIO_PATH = "inputs/audio/radio.m4a"
DEFAULT_TRANSCRIPT_PATH = "inputs/transcript/feishu.srt"
DEFAULT_OUTLINE_PATH = "inputs/outline.md"
DEFAULT_OUTPUTS_ROOT = "outputs"
DEFAULT_TRANSCRIPT_SOURCE = "feishu"
DEFAULT_LLM_PROVIDER = "minimax"
DEFAULT_LLM_API_KEY_ENV = "MINIMAX_API_KEY"
DEFAULT_LLM_BASE_URL = "https://api.minimaxi.com/v1"
DEFAULT_LLM_MODEL = "MiniMax-M2.7"


@dataclass(frozen=True)
class ProjectConfig:
    name: str
    workspace: Path
    audio_path: Path
    transcript_path: Path
    outline_path: Path
    outputs_root: Path
    transcript_source: str
    llm_provider: str
    llm_api_key_env: str
    llm_base_url: str
    llm_model: str
    openai_enabled: bool
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
    if not config_path.exists() and config_path.name == "config.yaml":
        fallback = config_path.with_name("config.example.yaml")
        if fallback.exists():
            config_path = fallback
    data: dict[str, Any] = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    project = data.get("project") or {}
    inputs = data.get("inputs") or {}
    outputs = data.get("outputs") or {}
    providers = data.get("providers") or {}
    transcript_provider = providers.get("transcript") or {}
    llm_provider = providers.get("llm") or {}
    provider_openai = providers.get("openai") or {}

    workspace = (config_path.parent / project.get("workspace", ".")).resolve()

    audio_path = (workspace / inputs.get("audio", DEFAULT_AUDIO_PATH)).resolve()
    transcript_path = (workspace / inputs.get("transcript", transcript_provider.get("input", DEFAULT_TRANSCRIPT_PATH))).resolve()
    outline_path = (workspace / inputs.get("outline", DEFAULT_OUTLINE_PATH)).resolve()
    outputs_root = (workspace / outputs.get("root", DEFAULT_OUTPUTS_ROOT)).resolve()

    editing = data.get("editing") or {}
    postproduction = data.get("postproduction") or {}
    openai_config = data.get("openai") or {}

    return ProjectConfig(
        name=project.get("name", "chinese-podcast-episode"),
        workspace=workspace,
        audio_path=audio_path,
        transcript_path=transcript_path,
        outline_path=outline_path,
        outputs_root=outputs_root,
        transcript_source=transcript_provider.get("source", DEFAULT_TRANSCRIPT_SOURCE),
        llm_provider=llm_provider.get("provider", DEFAULT_LLM_PROVIDER),
        llm_api_key_env=llm_provider.get("api_key_env", DEFAULT_LLM_API_KEY_ENV),
        llm_base_url=llm_provider.get("base_url", DEFAULT_LLM_BASE_URL),
        llm_model=_expand_env(llm_provider.get("model", DEFAULT_LLM_MODEL)),
        openai_enabled=bool(provider_openai.get("enabled", openai_config.get("enabled", False))),
        openai_api_key_env=openai_config.get("api_key_env", "OPENAI_API_KEY"),
        transcription_model=openai_config.get("transcription_model", "whisper-1"),
        text_model=_expand_env(openai_config.get("text_model", "gpt-5.5")),
        language=editing.get("language", "zh"),
        final_min_seconds=_minutes_to_seconds(editing.get("final_min_minutes", 45)),
        final_max_seconds=_minutes_to_seconds(editing.get("final_max_minutes", 60)),
        demo_min_seconds=_minutes_to_seconds(editing.get("demo_min_minutes", 6)),
        demo_max_seconds=_minutes_to_seconds(editing.get("demo_max_minutes", 10)),
        demo_candidate_min_seconds=_minutes_to_seconds(editing.get("demo_candidate_min_minutes", 12)),
        demo_candidate_max_seconds=_minutes_to_seconds(editing.get("demo_candidate_max_minutes", 18)),
        min_segment_seconds=int(editing.get("min_segment_seconds", 20)),
        crossfade_ms=int(editing.get("crossfade_ms", 80)),
        conservative_semantic_cuts=bool(editing.get("conservative_semantic_cuts", True)),
        cleanvoice_mode=postproduction.get("cleanvoice_mode", "manual_light_cleanup"),
        auphonic_mode=postproduction.get("auphonic_mode", "manual_mastering"),
        adobe_podcast_mode=postproduction.get("adobe_podcast_mode", "fallback_only"),
    )
