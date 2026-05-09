from podcast_pipeline.transcribe import merge_chunk_segments


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
