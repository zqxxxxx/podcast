from podcast_pipeline.runtime_env import get_env_value


def test_get_env_value_prefers_process_environment(monkeypatch):
    monkeypatch.setenv("PODCAST_PIPELINE_TEST_ENV", "process-value")
    monkeypatch.setattr("podcast_pipeline.runtime_env._read_windows_user_env", lambda name: "registry-value")
    assert get_env_value("PODCAST_PIPELINE_TEST_ENV") == "process-value"


def test_get_env_value_falls_back_to_persistent_environment(monkeypatch):
    monkeypatch.delenv("PODCAST_PIPELINE_TEST_ENV", raising=False)
    monkeypatch.setattr("podcast_pipeline.runtime_env._read_windows_user_env", lambda name: "registry-value")
    assert get_env_value("PODCAST_PIPELINE_TEST_ENV") == "registry-value"
