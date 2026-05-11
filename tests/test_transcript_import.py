import json

import pytest

from podcast_pipeline.transcript_import import import_transcript_file, parse_srt_timestamp


def test_parse_srt_timestamp_accepts_milliseconds():
    assert parse_srt_timestamp("01:02:03,456") == 3723.456
    assert parse_srt_timestamp("00:00:03.500") == 3.5


def test_import_srt_writes_canonical_transcript_json(tmp_path):
    source = tmp_path / "feishu.srt"
    source.write_text(
        """1
00:00:01,000 --> 00:00:03,500
Riko: 我们开始。

2
00:00:04,000 --> 00:00:08,000
嘉宾: 好的，我来讲讲。
""",
        encoding="utf-8",
    )
    output = tmp_path / "transcript.json"

    report = import_transcript_file(source, output)

    data = json.loads(output.read_text(encoding="utf-8"))
    assert report.segment_count == 2
    assert data["segments"] == [
        {
            "start": 1.0,
            "end": 3.5,
            "text": "我们开始。",
            "speaker": "Riko",
            "chunk_id": "feishu",
        },
        {
            "start": 4.0,
            "end": 8.0,
            "text": "好的，我来讲讲。",
            "speaker": "嘉宾",
            "chunk_id": "feishu",
        },
    ]


def test_import_vtt_skips_header_and_notes(tmp_path):
    source = tmp_path / "feishu.vtt"
    source.write_text(
        """WEBVTT

NOTE exported by Feishu

00:00:00.000 --> 00:00:02.000
说话人 1: 开头

00:00:02.500 --> 00:00:04.000
说话人 2: 回应
""",
        encoding="utf-8",
    )
    output = tmp_path / "transcript.json"

    import_transcript_file(source, output)

    data = json.loads(output.read_text(encoding="utf-8"))
    assert [segment["speaker"] for segment in data["segments"]] == ["说话人 1", "说话人 2"]
    assert [segment["text"] for segment in data["segments"]] == ["开头", "回应"]


def test_import_rejects_unsorted_timestamps(tmp_path):
    source = tmp_path / "bad.srt"
    source.write_text(
        """1
00:00:05,000 --> 00:00:06,000
后面

2
00:00:04,000 --> 00:00:05,000
前面
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="sorted"):
        import_transcript_file(source, tmp_path / "transcript.json")
