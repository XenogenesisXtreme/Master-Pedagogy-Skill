#!/usr/bin/env python3
"""
logic_engine.py — First-principles + relatability helpers for Master Pedagogy v5.

Three jobs:
1. build_analogy_seed(hobby)   -> structural hints about a hobby to seed analogies from
                                   (this doesn't write the analogy for you — it gives you
                                   the raw material so the analogy is grounded in something
                                   real about the hobby, not a generic surface reference)
2. core_truth(formula, plain)  -> formats the "strip the formula to a physical truth" block
3. generate_mindmap(...)       -> emits Mermaid.js syntax for the knowledge-tree mind map

Run this file directly (`python3 logic_engine.py`) to see a demo of all three.
No third-party dependencies — stdlib only, safe to run in any sandbox.
"""

from __future__ import annotations
from typing import Iterable


# A small knowledge base of structural traits per hobby category, used to seed
# analogies that go beyond "here's a sport metaphor" surface-level matching.
# Keys are matched case-insensitively as substrings of the learner's stated hobby.
_HOBBY_TRAITS = {
    "music":      ["timing/rhythm", "layering multiple parts into one whole", "practice = repetition with feedback", "tuning = small continuous correction"],
    "guitar":     ["timing/rhythm", "tension and release (string tension ~ physical tension)", "muscle memory built through repetition"],
    "piano":      ["independent hands doing different things at once", "timing/rhythm", "reading two staves simultaneously = parallel processing"],
    "cooking":    ["ratios and proportions", "timing multiple processes to finish together", "small input changes → big output changes (seasoning, heat)", "irreversible steps vs. adjustable ones"],
    "chess":      ["positional trade-offs", "thinking several moves ahead (prediction)", "sacrificing short-term for long-term gain"],
    "gaming":     ["resource management", "risk/reward trade-offs", "pattern recognition under time pressure", "iterating fast after failure (respawn/retry loop)"],
    "esports":    ["resource management", "reaction time vs. planning", "team roles/specialization"],
    "sports":     ["momentum", "energy expenditure vs. pacing", "team roles/specialization", "practice reps building reliability"],
    "basketball": ["momentum", "angles and trajectories (shooting arcs)", "spacing/positioning"],
    "soccer":     ["momentum", "angles and trajectories (passing/shots)", "space and positioning"],
    "football":   ["momentum", "formations = structured positioning", "risk/reward play-calling"],
    "dance":      ["timing/rhythm", "balance and center of mass", "muscle memory through repetition"],
    "art":        ["proportion and scale", "light/shadow = gradients", "composition = balance of elements"],
    "photography":["light as a quantity that can be measured and controlled", "framing = choosing what to include/exclude", "exposure = trade-off between multiple settings"],
    "coding":     ["logical dependencies (prerequisites)", "debugging = isolating variables", "abstraction layers"],
    "reading":    ["narrative structure = cause and effect chains", "foreshadowing = using early info to predict later info"],
    "cars":       ["mechanical trade-offs (power vs. efficiency)", "systems that depend on each other (engine/transmission)", "tuning = small continuous correction"],
    "fashion":    ["proportion and balance", "trends = patterns that shift over time", "layering"],
}

_GENERIC_TRAITS = [
    "getting better through repetition with feedback",
    "trade-offs between competing goals",
    "small changes early compounding into big differences later",
]


def build_analogy_seed(hobby: str) -> dict:
    """Return structural traits of a hobby to ground analogies in, plus a fallback.

    This is intentionally NOT trying to generate the analogy itself — that's a
    creative step best done by the model with full context on the subject being
    taught. This just supplies grounded raw material so the analogy isn't generic.
    """
    hobby_lower = (hobby or "").lower().strip()
    matched_traits: list[str] = []
    matched_keys: list[str] = []

    for key, traits in _HOBBY_TRAITS.items():
        if key in hobby_lower or hobby_lower in key:
            matched_traits.extend(traits)
            matched_keys.append(key)

    if not matched_traits:
        return {
            "hobby": hobby,
            "matched_category": None,
            "traits": _GENERIC_TRAITS,
            "note": (
                f"No specific trait bank for '{hobby}' — use the generic traits below, "
                "or better: ask the learner one follow-up question about what they "
                "actually *do* in this hobby (a specific motion, decision, or ratio) "
                "and build the analogy from that concrete detail instead."
            ),
        }

    return {
        "hobby": hobby,
        "matched_category": matched_keys,
        "traits": matched_traits,
        "note": "Pick 1-2 traits that most directly mirror the mechanism of the concept being taught — don't try to use all of them.",
    }


def core_truth(formula_name: str, plain_english: str, physical_truth: str) -> str:
    """Format the 'strip the formula to a Core Truth' block used at the start of a concept."""
    return (
        f"**{formula_name}**\n"
        f"Plain English: {plain_english}\n"
        f"Core Truth: {physical_truth}"
    )


def generate_mindmap(topic: str, prerequisites: Iterable[str], subunits: Iterable[str], completed: Iterable[str] = ()) -> str:
    """Emit Mermaid.js mind-map syntax showing prerequisites -> topic -> subunits.

    Completed subunits get a ✅ prefix so progress is visually obvious at a glance.
    Render this with the `diagram` visualize module, or as a fenced ```mermaid block
    in Text Mode (most chat renderers will draw it as-is).
    """
    completed_set = set(completed)
    lines = ["mindmap", f"  root(({topic}))"]

    if prerequisites:
        lines.append("    Prerequisites")
        for p in prerequisites:
            lines.append(f"      {p}")

    lines.append("    Sub-units")
    for s in subunits:
        prefix = "✅ " if s in completed_set else ""
        lines.append(f"      {prefix}{s}")

    return "\n".join(lines)


if __name__ == "__main__":
    print("=== build_analogy_seed('guitar') ===")
    print(build_analogy_seed("guitar"))
    print()
    print("=== build_analogy_seed('underwater basket weaving') ===")
    print(build_analogy_seed("underwater basket weaving"))
    print()
    print("=== core_truth demo ===")
    print(core_truth("F = ma", "Push strength depends on weight and desired speed.",
                      "Heavier things need more push to speed up the same amount."))
    print()
    print("=== generate_mindmap demo ===")
    print(generate_mindmap(
        topic="Rotational Mechanics",
        prerequisites=["Linear Dynamics", "Torque"],
        subunits=["Angular Velocity", "Moment of Inertia", "Angular Momentum"],
        completed=["Angular Velocity"],
    ))
