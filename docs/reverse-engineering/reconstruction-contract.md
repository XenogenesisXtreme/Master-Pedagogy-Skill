# Clean-room MPVE reconstruction contract

## Boundary

MPS decides whether a video intervention is appropriate and supplies learner/topic context. MPVE plans, renders, validates, and returns artifacts. MPVE never invents an intervention trigger and never declares conceptual mastery.

OpenMontage is an AGPL-3.0 observation target. No OpenMontage source, assets, prompts, brand material, or implementation text is copied into MPS. The contracts below use MPS-owned names and structures.

## Timeline contract

`Timeline` contains `fps`, `width`, `height`, typed `TimelineClip` records, and independent `TimedOverlay` records. A clip has an absolute start, positive local duration, visual kind, render props, layer, transition tokens, and transition duration. Frame conversion is `round(seconds * fps)`; hard-cut tokens are `cut` and `none`; soft transitions are bounded to half the local clip duration. Unknown visual kinds and invalid intervals are rejected before rendering.

The pedagogical `Storyboard` remains the source of truth. Timeline fields are optional render metadata and must not replace narration, equations, validation checks, or mastery checks.

## Caption contract

Caption words contain text, non-negative `start_ms`, `end_ms > start_ms`, and optional page breaks. Word start times must be monotonic. MPVE can emit SRT, WebVTT, and a JSON timing manifest with direction metadata. Captions are optional; missing caption support does not silently imply synchronized captions. Sidecar paths and cue counts are returned explicitly.

## Media QA contract

A job is completed only after a real output is validated. QA requires a non-empty file, decodable `ffprobe` output, a video stream, expected 16:9 dimensions, a positive duration within one second of the request, and four representative frame extractions. The final review records the probe, stream metadata, representative frame paths, audio presence/silence, errors, warnings, provider, requested properties, status, and recommended action.

Output-file existence alone is insufficient. Invalid bytes, missing streams, duration drift, wrong dimensions, or failed frame extraction produce a failed job and an actionable error.

## Provider and fallback contract

Provider selection remains behind the existing hybrid renderer boundary. A local deterministic provider is preferred; optional hosted providers may be used; SVG fallback is explicitly non-video. A fallback-only artifact cannot be represented as a completed MP4 job.

## Lifecycle contract

`POST /videos` validates request context and creates an idempotent job. Jobs transition through `queued`, `processing`, and `completed` or `failed`. Storyboard, render manifest, final review, QA frames, optional caption sidecars, and video are stored under the job directory. MPS resumes the written lesson and mastery check after delivery.
