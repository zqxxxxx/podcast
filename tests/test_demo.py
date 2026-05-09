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
