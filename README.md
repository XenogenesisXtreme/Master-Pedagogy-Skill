# Master Pedagogy Skill

An adaptive, mastery-gated tutoring framework for Science, Mathematics, and technical subjects. It combines first-principles teaching with exam-aware curricula, interactive learning mechanics, narrative options, and reusable helper scripts.

The skill is designed for agent clients that can load `SKILL.md` (including Claude and Manus). **Available behavior depends on the host:** interactive widgets, cross-session persistence, rendered visuals, and generated video require supporting tools or application infrastructure.

- **Website version:** [Gamified Learn](https://gamifiedlearn-5vbwad52.manus.space/) (requires a Manus account)
- **Main instructions:** [`SKILL.md`](SKILL.md)
- **Change history:** [`CHANGELOG.md`](CHANGELOG.md)

## What it includes

- **Exam profiles:** General / Conceptual Learning, NEET, JEE, IOQM, and NSEJS, with profile-specific teaching priorities, question formats, and mastery expectations.
- **Three learning modes:** Standard Tutorial, Narrative Quest, and confirmed Floathead Physics (FHP) Mode.
- **Adaptive mastery workflow:** prerequisite audits, incremental sub-units, quizzes, hints, remedial loops, support mode, and mastery gates.
- **Learner controls:** `why`, `visual`, `analogy`, `formal`, `hint`, `simpler`, `harder`, `review`, `exam mode`, `recap`, `video`, and `fhp`.
- **Persistent-state specification:** a canonical `LearnerState` schema for preferences, exam goals, mastery evidence, misconceptions, review scheduling, and session continuity.
- **Gamification:** XP, levels, streaks, combos, badges, Boss Battles and Rematches, branching paths, Scientist / Explorer Cards, and spaced review.
- **Visual support:** renderer-safe Mermaid mind maps and skill trees, plus instructions to create and check actual diagrams when rendering is available.
- **Optional video planning:** validated 16:9 storyboard generation and SVG scene-card fallback for lessons where motion or sequence helps.

## Exam profiles

The skill keeps the conceptual core stable while adapting how it is taught and assessed. Select a primary profile before curriculum design; secondary goals can be recorded without mixing incompatible styles in one question set.

| Profile | Emphasis | Typical assessment |
|---|---|---|
| **General / Conceptual Learning** | First principles, intuition, visual models, transfer, and real-world meaning | Explanations, worked examples, varied applications, and learner-generated questions |
| **NEET** | NCERT-aligned Biology, Chemistry, and Physics; precise terminology, diagrams, distinctions, and efficient recall | Single-best-answer MCQs, statement questions, diagram interpretation, distractor analysis, and timed practice |
| **JEE** | Mathematical modeling, derivations, multi-concept links, and rigorous problem solving | Multi-step and numerical problems, algebraic verification, and timed mixed sets |
| **IOQM** | Discovery, proof-oriented reasoning, patterns, invariants, geometry, number theory, and combinatorics | Non-routine problems, proof sketches, structured hints, counterexamples, and transfer |
| **NSEJS** | Integrated junior-science foundations across Physics, Chemistry, Biology, and Earth/space science | Mixed-subject reasoning, experiment and data interpretation, diagrams, and application questions |

Content is labeled **Core Preparation**, **Useful Extension**, or **Beyond Target Level**. Timed practice follows untimed conceptual mastery rather than replacing it.

## Learning modes and controls

- **Standard Tutorial** — direct, structured teaching with grounded analogies based on an interest the learner chooses.
- **Narrative Quest** — the same learning and mastery gates within a persistent story theme.
- **Floathead Physics (FHP)** — a rigorous, time-intensive rediscovery path. It requires explicit learner confirmation and does not require a hobby analogy. Its protocol moves from observation and question-setting through assumptions, limiting cases, modeling, derivation, checks, application, and limitations.

Learners can request local changes at any point—for example, `hint`, `simpler`, or `formal`. Commands change the teaching approach, not the underlying prerequisites or mastery requirements. `exam mode` applies the selected profile's assessment style; `video` offers an optional visual supplement when useful.

## LearnerState and persistence

`SKILL.md` defines one canonical `LearnerState` containing identity and learning preferences, exam goals, topic progress, mastery evidence, misconceptions, review queues, rewards, accessibility preferences, and pending session choices.

**The schema is a specification, not a storage service.** A host application must provide a database, file, session store, or equivalent mechanism to persist it between sessions. The skill keeps demonstrated conceptual mastery separate from XP, badges, and narrative progress.

## What is implemented in this repository

| Component | Implemented capability | Boundary |
|---|---|---|
| [`scripts/logic_engine.py`](scripts/logic_engine.py) | Analogy seeds, Core Truth formatting, FHP mode resolution/details, deterministic Mermaid mind maps and skill trees, Scientist Card helpers | Exam-specific curriculum behavior and learner-state persistence are directed by `SKILL.md`; this module does not implement a full tutoring application |
| [`script/logic_engine.py`](script/logic_engine.py) | Compatibility shim for older singular-path imports | Delegates to the canonical `scripts/` implementation |
| [`scripts/quiz_module.py`](scripts/quiz_module.py) | XP, levels, streaks, badges, combo, challenge-format, review, and Socratic helpers | The host/agent orchestrates the session and stores learner state |
| [`scripts/video_explainer.py`](scripts/video_explainer.py) | Provider-neutral storyboard construction and validation; deterministic SVG scene cards and a manifest as a fallback | **Does not generate an MP4 by itself.** A video provider or local rendering backend must be connected for actual video output |
| [`tests/`](tests/) | Unit tests for diagram/FHP helpers and storyboard/fallback behavior | Run with the command below |

## Quick start

Read [`SKILL.md`](SKILL.md) first. For a new topic, the intended flow is:

1. Initialize or resume learner state; choose an exam profile, subject, and learning mode.
2. Audit prerequisites and agree on the learning route.
3. Teach one sub-unit at a time, using appropriate visualizations and examples.
4. Assess mastery, give hints or a remedial loop when needed, then offer the learner a branching choice.
5. Record evidence and progress; schedule review and update the concept/skill maps.

For local helper use:

```python
from scripts.logic_engine import generate_mindmap, generate_skill_tree, fhp_mode_details

print(fhp_mode_details())
print(generate_mindmap("Rotational Mechanics", ["Linear Dynamics"], ["Torque", "Angular Momentum"]))
```

To build an optional video storyboard and static fallback scene cards:

```python
from scripts.video_explainer import build_storyboard, render_static_fallback

storyboard = build_storyboard(
    topic="Newton's Second Law",
    objective="Relate net force, mass, and acceleration.",
    narration="Observe the motion. Define the variables. Derive the relationship. Check the units.",
    mastery_check="Predict how acceleration changes when net force doubles.",
    exam_profile="JEE",
    style="whiteboard",
    equations=["F = ma"],
    derived=True,
)
render_static_fallback(storyboard, "build/video-scenes")
```

FHP video storyboards require `derived=True` so a video supplements a completed written derivation rather than replacing it.

## Installation and activation

Clone the repository:

```bash
git clone https://github.com/XenogenesisXtreme/Master-Pedagogy-Skill.git
cd Master-Pedagogy-Skill
```

Install or attach the skill according to your agent client's skill-directory or project-instructions workflow. The skill is intended to activate when a learner asks to study, learn, understand, review, or prepare for an exam. The host must support any optional interactive or media tools the session uses.

## Tests

The current tests use Python's standard library `unittest` runner:

```bash
python -m unittest discover -s tests -v
```

## Feature-retention audit

The `MPS-V5-c2.4-Exam-Profiles` branch was merged into `main`. The exam branch's skill instructions, helper modules, tests, and brand assets are present on `main`. The compared file trees differed only in `README.md` and `CHANGELOG.md`; the newer main-branch documentation edits were retained. This README now documents the merged feature set and clarifies which capabilities are specifications or provider-dependent rather than standalone runtime services.

## License and credit

MIT — see [`LICENSE`](LICENSE). This project builds on the original Master Pedagogy framework and preserves its prerequisite-audit and mastery-gating approach while adding adaptive learning modes, exam-aware guidance, and gamification.
