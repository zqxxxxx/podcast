from __future__ import annotations

from pathlib import Path


def write_postproduction_handoff(rough_cut_path: Path, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    handoff_path = output_dir / "postproduction_handoff.md"
    handoff_path.write_text(
        f"""# Postproduction Handoff

## Input

Use this rough cut:

`{rough_cut_path}`

## Cleanvoice

Use light cleanup:

- mouth sounds: on
- heavy breaths: on
- obvious stutters: on
- long silences: conservative
- aggressive filler-word removal: off by default for Chinese speech

Export a cleaned WAV file to:

`outputs/postproduction/cleanvoice_cleaned.wav`

## Auphonic

Upload the Cleanvoice output. Use:

- loudness normalization
- speaker leveling
- light noise reduction
- MP3 export

Save the final file to:

`outputs/final_episode.mp3`

## Adobe Podcast

Use only as fallback for heavy echo or noise. Compare a short sample before processing the whole episode.
""",
        encoding="utf-8",
    )
    return handoff_path
