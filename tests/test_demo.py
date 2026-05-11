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


def test_create_demo_edl_uses_candidate_transcript_excerpts(tmp_path):
    class CapturingLLM:
        def __init__(self):
            self.user_prompt = ""

        def generate_json(self, system_prompt, user_prompt):
            self.user_prompt = user_prompt
            return {"candidate_reason": "candidate", "segments": [{"start": 0, "end": 2, "reason": "x"}]}

    transcript = tmp_path / "transcript.json"
    content_map = tmp_path / "content_map.json"
    output = tmp_path / "demo.json"
    transcript.write_text(
        json.dumps(
            {
                "segments": [
                    {"start": 0, "end": 1, "text": "KEEP"},
                    {"start": 100, "end": 101, "text": "DROP"},
                ]
            }
        ),
        encoding="utf-8",
    )
    content_map.write_text(
        json.dumps(
            {
                "blocks": [
                    {
                        "start": 0,
                        "end": 2,
                        "topic": "candidate",
                        "outline_relation": "",
                        "summary": "",
                        "highlight_score": 5,
                        "deletion_score": 1,
                        "notes": "",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    llm = CapturingLLM()

    create_demo_edl(llm, transcript, content_map, output, min_seconds=1, max_seconds=5)

    assert "KEEP" in llm.user_prompt
    assert "DROP" not in llm.user_prompt


def test_create_demo_edl_sorts_model_segments_by_source_time(tmp_path):
    class UnsortedLLM:
        def generate_json(self, system_prompt, user_prompt):
            return {
                "candidate_reason": "candidate",
                "segments": [
                    {"start": 3, "end": 4, "reason": "later"},
                    {"start": 0, "end": 2, "reason": "earlier"},
                ],
            }

    transcript = tmp_path / "transcript.json"
    content_map = tmp_path / "content_map.json"
    output = tmp_path / "demo.json"
    transcript.write_text(json.dumps({"segments": []}), encoding="utf-8")
    content_map.write_text(json.dumps({"blocks": []}), encoding="utf-8")

    create_demo_edl(UnsortedLLM(), transcript, content_map, output, min_seconds=1, max_seconds=10)

    data = json.loads(output.read_text(encoding="utf-8"))
    assert [segment["start"] for segment in data["segments"]] == [0, 3]


def test_create_demo_edl_fits_overlong_model_segments_to_duration(tmp_path):
    class OverlongLLM:
        def generate_json(self, system_prompt, user_prompt):
            return {
                "candidate_reason": "candidate",
                "segments": [
                    {"start": 0, "end": 300, "reason": "a"},
                    {"start": 400, "end": 700, "reason": "b"},
                    {"start": 800, "end": 1100, "reason": "c"},
                ],
            }

    transcript = tmp_path / "transcript.json"
    content_map = tmp_path / "content_map.json"
    output = tmp_path / "demo.json"
    transcript.write_text(json.dumps({"segments": []}), encoding="utf-8")
    content_map.write_text(json.dumps({"blocks": []}), encoding="utf-8")

    create_demo_edl(OverlongLLM(), transcript, content_map, output, min_seconds=360, max_seconds=600)

    data = json.loads(output.read_text(encoding="utf-8"))
    assert 360 <= data["duration"] <= 600
