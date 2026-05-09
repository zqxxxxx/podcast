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
