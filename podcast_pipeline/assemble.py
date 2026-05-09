from __future__ import annotations

import json
from pathlib import Path

from podcast_pipeline.audio import assemble_segments
from podcast_pipeline.schemas import edit_segment_from_dict, total_edit_duration, validate_edit_segments


def load_edl(edl_path: Path):
    data = json.loads(edl_path.read_text(encoding="utf-8"))
    segments = [edit_segment_from_dict(item) for item in data["segments"]]
    validate_edit_segments(segments)
    return segments


def assemble_from_edl(source_audio: Path, edl_path: Path, work_dir: Path, output_path: Path) -> Path:
    segments = load_edl(edl_path)
    assemble_segments(source_audio, segments, work_dir, output_path)
    report_path = output_path.with_suffix(".report.json")
    report_path.write_text(
        json.dumps(
            {
                "source_audio": str(source_audio),
                "edl": str(edl_path),
                "output": str(output_path),
                "duration": total_edit_duration(segments),
                "segment_count": len(segments),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return output_path
