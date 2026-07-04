# Master Pedagogy Skill — Claude Edition (v5 / c1.1)

This is a Claude-specific overhaul of [Master-Pedagogy-Skill](https://github.com/XenogenesisXtreme/Master-Pedagogy-Skill), rebuilt to run as an [Anthropic Agent Skill](https://docs.claude.com/en/docs/build-with-claude/skills) in Claude.ai, Claude Code, and the Claude API.

The original skill's core idea — a multi-agent tutor that gates progress on real mastery checks — is kept intact. This version adds a full gamification layer on top of it: a persistent mascot companion, real interactive quiz widgets (in clients that support them), rotating mini-game formats instead of one repeated quiz type, a badge/streak system with actual code behind the XP math, and a 12-theme narrative quest library.

See `CHANGELOG.md` for the full list of what changed from the original v4.2 and why.

## What's in here

```
SKILL.md                              — the skill itself (read this first)
references/
  narrative_quests.md                 — 12 story themes + hobby-personalization notes
  challenge_deck.md                   — the 7 quiz/mini-game formats, spec for each
  rewards_and_companion.md            — badge list, leveling table, companion voice guide
scripts/
  logic_engine.py                     — analogy-seeding, mind-map generation
  quiz_module.py                      — XP/level math, streaks, badges, format rotation
```

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

## License

MIT — see `LICENSE`. Copyright is currently attributed to XenogenesisXtreme (the original repo owner); change the name in `LICENSE` if that's not correct for how you want this published.

## Credit

Built on the structure and intent of the original [Master-Pedagogy-Skill](https://github.com/XenogenesisXtreme/Master-Pedagogy-Skill) (Agents A–D, first-principles relatability filter, mandatory diagram/formula formatting rules). This edition adds Agent E (the Companion), the Challenge Deck, the badge/reward system, and rendering-mode-aware interactive quizzes.
