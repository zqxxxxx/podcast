# First Episode Runbook

## Source Of Truth

The first episode workflow uses Feishu for transcription, MiniMax for text-heavy editorial decisions, and local `ffmpeg` for audio assembly. OpenAI API is disabled by default and must not be required for normal execution.

## Before Running

- Put the raw audio at `inputs/audio/radio.m4a`.
- Export Feishu transcript with timestamps to `inputs/transcript/feishu.srt` or `inputs/transcript/feishu.vtt`.
- Put the interview outline and editorial brief in `inputs/outline.md`.
- Copy `config.example.yaml` to `config.yaml` and update paths if needed.
- Set `MINIMAX_API_KEY` as a persisted user environment variable.
- Install ffmpeg and confirm `podcast-pipeline doctor` passes.
- Do not require `OPENAI_API_KEY`; OpenAI is optional review-only and disabled by default.

## Transcript Import

Import the Feishu transcript before any LLM step:

```powershell
podcast-pipeline import-transcript --config config.yaml
```

The import step must write `outputs/transcript/transcript.json` with:

- `start` and `end` in raw-audio seconds.
- `text` as normalized Chinese transcript text.
- `speaker` when Feishu provides speaker labels.
- `chunk_id` set to `feishu`.

Stop if timestamps are missing, unsorted, empty, or clearly inconsistent with `radio.m4a`.

## Demo Calibration

Run content map, demo EDL, and demo assembly:

```powershell
podcast-pipeline content-map --config config.yaml
podcast-pipeline demo-edl --config config.yaml --version v1
podcast-pipeline assemble-demo --config config.yaml --version v1
```

Listen only to the demo file. Give feedback in plain Chinese. The feedback should describe pacing, content density, host/guest balance, story level, and naturalness.

Repeat demo versions until the demo feels right. The first acceptable demo is the editorial calibration point for the full episode.

## Freeze Style

Run `freeze-style` only after the user explicitly approves a demo.

The frozen style files are the source of truth for the full edit:

- `outputs/style/edit_style_guide.md`
- `outputs/style/selection_rules.json`
- `outputs/style/cutting_rules.json`

## Full Episode

Run final EDL and rough cut assembly:

```powershell
podcast-pipeline final-edl --config config.yaml
podcast-pipeline assemble-final --config config.yaml
```

The target is a natural full episode, configured as 45-60 minutes for this first episode. Do not force a rigid minute count at the expense of semantic completeness.

## Postproduction

Use the generated handoff file for Cleanvoice and Auphonic. Keep Cleanvoice conservative for Chinese filler words.

## Completion Checklist

- `outputs/transcript/transcript.json` exists and came from Feishu import.
- `outputs/content_map/content_map.json` exists.
- `outputs/demos/demo_vN.wav` exists for the approved demo.
- `outputs/style/edit_style_guide.md` exists.
- `outputs/edit_decision_list.json` exists.
- `outputs/rough_cut.wav` exists.
- `outputs/postproduction/postproduction_handoff.md` exists.
- `outputs/final_episode.mp3` exists after manual postproduction.
- `outputs/shownotes.md` exists.
