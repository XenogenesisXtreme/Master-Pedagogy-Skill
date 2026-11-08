# MPS expanded implementation status

Updated on the `mvpe` branch after integrating the expanded teaching and video workflow prompt.

## Fully implemented and tested

- Unified root MPS skill references MPVE as an attached capability rather than a separate tutor.
- MPVE request validation, FHP derivation gate, caption sidecars, asynchronous job lifecycle, duplicate protection, Remotion-first rendering, deterministic fallback, SVG fallback, and real media QA.
- Textbook-style equation rendering in the Remotion composition.
- Reusable `SubjectModule` / `TopicRoute` / `SubjectModuleRegistry` contracts.
- Fluid Mechanics module with nine topic routes, including hydrostatic pressure, buoyancy, continuity, Bernoulli, viscosity, surface tension, and applications.
- JSON-backed `LearnerSessionState` and `LearnerStateStore` for local session continuity.
- `MPSRecoveryOrchestrator` with per-concept incorrect counters, three-error threshold, diagnosis classification, MPS-injected video decision, duplicate recovery protection, FHP blocking, MPVE submission hook, status attachment, and recovery reset.
- 32 repository tests pass, including four new expanded-workflow tests.

## Implemented but not deployed as a hosted plugin

- The orchestrator can call `MPVEEngine` or an HTTP client through an injected callback, but no public authenticated plugin endpoint is deployed.
- The local HTTP API works through `scripts/mpve_server.py`; production authentication, remote object storage, durable queues, rate limits, and deployment configuration remain host responsibilities.
- The root MPS skill can instruct ChatGPT how to submit and poll MPVE jobs, but the ChatGPT runtime must provide an allowed backend/tool connection for actual network calls.

## Requires external providers or configuration

- Narration/TTS and music are not claimed unless a configured provider generates and QA-checks them. The local Remotion render may contain silent audio.
- Hosted rendering requires a caller-supplied provider adapter.
- Persistent cross-conversation learner state requires a configured durable store; the local JSON store is real persistence only within the configured filesystem.

## Not yet implemented

- A production ChatGPT plugin deployment with managed authentication and artifact hosting.
- Automatic publication of the video artifact into a remote learner-facing chat surface.
- A complete subject-module library for Mechanics, Chemistry, Biology, and Mathematics. The module interface is ready; Fluid Mechanics is the first complete implementation.

Do not describe deployment-dependent or not-yet-implemented items as operational merely because the skill or API documents them.
