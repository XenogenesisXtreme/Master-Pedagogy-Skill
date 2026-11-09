---
name: mpve
description: Master Pedagogy Video Engine for adding validated instructional video interventions to the existing Master Pedagogy Skill plugin. Use when MPS has already decided that a video is appropriate, when planning or rendering a physics explainer, or when integrating/testing the MPVE API.
---

# Master Pedagogy Video Engine

Use MPVE as a video capability **inside the existing Master Pedagogy Skill (MPS)**. Do not create a separate tutoring product, replace MPS, or let MPVE make pedagogical decisions that belong to MPS.

## Responsibility boundary

MPS owns the learner conversation and state, prerequisite and misconception diagnosis, the three-consecutive-incorrect-answer trigger, learning-mode and exam-profile decisions, follow-up teaching, and mastery gates.

MPVE owns only the video intervention after MPS supplies a valid request: planning, script/storyboard creation, diagrams and animation, textbook-style equations, narration text and captions when configured, rendering, media QA, job lifecycle, and artifact delivery. After delivery, MPS must resume the written lesson and mastery check. A video never proves mastery.

## When to invoke

Invoke MPVE only when MPS has decided that motion, sequencing, or a visual intervention will materially improve understanding. Pass the diagnosed knowledge gap and the pending mastery objective. Do not independently trigger a video merely because a learner has made a mistake.

For a learner-facing `video` command, use Cinematic by default. Allow explicit `video whiteboard`, `video short`, or `video fhp` overrides. Infer a presentation profile from the topic when no profile is supplied for an isolated video request; do not overwrite the learner's persistent curriculum profile with that inference.

## Request contract

Send structured JSON with at least `topic` and `objective`. Include these fields when known:

- `subtopic`, `learner_level`, `prerequisites`, and `misconception`
- `mastery_check`, `narration`, `equations`, and `visual_assets`
- `mode`, `style`, `duration`, and `aspect_ratio`
- `exam_profile`, `source_refs`, and `narration_language`
- `learner_interest` and `analogy_consent`
- `derived` for FHP requests

Defaults and gates:

- `style`: `cinematic`
- `aspect_ratio`: `16:9`
- `duration`: 15 seconds by default; any positive whole number is accepted up to `MPVE_MAX_DURATION_SECONDS` (600 seconds by default)
- Use learner interests only after MPS has asked permission. Set `analogy_consent: true` only with that permission and a learner-provided interest.
- FHP/Floathead Physics requires a completed written derivation and `derived: true`; never use MPVE to replace the first-principles discovery protocol.
- Preserve the supplied misconception and objective in the storyboard. Do not invent unsupported physics claims.

## Required production workflow

1. Receive a valid request from MPS; do not reinterpret the trigger or mastery decision.
2. Validate required fields, profile/style, 16:9 aspect ratio, positive duration under the configured safety ceiling, analogy consent, and FHP derivation state.
3. Create and persist the provider-neutral storyboard before rendering.
4. Render through the provider boundary. The current local order is Remotion Cinematic → deterministic local Cinematic fallback → optional hosted adapter → checked SVG scene-card fallback.
5. Preserve complete equation derivations. Render equations as textbook math: Greek glyphs, semantic subscripts/superscripts, fractions, and aligned lines—not raw LaTeX or underscore syntax.
6. Generate caption sidecars when caption timings are provided. Captions should remain simplified and readable.
7. Run post-render QA: decode with ffprobe, verify a real video stream, dimensions, duration, representative frames, and artifact integrity. For Remotion, expect 1920×1080 at 30 fps; for the deterministic fallback, expect 1280×720 at 24 fps.
8. Return the artifact and metadata only when the job is completed and the artifact exists. Identify fallback assets and limitations explicitly.
9. MPS resumes the written explanation and performs the pending mastery check.

## API lifecycle

Start the local adapter with:

```bash
python scripts/mpve_server.py --host 127.0.0.1 --port 8787
```

Use:

- `POST /videos` — submit a request and receive a job ID
- `GET /videos/{job_id}` — retrieve state, stage, progress, and errors
- `GET /videos/{job_id}/result` — retrieve the completed artifact and metadata

States are `queued`, `processing`, `completed`, and `failed`. Identical canonical requests are deduplicated. A result requested before completion is not success. A storyboard, placeholder, simulated render, or static SVG must never be described as a generated MP4.

See `references/chatgpt-integration.md` for the adapter contract and polling pseudocode. See `references/operations.md` for setup, provider behavior, QA, limitations, and verification commands.

## Clean-room and transparency rules

REA and OpenMontage findings may inform capability-level architecture and observable workflow patterns, but MPVE must use independently written code, assets, and interfaces. Do not copy OpenMontage source, protected assets, secrets, or implementation details. Credit OpenMontage/Calesthio as architectural inspiration when describing the project.

Be explicit about current limits: the local Remotion renderer produces a genuine MP4 and may contain silent audio when narration/TTS is not configured; narration text and caption timing are supported, but do not claim synthesized narration unless the selected provider actually produced it. Keep hosted providers behind the provider boundary.

## Repository integration points

- `scripts/mpve_engine.py` — job lifecycle and library API
- `scripts/mpve_server.py` — HTTP adapter
- `scripts/video_explainer.py` — storyboard contract and validation
- `scripts/hybrid_video.py` — provider dispatch
- `scripts/remotion_video.py` and `remotion/` — Remotion renderer
- `scripts/mpve_qa.py` — media QA
- `docs/mpve-api.md` — HTTP examples
- `docs/mpve-integration.md` — MPS/ChatGPT handoff
