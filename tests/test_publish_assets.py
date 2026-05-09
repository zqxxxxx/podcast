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
