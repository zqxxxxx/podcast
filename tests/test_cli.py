from podcast_pipeline.cli import main


def test_main_version(capsys):
    exit_code = main(["--version"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "0.1.0" in captured.out


def test_main_help(capsys):
    exit_code = main([])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "podcast-pipeline" in captured.out


def test_doctor_reports_workspace(capsys):
    exit_code = main(["doctor"])
    captured = capsys.readouterr()
    assert exit_code in (0, 1)
    assert "workspace:" in captured.out


def test_next_steps(capsys):
    exit_code = main(["next-steps"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "import-transcript" in captured.out
    assert "transcribe --config" not in captured.out
    assert "assemble-demo" in captured.out
    assert "freeze-style" in captured.out


def test_import_transcript_command(monkeypatch, tmp_path, capsys):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
project:
  name: test
  workspace: .
inputs:
  transcript: inputs/transcript/feishu.srt
outputs:
  root: outputs
""",
        encoding="utf-8",
    )
    transcript = tmp_path / "inputs" / "transcript" / "feishu.srt"
    transcript.parent.mkdir(parents=True)
    transcript.write_text(
        """1
00:00:00,000 --> 00:00:01,000
Riko: 开始
""",
        encoding="utf-8",
    )

    exit_code = main(["import-transcript", "--config", str(config_file)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "segments=1" in captured.out
    assert (tmp_path / "outputs" / "transcript" / "transcript.json").exists()


def test_demo_edl_version_argument_does_not_trigger_package_version(monkeypatch, tmp_path, capsys):
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
editing:
  demo_min_minutes: 0.01
  demo_max_minutes: 1
""",
        encoding="utf-8",
    )
    transcript = tmp_path / "outputs" / "transcript" / "transcript.json"
    transcript.parent.mkdir(parents=True)
    transcript.write_text('{"segments":[{"start":0,"end":2,"text":"demo"}]}', encoding="utf-8")
    content_map = tmp_path / "outputs" / "content_map" / "content_map.json"
    content_map.parent.mkdir(parents=True)
    content_map.write_text(
        '{"blocks":[{"start":0,"end":2,"topic":"demo","highlight_score":5,"deletion_score":1}]}',
        encoding="utf-8",
    )
    (tmp_path / "inputs" / "outline.md").parent.mkdir(parents=True)
    (tmp_path / "inputs" / "outline.md").write_text("# outline", encoding="utf-8")

    class FakeLLM:
        def generate_json(self, system_prompt, user_prompt):
            return {"candidate_reason": "demo", "segments": [{"start": 0, "end": 2, "reason": "demo"}]}

    monkeypatch.setattr("podcast_pipeline.llm.build_llm_client", lambda config: FakeLLM())

    exit_code = main(["demo-edl", "--config", str(config_file), "--version", "v2"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "0.1.0" not in captured.out
    assert (tmp_path / "outputs" / "demos" / "demo_v2_edit_decision_list.json").exists()
