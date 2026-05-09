# Chinese Podcast AI Production Pipeline Design

## Goal

Build a repeatable AI-assisted workflow that turns one recorded 3-hour Chinese podcast interview plus an interview outline into a 50-55 minute publishable audio episode, with a short demo calibration loop before the full edit.

The user should not manually edit a timeline. The system should produce content decisions, demo cuts, the final rough cut, post-production handoff files, and publishing assets.

## Inputs

- A single long-form raw audio file, usually around 3 hours.
- An interview outline in Markdown or plain text.
- Optional episode metadata: episode title, guest name, host name, target audience, platform notes, and desired tone.

## Outputs

- `outputs/demos/demo_vN.wav`: short demo versions for feedback.
- `outputs/demos/demo_vN_edit_decision_list.json`: timecoded decisions for each demo.
- `outputs/style/edit_style_guide.md`: frozen editorial style after demo approval.
- `outputs/style/selection_rules.json`: machine-readable content selection preferences.
- `outputs/style/cutting_rules.json`: machine-readable pacing and transition preferences.
- `outputs/edit_decision_list.json`: final 50-55 minute episode EDL.
- `outputs/rough_cut.wav`: full AI-edited rough cut before external audio cleanup.
- `outputs/final_episode.mp3`: final publishable audio after cleanup/mastering.
- `outputs/final_transcript.md`: transcript for the final episode.
- `outputs/shownotes.md`: title candidates, episode summary, chapters, and publishing notes.

## Core Workflow

### 1. Ingest

Create a project folder and validate that the raw audio file and outline exist. Store stable paths and episode settings in a project config file.

The config should include:

- target final duration: 50-55 minutes
- demo target duration: 6-10 minutes
- language: Chinese
- editing mode: conservative semantic cuts
- cleanup mode: post-rough-cut only
- export format: WAV for rough cuts, MP3 for final episode

### 2. Transcription

Split the long audio into API-safe chunks, transcribe each chunk in Chinese, then merge transcript segments back onto the original timeline.

The transcript format should preserve:

- absolute start and end time
- text
- optional speaker label if available
- source chunk id
- confidence or quality notes when available

Timecodes must always refer to the original raw audio until the rough cut has been assembled.

### 3. Content Map

Use the interview outline and transcript to build a content map of the full 3-hour recording.

Each content block should include:

- original time range
- topic label
- relation to the interview outline
- summary
- highlight score
- deletion score
- notes about story, emotion, insight, tension, repetition, or off-topic material

This step does not cut audio. It creates the decision surface for AI editing.

### 4. Demo Candidate Selection

Before editing the full episode, select a mixed demo candidate set from across the whole recording.

The demo should not simply use the beginning of the episode. It should include a representative blend:

- one story segment
- one opinion or insight segment
- one host follow-up or challenge
- one natural transition or conversational moment
- one segment that tests pacing and silence handling

The first candidate pool can be 12-18 minutes. The exported demo should be 6-10 minutes.

### 5. Demo Calibration Loop

Generate `demo_v1.wav` and a matching `demo_v1_edit_decision_list.json`.

The user listens only to the demo and gives feedback such as:

- too slow or too fast
- too fragmented
- not enough story
- too much host or not enough host
- too conclusion-heavy
- too many filler words kept
- too many natural pauses removed
- transitions feel abrupt
- content feels useful but not emotionally engaging

Each feedback round creates:

- a new demo version
- a new demo EDL
- a short feedback summary
- updated draft editing rules

The loop continues until the user says the demo is acceptable.

### 6. Style Freeze

After demo approval, convert the accepted demo and feedback into durable rules.

`edit_style_guide.md` should describe:

- target episode feeling
- ideal pacing
- preferred story-to-insight ratio
- host/guest balance
- how much natural silence to preserve
- how to handle Chinese filler words such as "嗯", "啊", "就是", "然后", "那个"
- whether laughter, hesitation, and emotional pauses should remain
- what counts as off-topic
- what makes a segment worth keeping
- what makes a segment safe to remove

`selection_rules.json` should encode content preferences. `cutting_rules.json` should encode pacing, boundary, transition, and minimum segment length rules.

### 7. Full Episode Edit Decision

Generate a full 50-55 minute EDL using:

- the transcript
- the content map
- the interview outline
- the approved demo EDL
- the frozen style guide
- selection and cutting rules

The full EDL should prefer complete semantic segments and avoid excessive micro-cuts. It should leave enough room for natural conversation while removing repetition, long setup, side paths, and weak explanations.

The system should first create a slightly longer internal candidate, around 60-70 minutes, then compress it to the target 50-55 minutes.

### 8. Rough Cut Assembly

Use the final EDL to assemble `rough_cut.wav` from the original raw audio.

This step should:

- preserve the selected ranges in order
- apply short crossfades only when needed
- avoid changing speed
- avoid cleanup that changes timing before the rough cut is exported
- validate final duration
- generate a cut report

### 9. Audio Cleanup

Run cleanup only after `rough_cut.wav` exists. This prevents transcript timecodes from drifting.

