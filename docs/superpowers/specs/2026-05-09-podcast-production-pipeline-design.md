# Chinese Podcast AI Production Pipeline Design

## Status

This document is the current execution design. It supersedes the earlier OpenAI transcription and GPT-text plan.

The default production path is:

```text
Feishu transcript + source audio
  -> transcript import and validation
  -> MiniMax editorial analysis
  -> ffmpeg audio assembly
  -> user demo feedback
  -> final rough cut and publishing assets
```

OpenAI API is disabled by default. It may be added later as an explicit optional review provider, but it must not be required for normal execution.

## Goals

Build a repeatable AI-assisted podcast workflow for a long Chinese interview. The workflow should produce:

- calibrated demo cuts for editorial feedback;
- a frozen style guide after demo approval;
- a natural 45-60 minute rough cut for the first episode;
- postproduction handoff instructions;
- publishing assets such as shownotes.

The workflow should keep cost predictable and avoid OpenAI API quota failures by using Feishu transcript export and MiniMax for text-heavy reasoning.

## Inputs

Required:

- `inputs/audio/radio.m4a`: original source audio. All edit decisions use this raw-audio timeline.
- `inputs/transcript/feishu.srt` or `inputs/transcript/feishu.vtt`: Feishu transcript with timestamps.
- `inputs/outline.md`: interview outline and editorial brief.
- `MINIMAX_API_KEY`: environment variable for MiniMax text generation.

Optional:

- corrected speaker map, for example `Riko = Speaker 1`, `Guest = Speaker 2`;
- protected terms and names for transcript correction;
- manual keep/delete notes from the producer.

## Outputs

- `outputs/transcript/transcript.json`: normalized transcript consumed by every downstream step.
- `outputs/content_map/content_map.json`: semantic map of topics, highlights, deletion candidates, and outline relation.
- `outputs/demos/demo_vN_edit_decision_list.json`: demo EDL.
- `outputs/demos/demo_vN.wav`: assembled demo audio.
- `outputs/demos/demo_vN_feedback.json`: user feedback normalized for later style freeze.
- `outputs/style/edit_style_guide.md`: approved editing style.
- `outputs/style/selection_rules.json`: machine-readable selection rules.
- `outputs/style/cutting_rules.json`: machine-readable cutting rules.
- `outputs/edit_decision_list.json`: final episode EDL.
- `outputs/rough_cut.wav`: assembled rough cut.
- `outputs/postproduction/postproduction_handoff.md`: Cleanvoice/Auphonic handoff.
- `outputs/shownotes.md`: publishing copy.

## Architecture

### Transcript Import

The import step converts Feishu SRT/VTT/TXT into the canonical transcript schema:

```json
{
  "segments": [
    {
      "start": 0.0,
      "end": 12.5,
      "text": "normalized transcript text",
      "speaker": "Riko",
      "chunk_id": "feishu"
    }
  ]
}
```

Validation is mandatory:

- timestamps must be non-negative and sorted;
- segment end must be greater than segment start;
- empty segments are dropped;
- total transcript coverage should be close to the source audio duration;
- if speaker labels are ambiguous, stop and ask for a speaker map.

### LLM Provider

MiniMax is the default LLM provider. The provider should be selected through configuration:

```yaml
providers:
  llm:
    provider: minimax
    api_key_env: MINIMAX_API_KEY
    base_url: https://api.minimax.io/v1
    model: MiniMax-M2.7
```

The provider interface must return strict JSON for existing pipeline modules. No default command may instantiate an OpenAI client unless the config explicitly enables an OpenAI optional review step.

### Editorial Flow

1. Build a content map from the normalized transcript and outline.
2. Generate one or more demo EDL candidates.
3. Validate the chosen demo EDL.
4. Assemble the demo with ffmpeg.
5. Ingest user feedback and iterate until approved.
6. Freeze style from the approved demo and feedback.
7. Generate the final EDL using the frozen style files.
8. Validate and assemble the rough cut.
9. Generate postproduction handoff and publishing assets.

### Quality Gates

The system relies on gates rather than trusting a single model response:

- Transcript gate: Feishu import validity and source-audio duration sanity check.
- Content gate: semantic coverage of outline sections and deletion candidates.
- Demo gate: 6-10 minute target, guest focus, representative story/insight/transition mix, not only the episode beginning.
- Final EDL gate: 45-60 minute configured target, sorted timestamps, minimum segment length, natural semantic arcs.
- Human gate: no style freeze before user approval of a demo.

## OpenAI Policy

OpenAI is not part of the default path.

Allowed uses:

- manually enabled optional review;
- one-off comparison experiments;
- legacy compatibility commands while the migration is in progress.

Disallowed default behavior:

- requiring `OPENAI_API_KEY`;
- using OpenAI for transcript creation;
- using GPT text models for content map, demo EDL, final EDL, or shownotes without explicit user approval.

## Postproduction

Version one remains a manual Cleanvoice/Auphonic handoff. Automation can be added later, but it is not required for the first episode.
