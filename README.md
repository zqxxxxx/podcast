# Podcast Production Pipeline

AI-assisted workflow for turning a long Chinese interview recording and an outline into calibrated demo cuts, a 50-55 minute rough cut, postproduction handoff files, and publishing assets.

## Setup

Install Python dependencies:

```powershell
python -m pip install -e ".[dev]"
```

Install `ffmpeg` and make sure both `ffmpeg` and `ffprobe` are available on `PATH`.

Set API environment variables:

```powershell
$env:OPENAI_API_KEY="..."
$env:OPENAI_TEXT_MODEL="..."
```

## Inputs

Place the raw audio at:

```text
inputs/audio/raw_episode.wav
```

Write the interview outline at:

```text
inputs/outline.md
```

Copy and edit the config:

```powershell
Copy-Item config.example.yaml config.yaml
```

## Workflow

Print the command order:

```powershell
podcast-pipeline next-steps --config config.yaml
```

Run the main stages:

```powershell
podcast-pipeline doctor
podcast-pipeline transcribe --config config.yaml
podcast-pipeline content-map --config config.yaml
podcast-pipeline demo-edl --config config.yaml --version v1
podcast-pipeline assemble-demo --config config.yaml --version v1
```

Listen to `outputs/demos/demo_v1.wav`, provide feedback, and repeat demo versions until approved.

After approval:

```powershell
podcast-pipeline freeze-style --config config.yaml --approved-version vN
podcast-pipeline final-edl --config config.yaml
podcast-pipeline assemble-final --config config.yaml
podcast-pipeline postproduction-handoff --config config.yaml
podcast-pipeline publishing-assets --config config.yaml
```

## Postproduction

Version one uses manual Cleanvoice and Auphonic handoff. The pipeline writes exact instructions to:

```text
outputs/postproduction/postproduction_handoff.md
```
