You are selecting a 6-10 minute demo cut from a longer Chinese podcast interview.

Return strict JSON:
{
  "candidate_reason": "why these segments calibrate the editing style",
  "segments": [
    {
      "start": 0.0,
      "end": 60.0,
      "reason": "why this segment belongs in the demo",
      "labels": ["story"]
    }
  ]
}

The demo must include a representative blend of story, insight, host follow-up, natural transition, and pacing/silence test material when available.
Avoid using only the beginning of the episode.
Keep source timestamps from the raw audio.
Hard duration constraint: the sum of returned segment durations must be 360-600 seconds, with an ideal target around 480 seconds.
Prefer 6-8 concise source segments. If a candidate block is long, choose the strongest subrange instead of returning the whole block.
