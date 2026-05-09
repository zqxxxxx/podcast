from podcast_pipeline.audio import ChunkPlan, build_chunk_plan, format_timestamp, parse_timestamp


def test_format_and_parse_timestamp():
    assert format_timestamp(3723.456) == "01:02:03.456"
    assert parse_timestamp("01:02:03.456") == 3723.456


def test_build_chunk_plan_uses_overlap():
    chunks = build_chunk_plan(total_seconds=3700, chunk_seconds=1800, overlap_seconds=5)
    assert chunks == [
        ChunkPlan(chunk_id="chunk_000", start=0, end=1800),
        ChunkPlan(chunk_id="chunk_001", start=1795, end=3595),
        ChunkPlan(chunk_id="chunk_002", start=3590, end=3700),
    ]
