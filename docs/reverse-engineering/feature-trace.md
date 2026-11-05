# MPVE feature trace

## Evidence status

The target is OpenMontage revision `195eab24478dc9363326aec437aefc3701635ddf`, licensed AGPL-3.0. REA static analysis produced evidence ID `ev_8fb813202915dbc83805b6682ac4232dfba9a94c4e7c26aea394330b7c78b766` over 42 relevant files, 35 parsed JavaScript/TypeScript files, 32,739 AST nodes, and 457 findings. Eight independent subsystem analyses were completed; the reducer agent failed for credit reasons and that failure is retained in the evidence ledger.

## End-to-end observed trace

1. **Request and policy.** OpenMontage reads a pipeline/stage contract, locks the intended runtime, and records provider/asset/review expectations. Evidence: `evidence/runtime.json`, `evidence/routing.json`.
2. **Planning IR.** The renderer accepts either broad time-addressed cuts with typed props or a narrower cinematic scene union. Cuts, overlays, captions, and audio are independent timed layers. Evidence: `evidence/scene-model.json`, `evidence/renderer.json`.
3. **Asset/provider selection.** Provider-neutral selectors discover capabilities, filter explicit routes, rank candidates, preserve provenance, and reject prohibited silent fallbacks. Evidence: `evidence/routing.json`.
4. **Composition.** Remotion sequences each timed unit using deterministic frame rounding. Cinematic scenes add title/video treatments, local fades, source trims, filters, vignette, and deterministic motion. Evidence: `evidence/renderer.json`, `evidence/transitions.json`.
5. **Audio and captions.** TTS/audio are separate capability boundaries. Word timing feeds animated captions or standalone SRT/VTT/JSON. Audio mixing supports fades, ducking, loudness, and exact duration. Evidence: `evidence/audio.json`, `evidence/captions.json`.
6. **Render.** The selected runtime produces an MP4, with staged media and props cleaned after execution. Evidence: `evidence/renderer.json`, `evidence/runtime.json`.
7. **Post-render QA.** The output is probed, sampled at representative positions, checked for audio/subtitle/promise conditions, and assigned pass/revise/fail before presentation. Evidence: `evidence/qa.json`, `evidence/runtime.json`.
8. **Delivery.** A validated export/publish artifact is produced separately from rendering. Evidence: `evidence/runtime.json`.

## MPS comparison

MPS already has the correct pedagogical boundary, asynchronous job lifecycle, idempotent request fingerprinting, local-first renderer, fallback reporting, FHP derivation gate, and honest silent-video behavior. Its main gaps were a render-neutral timeline IR, caption sidecars, schema-like final review, actual media QA before completion, and durable evidence for technical properties.

The `mvpe` branch adds independently authored versions of those highest-value contracts without importing OpenMontage code, assets, names, or implementation text. MPS remains the owner of learner state, intervention decisions, written explanations, and mastery.

## Observed vs inferred vs unknown

- **Observed:** file paths, source contracts, package manifests, schemas, tests, and REA findings in `evidence/*.json`.
- **Inferred:** OpenMontage behaves as a staged timeline compositor with provider-neutral routing and governance-oriented artifact gates.
- **Unknown:** complete runtime rendering success in every environment, all provider availability states, visual parity, and undocumented deployment policies. Static evidence does not prove those behaviors.
