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
        Path("config.example.yaml").read_text(encoding="utf-8").replace("text_model: gpt-5.5", "text_model: ${OPENAI_TEXT_MODEL}"),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="OPENAI_TEXT_MODEL"):
        load_config(config_file)


def test_load_config_falls_back_to_example_for_default_config_name(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_TEXT_MODEL", "unused")
    example = tmp_path / "config.example.yaml"
    example.write_text(Path("config.example.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    config = load_config(tmp_path / "config.yaml")
    assert config.text_model == "gpt-5.5"
