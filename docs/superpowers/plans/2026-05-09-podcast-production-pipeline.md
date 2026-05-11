# Podcast Episode Execution Plan

> Use this plan after the episode content is ready. One-time engineering defaults such as MiniMax provider settings, default paths, and OpenAI-disabled behavior are implemented in code and should not be reconfigured for each episode.

## Goal

Turn prepared episode materials into a calibrated demo, approved editing style, full rough cut, postproduction handoff, and publishing assets.

## Required Inputs

Place these files before running the pipeline:

- `inputs/audio/radio.m4a`
- `inputs/transcript/feishu.srt` or `inputs/transcript/feishu.vtt`
- `inputs/outline.md`

The Feishu transcript must include timestamps. SRT is preferred.

## Execution Steps

- [ ] Confirm the audio exists at `inputs/audio/radio.m4a`.

- [ ] Confirm the Feishu transcript exists at `inputs/transcript/feishu.srt` or update the config only if the file uses another supported path.

- [ ] Confirm `inputs/outline.md` contains the interview outline and editorial brief for this episode.

- [ ] Run the environment check:

```powershell
podcast-pipeline doctor
```

- [ ] Import the Feishu transcript:

```powershell
podcast-pipeline import-transcript --config config.yaml
```

Expected output:

```text
outputs/transcript/transcript.json segments=<count> first_start=<seconds> last_end=<seconds>
```

Stop if the import reports zero segments, missing timestamps, unsorted timestamps, or a duration that clearly does not match the source audio.

- [ ] Build the content map:

```powershell
podcast-pipeline content-map --config config.yaml
```

Expected output:

```text
outputs/content_map/content_map.json
```

- [ ] Generate the first demo edit decision list:

```powershell
podcast-pipeline demo-edl --config config.yaml --version v1
```

Expected output:

```text
outputs/demos/demo_v1_edit_decision_list.json
```

- [ ] Assemble the first demo:

```powershell
podcast-pipeline assemble-demo --config config.yaml --version v1
```

Expected output:

```text
outputs/demos/demo_v1.wav
```

- [ ] Listen to `outputs/demos/demo_v1.wav`.

Give feedback in Chinese about pacing, content density, host/guest balance, story level, and naturalness.

- [ ] Ingest demo feedback:

```powershell
podcast-pipeline demo-feedback --config config.yaml --version v1 --feedback "你的反馈"
```

- [ ] Repeat demo generation with `v2`, `v3`, etc. until one demo is approved.

- [ ] Freeze the approved style:

```powershell
podcast-pipeline freeze-style --config config.yaml --approved-version vN
```

Expected outputs:

```text
outputs/style/edit_style_guide.md
outputs/style/selection_rules.json
outputs/style/cutting_rules.json
```

- [ ] Generate the full episode EDL:

```powershell
podcast-pipeline final-edl --config config.yaml
```

Expected output:

```text
outputs/edit_decision_list.json
```

- [ ] Assemble the rough cut:

```powershell
podcast-pipeline assemble-final --config config.yaml
```

Expected output:

```text
outputs/rough_cut.wav
```

- [ ] Generate postproduction handoff:

```powershell
podcast-pipeline postproduction-handoff --config config.yaml
```

Expected output:

```text
outputs/postproduction/postproduction_handoff.md
```

- [ ] Generate publishing assets:

```powershell
podcast-pipeline publishing-assets --config config.yaml
```

Expected output:

```text
outputs/shownotes.md
```

## Completion Checklist

- `outputs/transcript/transcript.json` exists.
- `outputs/content_map/content_map.json` exists.
- Approved `outputs/demos/demo_vN.wav` exists.
- `outputs/style/edit_style_guide.md` exists.
- `outputs/edit_decision_list.json` exists.
- `outputs/rough_cut.wav` exists.
- `outputs/postproduction/postproduction_handoff.md` exists.
- `outputs/shownotes.md` exists.
