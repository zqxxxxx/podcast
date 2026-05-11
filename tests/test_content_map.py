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


class ChunkRecordingLLM:
    def __init__(self):
        self.prompts = []

    def generate_json(self, system_prompt, user_prompt):
        self.prompts.append(user_prompt)
        index = len(self.prompts)
        return {
            "blocks": [
                {
                    "start": index,
                    "end": index + 1,
                    "topic": f"chunk {index}",
                    "outline_relation": "测试",
                    "summary": "测试",
                    "highlight_score": 3,
                    "deletion_score": 3,
                    "notes": "测试",
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


def test_build_content_map_chunks_large_transcript(tmp_path):
    transcript = tmp_path / "transcript.json"
    outline = tmp_path / "outline.md"
    output = tmp_path / "content_map.json"
    transcript.write_text(
        json.dumps(
            {
                "segments": [
                    {"start": 0, "end": 1, "text": "第一段"},
                    {"start": 2, "end": 3, "text": "第二段"},
                    {"start": 4, "end": 5, "text": "第三段"},
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    outline.write_text("# 大纲", encoding="utf-8")
    llm = ChunkRecordingLLM()

    build_content_map(llm, transcript, outline, output, max_chunk_seconds=2)

    data = json.loads(output.read_text(encoding="utf-8"))
    assert len(llm.prompts) == 3
    assert [block["topic"] for block in data["blocks"]] == ["chunk 1", "chunk 2", "chunk 3"]
    assert sorted(path.name for path in (tmp_path / "chunks").glob("*.json")) == [
        "chunk_001.json",
        "chunk_002.json",
        "chunk_003.json",
    ]
