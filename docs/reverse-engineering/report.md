# OpenMontage → MPVE reverse-engineering report

## Executive summary

The full eight-area REA pass shows OpenMontage as a staged, provider-neutral video production system: a pedagogical or creative brief becomes a timed scene IR; selectors choose capable tools; composition layers media, titles, overlays, captions, and audio; post-render QA produces evidence; and delivery packaging is separate from rendering.

MPS already has a sound tutoring boundary and a working local-first video vertical slice. The highest-value compatible improvements are not copying Remotion or OpenMontage, but strengthening MPS's own interfaces: typed timeline metadata, deterministic frame/transition policy, caption sidecars, real post-render media QA, final-review evidence, and a clearer distinction between requested and observed media properties.

## Target identity and license

See [`target-identity.json`](target-identity.json) and [`openmontage-inventory.json`](openmontage-inventory.json). The target revision is fixed to `195eab24478dc9363326aec437aefc3701635ddf`; target license is AGPL-3.0. REA evidence is preserved under [`evidence/`](evidence/).

## Subsystem findings

| Area | Target behavior | MPS gap | `mvpe` response |
|---|---|---|---|
| Cinematic renderer | Typed video/title scenes, 1920×1080/30 fps, local fades, source trims, deterministic motion | Single 1280×720/24 fps physics renderer | Added render-neutral timeline contract and local transition rules |
| Scene/props | Timed cuts, overlays, typed component props, background layers | Compact pedagogical Scene only | Added optional typed timeline IR without replacing Storyboard |
| Captions | Word timestamps, page grouping, active-word timing, RTL/CJK controls, SRT/VTT paths | No caption schema or artifacts | Added validated timed words and SRT/VTT/JSON sidecars |
| Transitions | Local-duration fades, hard cuts, layered sequences | Scene switching by global progress | Added deterministic transition-window contract and tests |
| Audio | Separate tracks, TTS selection, ducking, loudness, word timing | Text-only narration and `audio: bool` | Documented as next adapter boundary; final review now reports audio state |
| Routing | Capability discovery, explicit route filters, provenance, no silent prohibited fallback | Fixed provider chain and opaque hosted callback | Preserved current chain and made fallback/QA evidence explicit |
| QA | Schema-backed reports, ffprobe, frame samples, audio/subtitle/promise checks | Completion based on path existence | Added real ffprobe/frame QA and final-review artifact |
| Runtime/delivery | Locked runtime, checkpoints, export bundle, publish log | Local job JSON, no final review or export package | Added durable final review and documented remaining production limits |

## Prioritized backlog

### P0 implemented on `mvpe`

- Reject invalid render outputs instead of trusting path existence.
- Persist technical probe data and four representative frame artifacts.
- Write a versioned final-review JSON artifact with pass/fail and recommended action.
- Add a clean-room timed-caption contract and SRT/VTT/JSON sidecars.
- Add typed timeline and local transition contracts with boundary tests.

### P1 documented for the next iteration

- Add an explicit capability selector with provider/tool/runtime metadata and route constraints.
- Add an audio stage with provider-neutral TTS, word timing, mix/ducking, loudness, and transcript checks.
- Add restart-safe JobStore reconstruction and artifact retention/cleanup.
- Add authenticated artifact delivery and export packaging with subtitles/thumbnail/metadata.
- Add visual regression/golden-frame checks for the local renderer.

### P2 optional extensions

- Remotion-compatible sidecar adapter kept outside MPS licensing scope.
- Rich typed visual components such as metric cards, comparison cards, progress bars, and media-backed title plates.
- Human approval checkpoints for high-impact or externally published content.

## Verification matrix

- Existing full suite: 20 tests passed before the branch extension.
- New timeline contract tests cover frame rounding, hard cuts, bounded fades, and invalid timing.
- New caption tests cover timestamp carry, monotonicity, sidecar validity, and JSON metadata.
- New MPVE tests cover invalid media rejection, caption artifact creation, and the existing lifecycle/idempotency/FHP contracts.
- Real MP4 acceptance remains required: H.264, 1280×720, 24 fps, 15–45 seconds, and four extracted QA frames.

## Limitations

The REA reducer agent failed because the session ran out of credits; all eight subsystem agents completed and their raw structured outputs are preserved. Static analysis does not prove all runtime behavior, visual quality, provider availability, or license compatibility for future reuse. The OpenMontage sidecar is not connected by this branch and no AGPL source is imported.

The branch also preserves unrelated pre-existing local edits in `README.md` and `scripts/logic_engine.py`; they are intentionally not included in the MPVE changeset.
