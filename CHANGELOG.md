# Changelog

## v5 / c1.1 — Claude Edition (this version)

Full gamification/engagement overhaul on top of the original v4.2 structure. Mastery gating (Agent A → B → C) and the diagram/formula formatting rules are unchanged — everything below is additive or a replacement of the "fun" layer specifically.

### Added
- **Agent E, The Companion** — a persistent, named mascot with a defined personality and a hard rule against generic filler praise ("Great job!" is explicitly banned; see `references/rewards_and_companion.md`).
- **Rendering Mode Detection** — the skill now checks whether an interactive-widget tool is available and renders quizzes/boss battles as real clickable widgets when it is, falling back to structured rich text when it isn't. Works in both Claude.ai-style clients and Claude Code/terminal/API contexts.
- **The Challenge Deck** (`references/challenge_deck.md`) — 7 distinct mini-game/question formats (Speed Round, Build-It, Debug-It, Prediction Market, Scenario MCQ, True/False Gauntlet, Boss Battle), each with its own pass/fail logic and both a Rich Mode and Text Mode rendering spec. An anti-repeat picker (`scripts/quiz_module.py::pick_next_format`) stops the same format running twice in a row.
- **Badge system** — 11 fixed, specifically-triggered badges with bonus XP (`references/rewards_and_companion.md`), computed via `scripts/quiz_module.py::check_badges`.
- **Streak tracking** with escalating callouts, computed via `scripts/quiz_module.py::StreakState`.
- **Leveling/title table** (Novice → Grandmaster) with XP thresholds computed via `scripts/quiz_module.py::level_for_xp` / `title_for_level`, instead of hand-tracked-in-prose XP.
- **Boss Battles** — a dedicated high-difficulty, multi-step, narrative-themed format that triggers specifically on level-up, with partial-credit handling ("battle-scarred" vs. "boss slayer" outcomes).
- **12-theme Narrative Quest library** (`references/narrative_quests.md`) — Space Mission, Detective, Heist, Fantasy Trial, Esports Ladder, Culinary Competition, Sports Season, Escape Room, Startup, Expedition, Courtroom, Time Loop — each with explicit hobby-personalization notes, replacing the original's two example themes.
- **Spaced repetition** — `scripts/quiz_module.py::schedule_review` flags concepts for a follow-up review question 1 and 3 chapters later.
- **`scripts/logic_engine.py::build_analogy_seed`** — a small hobby-trait knowledge base used to ground analogies in something structurally real about the learner's hobby, with a generic fallback + a "ask a follow-up question" instruction for hobbies not in the bank.
- **Session Setup step** — Companion naming and tone/humor calibration happen once per learner, not re-asked every chapter (the hobby question still resets per chapter, since analogies depend on it).
- **Chapter Trophy Card** deliverable — a shareable end-of-chapter summary (XP, badges, streak record, Companion send-off), in addition to the original Cheat Sheet and Problem Set deliverables.

### Changed
- Wrong answers are now explicitly framed as narrative "setbacks," not failures, when a Narrative Quest is active — an intentional pedagogical stance to keep mistakes low-stakes, not just flavor text.
- Sub-unit narrative beats now end on a small hook/cliffhanger rather than a flat stop.
- Deliverables generation now checks for a matching document skill (`docx`/`pdf`) before hand-rolling formatting, if the learner wants a persistent file.

### Unchanged (by design)
- The Agent A (Auditor) → Agent B (Architect) → Agent C (Proctor) mastery-gating pipeline.
- Mandatory diagram rules (Matplotlib-generated, geometrically accurate, textbook-labeled).
- The LaTeX-plus-plain-English hybrid formula presentation rule.
