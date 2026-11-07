# MPVE operations reference

## Setup

From the repository root:

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q script scripts tests
python scripts/mpve_server.py --host 127.0.0.1 --port 8787
```

The Remotion renderer requires Node.js, `npx`, FFmpeg, ffprobe, and installed dependencies under `remotion/`:

```bash
cd remotion
npm install
```

## Provider behavior

`render_hybrid(...)` attempts providers in this order:

1. `remotion-cinematic`: original MPS Remotion composition, 1920×1080, 30 fps.
2. `local-cinematic`: deterministic Pillow/FFmpeg fallback, 1280×720, 24 fps.
3. Optional hosted provider supplied by the caller.
4. `static-svg-fallback`: accessible scene cards, not a video.

The selected provider, errors, fallback assets, and quality gates are written to the render manifest. A fallback is never silently represented as the preferred renderer.

## HTTP contract

- `POST /videos` returns `202` for a new job and `200` for a duplicate canonical request.
- `GET /videos/{job_id}` returns `queued`, `processing`, `completed`, or `failed`, with stage, progress, and actionable errors.
- `GET /videos/{job_id}/result` returns `409` before completion and returns artifact plus metadata after success.

Jobs are stored under `build/mpve/jobs` by default. Production deployment should place storage, authentication, object storage, and durable queues behind the API boundary rather than changing MPS pedagogy code.

## QA requirements

Before marking a job completed, inspect the actual MP4 with ffprobe and validate:

- decodable H.264 video stream
- expected provider dimensions and frame rate
- duration within the requested 15–45 second range
- representative frame extraction
- caption sidecar timestamps when captions are supplied
- artifact existence and non-zero size

Run the full tests before delivery. The repository's integration tests cover duplicate requests, invalid requests, renderer failures, FHP gating, caption sidecars, manifest round trips, fallback behavior, and a real Remotion-backed hybrid render.

## Transparency limits

The Remotion path currently creates a genuine playable MP4. It may contain silent audio when no narration/TTS provider is configured. Do not claim generated speech or music unless a provider actually produced and QA-checked those streams. A static SVG, storyboard, placeholder, or mock URL is not a video artifact.

## Clean-room boundary

REA is a reverse-engineering method, not a source-code dependency. Use capability-level findings from OpenMontage to inform staged architecture, but keep MPVE code and assets independently authored. Attribute OpenMontage/Calesthio as inspiration without copying protected implementation details.
