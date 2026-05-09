import pytest

from podcast_pipeline.schemas import (
    EditSegment,
    edit_segment_from_dict,
    total_edit_duration,
    validate_edit_segments,
)


def test_validate_edit_segments_requires_sorted_segments():
    segments = [
        EditSegment(start=10, end=20, reason="later"),
        EditSegment(start=5, end=8, reason="earlier"),
    ]
    with pytest.raises(ValueError, match="sorted"):
        validate_edit_segments(segments)


def test_total_edit_duration():
    segments = [
        EditSegment(start=0, end=10, reason="opening"),
        EditSegment(start=20, end=35.5, reason="story"),
    ]
    assert total_edit_duration(segments) == 25.5


def test_edit_segment_from_dict_defaults_source_and_labels():
    segment = edit_segment_from_dict({"start": 1, "end": 2, "reason": "keep"})
    assert segment.source == "raw"
    assert segment.labels == []
