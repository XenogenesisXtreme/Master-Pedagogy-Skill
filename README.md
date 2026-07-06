# Master Pedagogy Skill  (v5 / c1.2 — Extended Gamification Edition)

This is a Claude-specific overhaul of [Master-Pedagogy-Skill](https://github.com/XenogenesisXtreme/Master-Pedagogy-Skill), rebuilt to run as an [Anthropic Agent Skill](https://docs.claude.com/en/docs/build-with-claude/skills) in Claude.ai, Claude Code, and the Claude API.

The original skill's core idea — a multi-agent tutor that gates progress on real mastery checks — is kept intact. This version adds a full gamification layer on top of it: a persistent mascot companion, real interactive quiz widgets (in clients that support them), rotating mini-game formats instead of one repeated quiz type, a badge/streak system with actual code behind the XP math, a 12-theme narrative quest library, and — in c1.2 — a suite of game-mechanic inspirations: combo multipliers, branching story paths, timed speedruns, Scientist/Explorer Character Cards, Socratic "Show Me the Why" mode, cross-chapter Boss Rematches, and a visual skill-tree progression map.

PS: Use this skill in chat, avoid using it over many chats, it just runs better in one chat

See `CHANGELOG.md` for the full list of what changed from the original v4.2 and why.

---

## What's in here

```
SKILL.md                              — the skill itself (read this first)
references/
  narrative_quests.md                 — 12 story themes + hobby-personalization notes + XG quest integration
  challenge_deck.md                   — the 7 quiz/mini-game formats, spec for each + branching/Socratic integration
  rewards_and_companion.md            — badge list (16 total), leveling table, companion voice guide (60+ voice lines)
  scientist_cards.md                  — full database of 40+ Scientist/Explorer Character Cards + dynamic generation rules
scripts/
  logic_engine.py                     — analogy-seeding, mind-map generation, scientist card builder, skill-tree emitter
  quiz_module.py                      — XP/level math, streaks, badges, combo multiplier, Boss Rematch queue, Socratic chain generator
```

---

## Installing

**Claude.ai / Claude apps**: package this folder as a `.skill` file (see below) and upload it — Anthropic's docs cover the current upload flow, since this changes over time: https://docs.claude.com

**Claude Code**: copy this whole folder into your skills directory, e.g.

```bash
mkdir -p ~/.claude/skills
cp -r . ~/.claude/skills/master-pedagogy-v5
```

**Packaging as `.skill`**: if you have Anthropic's `skill-creator` tooling available, run:

```bash
python -m scripts.package_skill /path/to/this/folder
```

---

## How to Use on Manus

This skill is designed to be dropped into any Manus project and activated automatically when a learner asks to study or master a topic. Here's how to set it up and use it:

### Installation

**Step 1: Clone into your Manus project**

```bash
git clone https://github.com/XenogenesisXtreme/Master-Pedagogy-Skill.git
cd Master-Pedagogy-Skill
```

**Step 2: Add the skill to your project configuration**

Copy the entire folder contents into your Manus project's skills directory. The `SKILL.md` file will be auto-detected by Manus as an agent skill.

**Step 3 (optional): Use as a project-level instruction**

If you want the skill to be active by default on every task (without needing to be triggered), add its contents to your project's instructions via Manus settings. Otherwise, it will auto-activate when the user mentions learning, studying, mastering, or reviewing any topic.

### Activation Triggers

The skill auto-activates when the user says anything like:

| Example Trigger | What It Activates |
|---|---|
| "Teach me [topic]" | Full learning session |
| "Help me understand [topic]" | Full learning session |
| "Quiz me on [topic]" | Skips teaching, goes straight to assessment |
| "I want to learn/master [topic]" | Full learning session |
| "Help me study for [exam/subject]" | Full learning session with exam prep framing |
| "I'm struggling with [topic]" | Skips to Support Mode directly |

You do **not** need to say "gamify this" — the gamification layer is the default delivery mechanism.

### What to Expect

Once activated, the session follows this flow:

1. **Session Setup** — The Companion (Agent E) introduces itself, asks for a name, calibrates tone ("thick and fast," "dry and witty," or "mostly serious"), and asks the learner's depth preference (quick quizzes vs. step-by-step "why" explanations).
2. **Prerequisite Audit** — Agent A checks what foundational knowledge is needed before the chapter begins.
3. **Quest Selection** — Agent D offers a choice: standard tutorial or a narrative quest (12 themes, personalized to the learner's hobby).
4. **Learning Loop** — Each sub-unit goes: Architect teaches → Proctor tests (with Scientist Cards, Socratic mode, and branching paths) → Gamemaster awards XP/streaks/combos/badges → Companion reacts.
5. **Boss Battles** — Every 500 XP triggers a level-up and a Boss Battle (a multi-step, real-world application problem).
6. **Chapter Deliverables** — On completion: Cheat Sheet, Problem Set, and Trophy Card (with Scientist Card collection recap).

### Rendering Modes

The skill detects Manus's capabilities automatically:

- **Rich Mode** (if Manus's `visualize` widget system is available): Interactive quiz widgets, animated progress bars, styled card widgets.
- **Text Mode** (default fallback): Rich text with Unicode progress bars, boxed callouts, emoji UI elements, and lettered answer choices.

You don't need to configure this — the skill checks on startup and stays consistent.

### Example Session

```
You: Teach me rotational mechanics, I like guitar.

Companion: [introduces itself, asks for name and vibe]
...
Agent A: [checks prerequisites — linear dynamics, torque]
Agent D: [offers quest: Space Mission, Detective, or Startup]
You: Space Mission, thick and fast jokes.
...
[The session begins with narrative, quizzes, Scientist Cards,
 combo multipliers, and branching paths — all themed to the ship
 keeping its gyroscopes stabilized for re-entry.]
```

### Tips for Best Results

State your hobby early so the analogy engine builds everything around it. Answer honestly on the audit — Agent A will fill gaps before they become problems. Use branching paths after each quiz: pick "Go Deeper" if you want the math, "Apply It" if you want real-world context, or "Power On" to stay fast-paced. Ask "why" — any "why does that work" question triggers Socratic mode automatically. Don't skip the Scientist Cards — they're the human stories behind the formulas, and they're collected across chapters for a real sense of accumulation.

---

## Recent Changes

### v5 c1.2 — Extended Gamification Edition (XG) — Latest

Released as branch `V5_c1.2_XG` (July 2026). Added nine new game-mechanic-inspired features:

| Feature | Description |
|---|---|
| **Combo multiplier system** | 1.5x XP after 2 consecutive fast clears (<90s each), 2.0x after 4. Resets on miss or slow clear. Companion announces activations and expirations. |
| **Branching paths** | After every quiz, the learner chooses: "Go Deeper" (more math/proof), "Apply It" (real-world case study), or "Power On" (next sub-unit). Shapes narrative beat and quiz format. |
| **Timed speedrun challenges** | After a fast clear, the learner can attempt a 60-second bonus round for +50 XP. No penalty for failing. |
| **Unlockable lore cards** | Story-themed collectibles tied to the active narrative quest. Different archives per theme (mission logs, cold case files, ancient scrolls, etc.). |
| **Scientist/Explorer Character Cards** | Full database of 40+ pre-built cards covering physics, optics, electromagnetism, chemistry, biology, astronomy, mathematics, and history. Each card has name, discovery, significance, human detail, and quote. Emitted before quizzes as collectible info blocks. |
| **Socratic "Show Me the Why" mode** | Guided 3–5 step derivation chains where the learner predicts each step (Prediction Market format per step). Activated by depth preference, "why" questions, or manual request. Awards Curious Mind badge. |
| **Cross-chapter Boss Rematches** | Concepts struggled with 3+ chapters ago resurface paired with a current concept. 1.5x XP and a new "Revenge" badge. Framed narratively as a second chance. |
| **Visual skill-tree progression map** | Mermaid diagram showing completed, in-progress, and locked chapters across the learner's entire journey. Rendered at chapter start and updated on completion. |
| **Easter egg callbacks** | Companion stores unusually creative learner answers and references them later in different contexts. |

Five new badges added: Combo Breaker (+15 XP), Untouchable (+40 XP), Speed Demon (+20 XP), Lore Keeper (+50 XP), Revenge (+35 XP).

### v5 c1.1 — Initial Claude Overhaul

The original Claude-specific version that added the gamification layer (companion, badges, streaks, levels, boss battles, narrative quests, challenge deck) on top of the core v4.2 mastery-gating framework.

---

## License

MIT — see `LICENSE`. Copyright is currently attributed to XenogenesisXtreme (the original repo owner); change the name in `LICENSE` if that's not correct for how you want this published.

## Credit

Built on the structure and intent of the original [Master-Pedagogy-Skill](https://github.com/XenogenesisXtreme/Master-Pedagogy-Skill) (Agents A–D, first-principles relatability filter, mandatory diagram/formula formatting rules). This edition adds Agent E (the Companion), the Challenge Deck, the badge/reward system, rendering-mode-aware interactive quizzes, and the Extended Gamification suite (combos, branching, speedruns, Scientist Cards, Socratic mode, Boss Rematches, skill tree).
