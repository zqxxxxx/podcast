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
    transcript.write_text(
        json.dumps({"segments": [{"start": 0, "end": 90, "text": "测试"}]}, ensure_ascii=False),
        encoding="utf-8",
    )
    outline.write_text("# 大纲", encoding="utf-8")

    build_content_map(FakeLLM(), transcript, outline, output)

    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["blocks"][0]["topic"] == "开场故事"
