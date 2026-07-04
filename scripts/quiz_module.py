#!/usr/bin/env python3
"""
quiz_module.py — Gamification math + quiz logistics for Master Pedagogy v5.

Single source of truth for anything numeric: XP totals, levels, streaks, badge
triggers, which Challenge Deck format comes next, and spaced-repetition scheduling.
Keeps Agent D from hand-waving XP math in prose (easy to get inconsistent across
a long session otherwise).

Run this file directly (`python3 quiz_module.py`) to see a demo of all functions.
No third-party dependencies — stdlib only.
"""

from __future__ import annotations
from dataclasses import dataclass, field
import random

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
}

CHALLENGE_FORMATS = [
    "speed_round", "build_it", "debug_it", "prediction_market",
    "scenario_mcq", "true_false_gauntlet",
]  # boss_battle is handled separately — only on level-up


def level_for_xp(xp: int) -> int:
    """Level 1 at 0 XP, +1 level per LEVEL_XP_STEP XP."""
    return (xp // LEVEL_XP_STEP) + 1


def title_for_level(level: int) -> str:
    if level in LEVEL_TITLES:
        return LEVEL_TITLES[level]
    return f"Grandmaster, Level {level}"


def award_xp(current_xp: int, base_amount: int, badges_earned: list[str] | None = None) -> dict:
    """Apply a base XP award plus any badge bonuses; report whether a level-up happened."""
    old_level = level_for_xp(current_xp)
    bonus = sum(BADGE_BONUS_XP.get(b, 0) for b in (badges_earned or []))
    new_xp = current_xp + base_amount + bonus
    new_level = level_for_xp(new_xp)

    return {
        "old_xp": current_xp,
        "new_xp": new_xp,
        "base_amount": base_amount,
        "badge_bonus": bonus,
        "old_level": old_level,
        "new_level": new_level,
        "leveled_up": new_level > old_level,
        "title": title_for_level(new_level),
        "boss_battle_unlocked": new_level > old_level,
    }


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


def check_badges(*, first_ever_pass: bool = False, streak: int = 0,
                  comeback: bool = False, asked_why: bool = False,
                  debug_it_solved: bool = False, prediction_correct_with_reason: bool = False,
                  boss_battle_result: str | None = None,  # "clean" | "partial" | None
                  no_skip_chapter_complete: bool = False,
                  spaced_review_correct: bool = False) -> list[str]:
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
    return earned


def pick_next_format(history: list[str], rng: random.Random | None = None) -> str:
    """Pick the next Challenge Deck format, never repeating the immediately-previous one.

    `history` is the list of formats used so far this chapter, most recent last.
    Boss Battle is intentionally excluded — that's triggered separately on level-up.
    """
    rng = rng or random
    last = history[-1] if history else None
    choices = [f for f in CHALLENGE_FORMATS if f != last]
    return rng.choice(choices)


def schedule_review(chapter_index: int, concept: str) -> list[dict]:
    """Spaced-repetition schedule: review this concept 1 chapter and 3 chapters later."""
    return [
        {"review_at_chapter": chapter_index + 1, "concept": concept, "interval": "short"},
        {"review_at_chapter": chapter_index + 3, "concept": concept, "interval": "long"},
    ]


if __name__ == "__main__":
    print("=== award_xp demo (first-try pass, one badge) ===")
    print(award_xp(current_xp=480, base_amount=100, badges_earned=["on_fire"]))
    print()

    print("=== StreakState demo ===")
    s = StreakState()
    for correct in [True, True, True, False, True]:
        s.update(correct)
        print(f"  correct={correct!s:5} -> current={s.current}, best={s.best}")
    print()

    print("=== check_badges demo ===")
    print(check_badges(streak=3, comeback=False))
    print(check_badges(boss_battle_result="clean"))
    print()

    print("=== pick_next_format demo (avoids repeating 'debug_it') ===")
    rng = random.Random(42)
    hist = ["scenario_mcq", "debug_it"]
    for _ in range(5):
        nxt = pick_next_format(hist, rng=rng)
        print(f"  history={hist} -> next={nxt}")
        hist.append(nxt)
    print()

    print("=== schedule_review demo ===")
    print(schedule_review(chapter_index=2, concept="Torque"))
