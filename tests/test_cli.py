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
    assert "assemble-demo" in captured.out
    assert "freeze-style" in captured.out
