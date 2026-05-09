# First Episode Runbook

## Before Running

- Put the raw audio in `inputs/audio/`.
- Put the interview outline in `inputs/outline.md`.
- Copy `config.example.yaml` to `config.yaml` and update the audio path.
- Set `OPENAI_API_KEY` once as a user environment variable if it is not already saved on this machine.
- Install ffmpeg and confirm `podcast-pipeline doctor` passes.
- The text model is fixed to `gpt-5.5` in the project config.
- The pipeline can read the persisted user environment variable directly.

## Demo Calibration

Run transcription, content map, demo EDL, and demo assembly.

Audio commands automatically check `ffmpeg` and `ffprobe` before using them.

Listen only to the demo file. Give feedback in plain Chinese. The feedback should describe pacing, content density, host/guest balance, story level, and naturalness.

Repeat demo versions until the demo feels right.

## Freeze Style

Run `freeze-style` only after the user explicitly approves a demo.

The frozen style files are the source of truth for the full edit.

## Full Episode

Run final EDL and rough cut assembly. Confirm duration is 50-55 minutes.

## Postproduction

Use the generated handoff file for Cleanvoice and Auphonic. Keep Cleanvoice conservative for Chinese filler words.

## Completion Checklist

- `outputs/demos/demo_vN.wav` exists for the approved demo.
- `outputs/style/edit_style_guide.md` exists.
- `outputs/edit_decision_list.json` exists.
- `outputs/rough_cut.wav` exists.
- `outputs/postproduction/postproduction_handoff.md` exists.
- `outputs/final_episode.mp3` exists after manual postproduction.
- `outputs/shownotes.md` exists.
