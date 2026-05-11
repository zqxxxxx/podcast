import json

from podcast_pipeline.assemble import load_edl


def test_load_edl_allows_non_linear_sequence_for_cold_open(tmp_path):
    edl = tmp_path / "edit.json"
    edl.write_text(
        json.dumps(
            {
                "segments": [
                    {"start": 100, "end": 110, "reason": "cold open"},
                    {"start": 10, "end": 20, "reason": "intro"},
                ]
            }
        ),
        encoding="utf-8",
    )

    segments = load_edl(edl)

    assert [segment.start for segment in segments] == [100, 10]