Recommended cleanup sequence for Chinese podcast audio:

1. Cleanvoice light cleanup
   - mouth sounds
   - heavy breaths
   - obvious stutters
   - long silences, conservatively
   - avoid aggressive filler-word removal by default

2. Auphonic final mastering
   - loudness normalization
   - speaker leveling
   - light noise reduction
   - final MP3 export

Adobe Podcast Enhance Speech is a fallback, not the default. Use it only when the recording has heavy room echo or noise and the result still preserves natural Chinese speech.

### 10. Publishing Assets

Generate final publishing materials from the final EDL and transcript:

- final transcript
- show notes
- title candidates
- episode summary
- chapter timestamps based on final episode time, not raw audio time
- optional social clips list

## Skills

Use these Codex skills during implementation and operation:

- `skill-installer`: install curated skills such as `transcribe` if needed.
- `transcribe`: assist with audio transcription workflows after installation.
- `openai-docs`: check current OpenAI transcription and model documentation.
- `writing-plans`: convert this design into a step-by-step implementation plan.
- `verification-before-completion`: verify the pipeline with real or sample files before declaring it ready.
- `systematic-debugging`: diagnose failed transcription, EDL, ffmpeg, or export steps.
- Optional future custom skill: `podcast-editor`, created after the workflow stabilizes, so future episodes can reuse this process directly.

## Tools

### Required Local Tools

- Python: orchestration, API calls, JSON processing, Markdown generation.
- ffmpeg: audio slicing, concatenation, WAV/MP3 export, duration checks.

### External Services

- OpenAI transcription: Chinese transcript with timestamps.
- OpenAI text model: content mapping, demo selection, EDL generation, style guide generation, shownotes.
- Cleanvoice: post-rough-cut cleanup.
- Auphonic: final loudness normalization and mastering.

### Optional Services

- Adobe Podcast Enhance Speech: fallback for very noisy or echo-heavy recordings.
- CapCut/Jianying: optional manual visual review or video publishing workflow.

## Agent Roles

These are conceptual roles for implementation and future automation. They do not require spawning subagents unless the user explicitly approves parallel agent work.

- Pipeline Architect: project structure, config, command entrypoints.
- Transcription Agent: chunking, transcription, transcript merge, timestamp validation.
- Content Editor Agent: content map, outline alignment, highlight scoring.
- Demo Editor Agent: demo candidate selection, demo EDL, feedback incorporation.
- Style Guide Agent: converts approved demo feedback into durable editing rules.
- Assembly Agent: ffmpeg EDL assembly, duration validation, rough-cut export.
- Postproduction Agent: Cleanvoice/Auphonic handoff instructions or API integration.
- QA Agent: checks file existence, durations, JSON validity, missing transcript spans, and final deliverables.

## Proposed Project Structure

```text
podcast_pipeline/
  __init__.py
  cli.py
  config.py
  ingest.py
  audio.py
  transcribe.py
  content_map.py
  demo.py
  style.py
  edit_decision.py
  assemble.py
  publish_assets.py
  schemas.py
  prompts/
    content_map.md
    demo_selection.md
    demo_feedback.md
    style_freeze.md
    final_edit_decision.md
    shownotes.md
inputs/
  audio/
  outline.md
outputs/
  transcript/
  content_map/
  demos/
  style/
  postproduction/
tests/
  fixtures/
```

## Implementation Boundaries

The first implementation should make the workflow runnable from the command line. It should not build a web UI.

The first version can support manual upload/download for Cleanvoice and Auphonic, documented with exact handoff files. API automation for those services can be added later if credentials and service constraints are clear.

The pipeline should be restartable. If transcription has already completed, later commands should reuse existing transcript files unless the user asks to regenerate them.

The pipeline should produce inspectable intermediate files at every major stage.

## Quality Checks

Before full-episode export:

- transcript JSON is valid
- all segment timecodes are monotonic
- demo duration is within 6-10 minutes
- final EDL duration is within 50-55 minutes
- selected segments do not overlap incorrectly
- each selected segment has a reason
- style guide exists before final EDL generation

Before completion:

- `rough_cut.wav` exists
- `final_episode.mp3` exists or postproduction handoff is documented
- output duration is reported
- final transcript and shownotes exist
- all generated JSON files validate against schemas

## Open Questions For Implementation

- Whether the user wants fully local open-source transcription as a fallback.
- Whether Cleanvoice and Auphonic should be integrated through APIs or handled as documented manual upload/download steps in version one.
- Whether speaker diarization is required for host/guest balance or can be inferred from transcript patterns.
- Whether the final episode should include intro/outro music.

## Recommended Version One

Version one should build:

- project config
- audio duration inspection
- transcription chunk plan
- transcript schema
- content map generation
- demo EDL generation
- demo assembly
- feedback ingestion
- style guide generation
- final EDL generation
- rough cut assembly
- postproduction handoff checklist
- publishing asset generation

Version one should defer:

- Cleanvoice API automation
- Auphonic API automation
- Adobe Podcast automation
- web dashboard
- automatic intro/outro music mixing

