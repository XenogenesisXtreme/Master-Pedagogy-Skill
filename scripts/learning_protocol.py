#!/usr/bin/env python3
"""Deterministic contracts for Master Pedagogy's Intuitive Mastery layer."""

from __future__ import annotations

from typing import Any

TEACHING_SEQUENCE = (
    "intuition",
    "physical_understanding",
    "concept",
    "equation",
    "application",
    "mastery",
)

PROBLEM_SOLVING_STEPS = (
    "understand_situation",
    "identify_given_information",
    "identify_governing_principle",
    "establish_equation",
    "substitute_values",
    "calculate",
    "interpret_answer",
    "exam_insight",
)

DIFFICULTY_LEVELS = {
    1: "intuition",
    2: "foundations",
    3: "application",
    4: "exam_standard",
    5: "challenge",
}

ERROR_CATEGORIES = (
    "conceptual_misunderstanding",
    "physical_interpretation",
    "equation_selection",
    "sign_convention",
    "mathematical_manipulation",
    "unit_conversion",
    "calculation",
    "question_interpretation",
)

_ERROR_HINTS = {
    "unit_conversion": ("unit", "convert", "cm", "mm", "km/h", "minutes"),
    "sign_convention": ("sign", "negative", "direction", "clockwise", "counterclockwise"),
    "calculation": ("arithmetic", "calculate", "addition", "subtraction", "multiply", "divide"),
    "mathematical_manipulation": ("algebra", "rearrange", "factor", "cancel", "solve for"),
    "equation_selection": ("wrong formula", "wrong equation", "which formula", "principle"),
    "question_interpretation": ("misread", "asked for", "what is required", "condition"),
    "physical_interpretation": ("force direction", "motion", "what happens", "meaning", "physical"),
    "conceptual_misunderstanding": ("definition", "why", "concept", "understand", "confused"),
}

_REMEDIATION = {
    "conceptual_misunderstanding": ("restate the definition", "use a simpler physical example", "ask the learner to explain it back"),
    "physical_interpretation": ("rebuild the situation diagram", "identify each physical quantity", "predict the direction or trend"),
    "equation_selection": ("describe the situation first", "name the governing principle", "compare why nearby equations do or do not apply"),
    "sign_convention": ("declare the positive direction", "draw the vectors or axes", "check the result against the chosen convention"),
    "mathematical_manipulation": ("keep one algebraic step per line", "name the operation", "substitute a simple check value"),
    "unit_conversion": ("write units beside every value", "convert before substitution", "check dimensional consistency"),
    "calculation": ("separate the setup from arithmetic", "estimate the answer first", "recalculate with an independent check"),
    "question_interpretation": ("underline the requested quantity", "list givens and unknowns", "translate the wording into a physical question"),
}


def teaching_sequence() -> tuple[str, ...]:
    """Return the default concept-teaching order."""
    return TEACHING_SEQUENCE


def problem_solving_steps() -> tuple[str, ...]:
    """Return the full numerical-problem protocol."""
    return PROBLEM_SOLVING_STEPS


def classify_error(description: str) -> str:
    """Classify a learner error using transparent keyword hints.

    Hosts may replace this heuristic with a richer judge, but they should keep
    the returned category vocabulary stable for LearnerState and analytics.
    """
    text = (description or "").strip().lower()
    for category in ERROR_CATEGORIES:
        if any(hint in text for hint in _ERROR_HINTS[category]):
            return category
    return "conceptual_misunderstanding"


def remediation_plan(category: str) -> tuple[str, ...]:
    """Return the smallest useful remediation sequence for an error category."""
    if category not in ERROR_CATEGORIES:
        raise ValueError(f"Unknown error category {category!r}.")
    return _REMEDIATION[category]


def next_difficulty_level(current: int, demonstrated_mastery: bool, consecutive_misses: int = 0) -> int:
    """Advance only on demonstrated mastery; step back after repeated misses."""
    if current not in DIFFICULTY_LEVELS:
        raise ValueError("current difficulty must be an integer from 1 to 5")
    if consecutive_misses >= 2:
        return max(1, current - 1)
    if demonstrated_mastery:
        return min(5, current + 1)
    return current


def build_micro_lesson_plan(concept: str, level: int = 1, numerical: bool = False) -> dict[str, Any]:
    """Create a compact plan that keeps the learner in control of response size."""
    if level not in DIFFICULTY_LEVELS:
        raise ValueError("level must be an integer from 1 to 5")
    plan = {
        "concept": concept,
        "difficulty_level": level,
        "difficulty_name": DIFFICULTY_LEVELS[level],
        "steps": list(TEACHING_SEQUENCE),
        "response_shape": ["one conceptual idea", "one intuitive explanation", "one useful representation", "one next step"],
    }
    if numerical:
        plan["problem_solving_steps"] = list(PROBLEM_SOLVING_STEPS)
    return plan
