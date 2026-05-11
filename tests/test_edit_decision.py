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


def test_create_final_edl_includes_configured_duration_in_prompt(tmp_path):
    class CapturingLLM:
        def __init__(self):
            self.user_prompt = ""

        def generate_json(self, system_prompt, user_prompt):
            self.user_prompt = user_prompt
            return {
                "segments": [{"start": 0, "end": 2700, "reason": "natural complete arc"}],
                "total_target_reasoning": "fits natural target",
            }

    for name in ["transcript.json", "content_map.json", "style.md", "selection.json", "cutting.json"]:
        (tmp_path / name).write_text("{}", encoding="utf-8")

    llm = CapturingLLM()
    create_final_edl(
        llm,
        tmp_path / "transcript.json",
        tmp_path / "content_map.json",
        tmp_path / "style.md",
        tmp_path / "selection.json",
        tmp_path / "cutting.json",
        tmp_path / "edit.json",
        min_seconds=2700,
        max_seconds=3600,
    )

    assert "Target duration: 45-60 minutes" in llm.user_prompt
