from types import SimpleNamespace

from podcast_pipeline.audio import ChunkPlan
from podcast_pipeline.transcribe import create_transcript, merge_chunk_segments


def test_merge_chunk_segments_adds_chunk_offsets_and_drops_overlap_duplicates():
    chunks = [
        {
            "chunk_id": "chunk_000",
            "offset": 0,
            "segments": [
                {"start": 0, "end": 4, "text": "开场"},
                {"start": 1796, "end": 1800, "text": "重叠句"},
            ],
        },
        {
            "chunk_id": "chunk_001",
            "offset": 1795,
            "segments": [
                {"start": 0, "end": 4, "text": "重叠句"},
                {"start": 10, "end": 15, "text": "新内容"},
            ],
        },
    ]
    merged = merge_chunk_segments(chunks, duplicate_window_seconds=6)
    assert [segment.text for segment in merged] == ["开场", "重叠句", "新内容"]
    assert merged[-1].start == 1805


def test_create_transcript_uses_compressed_m4a_chunks(monkeypatch, tmp_path):
    extracted_paths = []

    config = SimpleNamespace(
        audio_path=tmp_path / "radio.m4a",
        outputs_root=tmp_path / "outputs",
        openai_api_key_env="OPENAI_API_KEY",
        transcription_model="whisper-1",
        language="zh",
    )
    config.audio_path.write_bytes(b"audio")

    monkeypatch.setattr("podcast_pipeline.transcribe.get_env_value", lambda name: "test-key")
    monkeypatch.setattr("podcast_pipeline.transcribe.OpenAI", lambda api_key: object())
    monkeypatch.setattr("podcast_pipeline.transcribe.ffprobe_duration", lambda path: 1800)
    monkeypatch.setattr(
        "podcast_pipeline.transcribe.build_chunk_plan",
        lambda total_seconds, chunk_seconds: [ChunkPlan("chunk_000", 0, 1800)],
    )
    monkeypatch.setattr(
        "podcast_pipeline.transcribe.extract_transcription_chunk",
        lambda source, destination, start, end: extracted_paths.append(destination),
    )
    monkeypatch.setattr(
        "podcast_pipeline.transcribe.transcribe_audio_file",
        lambda client, audio_path, model, language: {"segments": []},
    )

    create_transcript(config)

    assert extracted_paths == [tmp_path / "outputs" / "transcript" / "chunks" / "chunk_000.m4a"]
