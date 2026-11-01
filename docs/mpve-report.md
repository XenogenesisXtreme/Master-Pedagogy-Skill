# MPVE reverse-engineering and implementation report

## Scope

This implementation follows `MPVE_Manus_Handoff_and_Super_Prompt_v2.pdf`. The target state is one Master Pedagogy plugin with an attached video engine. MPS retains learner conversation, state, diagnosis, intervention triggers, and mastery gates. MPVE owns planning, rendering, QA, lifecycle, API, and artifact delivery.

No OpenMontage source code or assets were copied. OpenMontage was inspected as a public AGPL-3.0 repository for capabilities and architectural patterns only; the implementation in this repository is independently written and uses the existing MPS renderer contracts.

## REA evidence

REA static analysis was run against OpenMontage's `remotion-composer` directory.

- OpenMontage revision: `195eab24478dc9363326aec437aefc3701635ddf`.
- REA evidence ID: `ev_8fb813202915dbc83805b6682ac4232dfba9a94c4e7c26aea394330b7c78b766`.
- Analyzed artifact SHA-256: `56a2b742d1f13da7ce78dced6f91c22de2795f62cb9bd22a22dd0bbf1d9b0cc7`.
- REA analyzed 42 relevant files, parsed 35 JavaScript/TypeScript files, visited 32,739 AST nodes, and retained 457 findings with no parse failures.
- REA limitations were preserved: static parsing did not execute bootstrap code, prove runtime execution, resolve every dynamic path, or invoke Webpack/Rspack handlers.

The useful patterns translated into MPVE contracts are staged planning before rendering, explicit provider boundaries, durable render metadata, quality gates, and honest fallback reporting. The target's AGPL license is the reason this repository contains no imported OpenMontage implementation.

## Clean-room MPVE design

The engine is intentionally smaller and tailored to MPS:

1. `scripts/mpve_engine.py` validates structured learning context, creates a storyboard through the existing `video_explainer` contract, persists job state, deduplicates canonical requests, calls the existing hybrid renderer, and returns artifact metadata.
2. `scripts/mpve_server.py` exposes `POST /videos`, `GET /videos/{job_id}`, and `GET /videos/{job_id}/result` through a dependency-light local HTTP adapter.
3. `skills/mpve/SKILL.md` packages the MPS/MPVE boundary and operating workflow for agent use.
4. `docs/mpve-api.md` documents setup and request/response examples.
5. `docs/mpve-integration.md` provides ChatGPT adapter pseudocode and error/fallback rules.

The provider order remains the existing MPS order: local deterministic Cinematic MP4 renderer, optional hosted adapter hook, then checked SVG fallback. Fallback output is explicitly labeled and is never represented as a genuine MP4.

## Acceptance verification

### Automated tests

- Dedicated MPVE tests: 5/5 passed.
- Skill validation: `reverse-engineer-anything` and `mpve` both passed the official skill validator.
- Python compilation and `git diff --check` passed after the MPVE changes.
- The first full-suite run found and fixed a test mock signature mismatch; the implementation failure path was not hidden.

### Real API vertical slice

A real request was submitted through the running API for Floatation, with a NEET learner level, the misconception “A heavier object must always sink,” objective “Explain why an object floats when buoyant force balances its weight,” 15-second duration, Cinematic style, and 16:9 aspect ratio.

Observed lifecycle:

`processing / planning` → `processing / rendering` → `completed / completed`.

The completed result used provider `local-cinematic` and produced a genuine MP4 at `build/mpve-demo/jobs/mps-6e32d626700b/video.mp4`. `ffprobe` verified:

- H.264 video stream
- 1280×720 dimensions
- 24 fps
- 15.000 seconds
- 16:9 landscape

The job also produced a storyboard JSON and render manifest. The local renderer is silent when narration/TTS is not configured; this is reported by `audio: false` rather than hidden.

## Known limitations

- The current server is a local development adapter: no authentication, multi-process queue, remote object storage, or production retention policy.
- Job state is persisted as JSON under the configured output root, but the in-memory index is not reconstructed across server restarts.
- The local renderer's current generic scene model is deterministic and physics-oriented; it is not a general text-to-video model.
- Narration/TTS and synchronized captions remain host/provider extensions. A silent MP4 is valid and explicitly reported.
- The existing hybrid renderer's hosted adapter hook is callable integration surface, not a configured hosted provider.
- A complete production deployment should add authenticated storage, durable queue recovery, media URL serving, and a configured narration/caption provider behind the same MPVE contract.

## Next integration step

Connect the existing MPS plugin's video command or intervention trigger to `POST /videos` using the adapter described in `docs/mpve-integration.md`. After MPVE completes, deliver the artifact and return control to MPS for the written explanation and mastery check. Do not let MPVE independently trigger video generation or declare mastery.
