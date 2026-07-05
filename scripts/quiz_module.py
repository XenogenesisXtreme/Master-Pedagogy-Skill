#!/usr/bin/env python3
"""
quiz_module.py — Gamification math + quiz logistics for Master Pedagogy v5 (XG Edition).

Single source of truth for anything numeric: XP totals, levels, streaks, badges,
combo multipliers, Boss Rematch flagging, Socratic chain generation, which Challenge
Deck format comes next, and spaced-repetition scheduling.

Keeps Agent D from hand-waving XP math in prose (easy to get inconsistent across
a long session otherwise).

Run this file directly (`python3 quiz_module.py`) to see a demo of all functions.
No third-party dependencies — stdlib only.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Iterable
import random
import time


# ── Constants ──────────────────────────────────────────────────────────────────

LEVEL_XP_STEP = 500

LEVEL_TITLES = {
    1: "Novice", 2: "Apprentice", 3: "Adept", 4: "Specialist",
    5: "Expert", 6: "Master",
}

# Bonus XP per badge — keep in sync with references/rewards_and_companion.md
BADGE_BONUS_XP = {
    "first_blood": 20,
    "on_fire": 30,
    "blazing": 60,
    "comeback": 25,
    "curious_mind": 25,
    "bug_hunter": 30,
    "good_read": 25,
    "boss_slayer": 75,
    "battle_scarred": 40,
    "no_skips": 30,
    "long_memory": 25,
    "revenge": 35,  # XG: Boss Rematch win badge bonus
}

CHALLENGE_FORMATS = [
    "speed_round", "build_it", "debug_it", "prediction_market",
    "scenario_mcq", "true_false_gauntlet",
]  # boss_battle is handled separately — only on level-up


# ── XP & Leveling ──────────────────────────────────────────────────────────────

def level_for_xp(xp: int) -> int:
    """Level 1 at 0 XP, +1 level per LEVEL_XP_STEP XP."""
    return (xp // LEVEL_XP_STEP) + 1


def title_for_level(level: int) -> str:
    if level in LEVEL_TITLES:
        return LEVEL_TITLES[level]
    return f"Grandmaster, Level {level}"


def award_xp(
    current_xp: int,
    base_amount: int,
    combo_multiplier: float = 1.0,
    badges_earned: list[str] | None = None,
    is_boss_rematch: bool = False,
) -> dict:
    """Apply base XP + combo multiplier + badge bonuses.

    Returns a dict with old/new XP, level status, and whether a level-up happened.
    """
    old_level = level_for_xp(current_xp)
    effective_base = int(base_amount * combo_multiplier)

    # Boss Rematch gets 1.5x on top of everything
    if is_boss_rematch:
        effective_base = int(effective_base * 1.5)

    bonus = sum(BADGE_BONUS_XP.get(b, 0) for b in (badges_earned or []))
    new_xp = current_xp + effective_base + bonus
    new_level = level_for_xp(new_xp)

    return {
        "old_xp": current_xp,
        "new_xp": new_xp,
        "base_amount": base_amount,
        "combo_multiplier": combo_multiplier,
        "effective_xp_from_pass": effective_base,
        "badge_bonus": bonus,
        "is_boss_rematch": is_boss_rematch,
        "old_level": old_level,
        "new_level": new_level,
        "leveled_up": new_level > old_level,
        "title": title_for_level(new_level),
        "boss_battle_unlocked": new_level > old_level,
    }


# ── Streak Tracking ────────────────────────────────────────────────────────────

@dataclass
class StreakState:
    current: int = 0
    best: int = 0

    def update(self, correct_first_try: bool) -> "StreakState":
        if correct_first_try:
            self.current += 1
            self.best = max(self.best, self.current)
        else:
            self.current = 0
        return self


# ── Combo System (NEW — XG Edition) ──────────────────────────────────────────

@dataclass
class ComboState:
    """Tracks the combo multiplier state.

    Combo is about speed AND consistency:
      - 2 consecutive first-try clears in <90s each → 1.5x for next 2
      - 4 consecutive first-try clears in <90s each → 2.0x for next 4
      - Any miss or slow clear → reset to 0
    """
    consecutive_quick_clears: int = 0
    remaining_boosted_uses: int = 0
    current_multiplier: float = 1.0
    quick_threshold_seconds: int = 90  # sub-units cleared faster than this count
    boss_rematch_multiplier: float = 1.5  # XG: Boss Rematch XP bonus

    def record_clear(self, time_taken_seconds: int, correct: bool) -> str:
        """Record a sub-unit clear. Returns the current multiplier or 'reset'."""
        if not correct:
            self._reset()
            return "reset"

        if time_taken_seconds > self.quick_threshold_seconds:
            self._reset()
            return "reset"

        self.consecutive_quick_clears += 1

        if self.remaining_boosted_uses > 0:
            self.remaining_boosted_uses -= 1
            if self.remaining_boosted_uses == 0:
                self.current_multiplier = 1.0
                self.consecutive_quick_clears = 0
                return "expired"
            return f"x{self.current_multiplier}"

        # Determine if we hit a threshold
        if self.consecutive_quick_clears == 4:
            self.current_multiplier = 2.0
            self.remaining_boosted_uses = 3  # this one counts, 3 more boosted
            return "upgrade_to_2x"
        elif self.consecutive_quick_clears == 2:
            self.current_multiplier = 1.5
            self.remaining_boosted_uses = 1  # this one counts, 1 more boosted
            return "activate_1.5x"
        elif self.consecutive_quick_clears == 1:
            return "building"
        elif self.consecutive_quick_clears == 3:
            return "building"  # one more for upgrade

        return f"x{self.current_multiplier}"

    def _reset(self):
        self.consecutive_quick_clears = 0
        self.remaining_boosted_uses = 0
        self.current_multiplier = 1.0

    def get_multiplier(self) -> float:
        return self.current_multiplier


# ── Badge System ───────────────────────────────────────────────────────────────

def check_badges(
    *,
    first_ever_pass: bool = False,
    streak: int = 0,
    comeback: bool = False,
    asked_why: bool = False,
    debug_it_solved: bool = False,
    prediction_correct_with_reason: bool = False,
    boss_battle_result: str | None = None,  # "clean" | "partial" | None
    no_skip_chapter_complete: bool = False,
    spaced_review_correct: bool = False,
    boss_rematch_win: bool = False,  # XG
) -> list[str]:
    """Given flags about what just happened, return the list of badge IDs earned.

    Deliberately conservative — most calls should return an empty list. See
    references/rewards_and_companion.md for the "don't devalue badges" rule.
    """
    earned = []
    if first_ever_pass:
        earned.append("first_blood")
    if streak == 3:
        earned.append("on_fire")
    if streak == 6:
        earned.append("blazing")
    if comeback:
        earned.append("comeback")
    if asked_why:
        earned.append("curious_mind")
    if debug_it_solved:
        earned.append("bug_hunter")
    if prediction_correct_with_reason:
        earned.append("good_read")
    if boss_battle_result == "clean":
        earned.append("boss_slayer")
    elif boss_battle_result == "partial":
        earned.append("battle_scarred")
    if no_skip_chapter_complete:
        earned.append("no_skips")
    if spaced_review_correct:
        earned.append("long_memory")
    if boss_rematch_win:
        earned.append("revenge")
    return earned


# ── Challenge Format Picker ────────────────────────────────────────────────────

def pick_next_format(history: list[str], rng: random.Random | None = None) -> str:
    """Pick the next Challenge Deck format, never repeating the immediately-previous one.

    `history` is the list of formats used so far this chapter, most recent last.
    Boss Battle is intentionally excluded — that's triggered separately on level-up.
    """
    rng = rng or random
    last = history[-1] if history else None
    choices = [f for f in CHALLENGE_FORMATS if f != last]
    return rng.choice(choices)


# ── Spaced Repetition & Boss Rematches ─────────────────────────────────────────

def schedule_review(chapter_index: int, concept: str, needed_remedial: bool = False) -> list[dict]:
    """Spaced-repetition schedule: review this concept 1 chapter and 3 chapters later.

    If `needed_remedial` is True, the 3-chapter review is a Boss Rematch candidate.
    """
    reviews = [
        {"review_at_chapter": chapter_index + 1, "concept": concept, "interval": "short"},
    ]

    if needed_remedial:
        reviews.append({
            "review_at_chapter": chapter_index + 3,
            "concept": concept,
            "interval": "long",
            "boss_rematch_candidate": True,
        })
    else:
        reviews.append({
            "review_at_chapter": chapter_index + 3,
            "concept": concept,
            "interval": "long",
        })

    return reviews


@dataclass
class BossRematchQueue:
    """Tracks concepts waiting for a Boss Rematch."""
    entries: list[dict] = field(default_factory=list)
    # Each entry: {"concept": str, "chapter_missed_on": int, "current_chapter": int}

    def flag_rematch(self, concept: str, chapter_missed_on: int, current_chapter: int):
        if current_chapter >= chapter_missed_on + 3:
            self.entries.append({
                "concept": concept,
                "chapter_missed_on": chapter_missed_on,
                "current_chapter": current_chapter,
            })

    def pop_remarch(self, current_chapter: int) -> dict | None:
        """Return the oldest Boss Rematch candidate that is ready (3+ chapters since miss)."""
        ready = [e for e in self.entries if current_chapter >= e["chapter_missed_on"] + 3]
        if not ready:
            return None
        # Pop the oldest
        chosen = ready[0]
        self.entries.remove(chosen)
        return chosen


# ── Socratic Mode Chain Generator ──────────────────────────────────────────────

def socratic_chain(concept: str, topic: str) -> list[dict]:
    """Break a concept into a 3-5 step prediction chain for Socratic mode.

    Each step is a "what happens next?" prediction with 2-3 options.
    Returns a list of step dicts the Proctor can render one at a time.

    This is a structural template — the actual content (questions, options, answers)
    must be filled in by Agent C using its knowledge of the specific topic.
    """
    # The model will fill in the actual step content; this provides the structure.
    # The returned list is a template with placeholder prompts.
    steps = []
    num_steps = random.randint(3, 5)

    for i in range(num_steps):
        step_label = f"Step {i+1} of {num_steps}"
        if i == 0:
            hint = f"Start from the definition of {concept}."
        elif i == num_steps - 1:
            hint = "This is the final step — connect back to the original question."
        else:
            hint = f"Build on Step {i}: apply the result from the previous step."

        steps.append({
            "step_label": step_label,
            "hint": hint,
            "prediction_prompt": "",  # Agent C fills this in
            "options": [],  # Agent C fills in 2-3 options
            "correct_option": None,  # Agent C marks the right one
            "explanation": "",  # Why the correct option is right
        })

    return steps


# ── Scientist Card Collection Tracker ──────────────────────────────────────────

@dataclass
class ScientistCardCollection:
    """Tracks which Scientist/Explorer Character Cards the learner has collected."""
    collected: list[str] = field(default_factory=list)  # list of scientist names
    current_chapter_cards: list[str] = field(default_factory=list)

    def add_card(self, scientist_name: str, chapter_index: int) -> str:
        """Add a card. Returns 'new' if first time, 'duplicate' if already collected."""
        normalized = scientist_name.strip().lower()
        for existing in self.collected:
            if existing.strip().lower() == normalized:
                return "duplicate"
        self.collected.append(scientist_name)
        self.current_chapter_cards.append(scientist_name)
        return "new"

    def get_collection_summary(self) -> dict:
        return {
            "total_collected": len(self.collected),
            "current_chapter": self.current_chapter_cards,
            "chapter_count": len(self.current_chapter_cards),
            "all_cards": list(self.collected),
        }

    def reset_chapter_tracker(self):
        self.current_chapter_cards = []


# ── Demo ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("=== award_xp demo (first-try pass, combo active) ===")
    print("=" * 60)
    result = award_xp(
        current_xp=480,
        base_amount=100,
        combo_multiplier=1.5,
        badges_earned=["on_fire"],
    )
    for k, v in result.items():
        print(f"  {k}: {v}")
    print()

    print("=" * 60)
    print("=== award_xp demo (Boss Rematch win) ===")
    print("=" * 60)
    result = award_xp(
        current_xp=1000,
        base_amount=100,
        combo_multiplier=1.0,
        badges_earned=["revenge"],
        is_boss_rematch=True,
    )
    for k, v in result.items():
        print(f"  {k}: {v}")
    print()

    print("=" * 60)
    print("=== ComboState demo ===")
    print("=" * 60)
    combo = ComboState()
    times = [45, 30, 75, 50, 80, 25, 100, 35, 40]  # last one is >90s = reset
    for i, t in enumerate(times):
        status = combo.record_clear(t, correct=True)
        print(f"  Clear {i+1} in {t}s → multiplier={combo.current_multiplier}x | status: {status}")
    print()

    print("=" * 60)
    print("=== StreakState demo ===")
    print("=" * 60)
    s = StreakState()
    for correct in [True, True, True, False, True]:
        s.update(correct)
        print(f"  correct={correct!s:5} -> current={s.current}, best={s.best}")
    print()

    print("=" * 60)
    print("=== check_badges demo ===")
    print("=" * 60)
    print(check_badges(streak=3, comeback=False))
    print(check_badges(boss_battle_result="clean"))
    print(check_badges(boss_rematch_win=True))
    print()

    print("=" * 60)
    print("=== pick_next_format demo (avoids repeating 'debug_it') ===")
    print("=" * 60)
    rng = random.Random(42)
    hist = ["scenario_mcq", "debug_it"]
    for _ in range(5):
        nxt = pick_next_format(hist, rng=rng)
        print(f"  history={hist} -> next={nxt}")
        hist.append(nxt)
    print()

    print("=" * 60)
    print("=== schedule_review demo ===")
    print("=" * 60)
    print(schedule_review(chapter_index=2, concept="Torque"))
    print(schedule_review(chapter_index=2, concept="Angular Momentum", needed_remedial=True))
    print()

    print("=" * 60)
    print("=== BossRematchQueue demo ===")
    print("=" * 60)
    queue = BossRematchQueue()
    queue.flag_rematch("Torque", chapter_missed_on=1, current_chapter=4)
    queue.flag_rematch("Angular Velocity", chapter_missed_on=2, current_chapter=4)
    queue.flag_rematch("Friction", chapter_missed_on=3, current_chapter=4)  # not ready yet
    print("Ready rematches at ch.4:")
    match = queue.pop_remarch(4)
    while match:
        print(f"  → {match['concept']} (missed on ch.{match['chapter_missed_on']})")
        match = queue.pop_remarch(4)
    print()

    print("=" * 60)
    print("=== socratic_chain demo ===")
    print("=" * 60)
    chain = socratic_chain("Newton's Second Law", "Dynamics")
    print(f"  Generated {len(chain)} steps for 'Newton's Second Law'")
    for step in chain:
        print(f"  {step['step_label']}: {step['hint']}")
    print()

    print("=" * 60)
    print("=== ScientistCardCollection demo ===")
    print("=" * 60)
    collection = ScientistCardCollection()
    print(collection.add_card("Theodore Lyman", chapter_index=3))
    print(collection.add_card("Isaac Newton", chapter_index=3))
    print(collection.add_card("Theodore Lyman", chapter_index=4))  # duplicate
    print(collection.add_card("Marie Curie", chapter_index=3))
    summary = collection.get_collection_summary()
    print(f"  Collection: {summary}")
    collection.reset_chapter_tracker()
    summary2 = collection.get_collection_summary()
    print(f"  After chapter reset: {summary2}")
