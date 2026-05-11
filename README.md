# Podcast Production Pipeline

AI-assisted workflow for turning a long Chinese interview recording, a Feishu transcript, and an interview outline into calibrated demo cuts, a natural full rough cut, postproduction handoff files, and publishing assets.

## Current Production Contract

The main pipeline must not depend on OpenAI API quota.

- Transcript source: Feishu export, preferably `inputs/transcript/feishu.srt`.
- Source audio: `inputs/audio/radio.m4a`.
- Editorial LLM: MiniMax via `MINIMAX_API_KEY`.
- Audio assembly: local `ffmpeg` / `ffprobe`.
- OpenAI: disabled by default and allowed only as an explicit optional review fallback.

This repository still contains earlier OpenAI transcription code for compatibility. Default episode execution follows this README, the first episode runbook, and the updated execution plan.

## Setup

Install Python dependencies:

```powershell
python -m pip install -e ".[dev]"
```

Install `ffmpeg` and make sure both `ffmpeg` and `ffprobe` are available on `PATH`.

Set the MiniMax API key once as a user environment variable:

```powershell
[Environment]::SetEnvironmentVariable("MINIMAX_API_KEY", "...", "User")
$env:MINIMAX_API_KEY="..."
```

Do not set or require `OPENAI_API_KEY` for the default workflow.

## Inputs

Place the raw audio at:

```text
inputs/audio/radio.m4a
```

Export Feishu transcript with timestamps and place it at one of:

```text
inputs/transcript/feishu.srt
inputs/transcript/feishu.vtt
inputs/transcript/feishu.txt
```

SRT or VTT is preferred because the edit decision list must cut the original audio by source timestamps.

Write the interview outline and editorial brief at:

```text
inputs/outline.md
```

Copy and edit the config:

```powershell
Copy-Item config.example.yaml config.yaml
```

## Default Workflow

The default command order:

```powershell
podcast-pipeline doctor
podcast-pipeline import-transcript --config config.yaml
podcast-pipeline content-map --config config.yaml
podcast-pipeline demo-edl --config config.yaml --version v1
podcast-pipeline assemble-demo --config config.yaml --version v1
```

Listen to `outputs/demos/demo_v1.wav`, provide Chinese feedback about pacing, content density, host/guest balance, story level, and naturalness, then repeat demo versions until approved.

After approval:

```powershell
podcast-pipeline demo-feedback --config config.yaml --version v1 --feedback "..."
podcast-pipeline freeze-style --config config.yaml --approved-version vN
podcast-pipeline final-edl --config config.yaml
podcast-pipeline assemble-final --config config.yaml
podcast-pipeline postproduction-handoff --config config.yaml
podcast-pipeline publishing-assets --config config.yaml
```

## Quality Gates

The MiniMax workflow must include these gates before audio assembly:

- Feishu import validation: timestamps are sorted, non-empty, and close to the source audio duration.
- Content map: transcript is chunked into semantic blocks before final selection.
- Demo EDL validation: total duration, source timestamp order, minimum segment duration, topic coverage, and guest focus.
- Demo feedback loop: no full episode style freeze before the user approves a demo.
- Final EDL validation: natural semantic arcs are preferred over rigid minute-count optimization.

## Postproduction

Version one uses manual Cleanvoice and Auphonic handoff. The pipeline writes exact instructions to:

```text
outputs/postproduction/postproduction_handoff.md
```
