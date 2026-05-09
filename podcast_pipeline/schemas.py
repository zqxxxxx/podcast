from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TranscriptSegment:
    start: float
    end: float
    text: str
    speaker: str | None = None
    chunk_id: str | None = None


@dataclass(frozen=True)
class ContentBlock:
    start: float
    end: float
    topic: str
    outline_relation: str
    summary: str
    highlight_score: int
    deletion_score: int
    notes: str


@dataclass(frozen=True)
class EditSegment:
    start: float
    end: float
    reason: str
    source: str = "raw"
    labels: list[str] = field(default_factory=list)


def segment_duration(segment: TranscriptSegment | ContentBlock | EditSegment) -> float:
    return round(segment.end - segment.start, 3)


def total_edit_duration(segments: list[EditSegment]) -> float:
    return round(sum(segment_duration(segment) for segment in segments), 3)


def validate_time_range(start: float, end: float, label: str) -> None:
    if start < 0:
        raise ValueError(f"{label} start must be non-negative.")
    if end <= start:
        raise ValueError(f"{label} end must be greater than start.")


def validate_edit_segments(segments: list[EditSegment]) -> None:
    previous_start = -1.0
    for index, segment in enumerate(segments):
        validate_time_range(segment.start, segment.end, f"segment {index}")
        if segment.start < previous_start:
            raise ValueError("Edit segments must be sorted by source start time.")
        if not segment.reason.strip():
            raise ValueError(f"segment {index} requires a reason.")
        previous_start = segment.start


def transcript_segment_from_dict(data: dict[str, Any]) -> TranscriptSegment:
    return TranscriptSegment(
        start=float(data["start"]),
        end=float(data["end"]),
        text=str(data["text"]),
        speaker=data.get("speaker"),
        chunk_id=data.get("chunk_id"),
    )


def edit_segment_from_dict(data: dict[str, Any]) -> EditSegment:
    labels = data.get("labels") or []
    if not isinstance(labels, list):
        raise ValueError("labels must be a list.")
    return EditSegment(
        start=float(data["start"]),
        end=float(data["end"]),
        reason=str(data["reason"]),
        source=str(data.get("source", "raw")),
        labels=[str(label) for label in labels],
    )


def edit_segment_to_dict(segment: EditSegment) -> dict[str, Any]:
    return {
        "start": segment.start,
        "end": segment.end,
        "duration": segment_duration(segment),
        "reason": segment.reason,
        "source": segment.source,
        "labels": segment.labels,
    }
