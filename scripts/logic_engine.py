#!/usr/bin/env python3
"""Reusable helpers for Master Pedagogy v5.

The module is dependency-free and intentionally keeps diagram output as Mermaid
source. The emitted diagrams use stable IDs, escaped labels, and explicit theme
styles so they render consistently in Mermaid-capable clients.
"""

from __future__ import annotations

import re
from typing import Iterable, Mapping


LEARNING_MODES = (
    "standard",
    "narrative",
    "fhp",
)

FHP_MODE = "fhp"
FHP_DISPLAY_NAME = "Floathead Physics (FHP) Mode"
FHP_PROTOCOL = (
    "observe",
    "question",
    "knowns_unknowns",
    "assumptions",
    "limiting_case",
    "model",
    "derive",
    "sanity_checks",
    "new_application",
    "limitations",
)


_HOBBY_TRAITS = {
    "music": ["timing/rhythm", "layering multiple parts into one whole", "practice = repetition with feedback", "tuning = small continuous correction"],
    "guitar": ["timing/rhythm", "tension and release", "muscle memory built through repetition"],
    "piano": ["independent hands doing different things at once", "timing/rhythm", "parallel processing"],
    "cooking": ["ratios and proportions", "timing multiple processes to finish together", "small input changes can produce big output changes"],
    "chess": ["positional trade-offs", "thinking several moves ahead", "sacrificing short-term for long-term gain"],
    "gaming": ["resource management", "risk/reward trade-offs", "pattern recognition under time pressure", "iterating after failure"],
    "coding": ["logical dependencies", "debugging by isolating variables", "abstraction layers"],
    "sports": ["momentum", "energy expenditure versus pacing", "team roles and specialization"],
}
_GENERIC_TRAITS = [
    "getting better through repetition with feedback",
    "trade-offs between competing goals",
    "small changes early compounding into big differences later",
]


def build_analogy_seed(hobby: str) -> dict:
    """Return structural traits for an analogy without inventing a hobby."""
    hobby_text = (hobby or "").strip()
    lowered = hobby_text.lower()
    traits: list[str] = []
    matched: list[str] = []
    for key, values in _HOBBY_TRAITS.items():
        if key in lowered or lowered in key:
            traits.extend(values)
            matched.append(key)
    if not traits:
        return {
            "hobby": hobby,
            "matched_category": None,
            "traits": _GENERIC_TRAITS.copy(),
            "note": "Ask for a concrete motion, decision, or ratio before building a specific analogy.",
        }
    return {
        "hobby": hobby,
        "matched_category": matched,
        "traits": traits,
        "note": "Choose one or two traits that mirror the mechanism; state the analogy's limits.",
    }


def core_truth(formula_name: str, plain_english: str, physical_truth: str) -> str:
    """Format a compact Core Truth block."""
    return f"**{formula_name}**\nPlain English: {plain_english}\nCore Truth: {physical_truth}"


def resolve_learning_mode(mode: str | None) -> str:
    """Normalize a learner mode and make FHP discoverable to programmatic callers."""
    value = (mode or "standard").strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "tutorial": "standard",
        "standard_tutorial": "standard",
        "quest": "narrative",
        "narrative_quest": "narrative",
        "floathead": FHP_MODE,
        "floathead_physics": FHP_MODE,
        "floathead_physics_mode": FHP_MODE,
        "fhp_mode": FHP_MODE,
    }
    resolved = aliases.get(value, value)
    if resolved not in LEARNING_MODES:
        raise ValueError(f"Unknown learning mode {mode!r}; choose standard, narrative, or fhp.")
    return resolved


def fhp_mode_details() -> dict:
    """Return the confirmation and protocol contract for Floathead Physics mode."""
    return {
        "id": FHP_MODE,
        "name": FHP_DISPLAY_NAME,
        "requires_confirmation": True,
        "requires_hobby": False,
        "protocol": list(FHP_PROTOCOL),
        "warning": "FHP is rigorous and time-intensive. Ask whether the learner is sure before beginning.",
    }


def _label(value: object) -> str:
    """Escape Mermaid label characters while retaining readable Unicode text."""
    text = re.sub(r"\s+", " ", str(value or "")).strip() or "Untitled"
    return text.replace('"', "'").replace("[", "(").replace("]", ")").replace("{", "(").replace("}", ")")


def _node_id(prefix: str, index: int) -> str:
    return f"{prefix}{index}"


def _diagram_header(direction: str) -> list[str]:
    return [
        "%%{init: {'theme':'base','themeVariables': {'fontFamily':'Inter,Segoe UI,sans-serif','primaryColor':'#111827','primaryTextColor':'#f8fafc','primaryBorderColor':'#22d3ee','lineColor':'#64748b','secondaryColor':'#172554','tertiaryColor':'#1e293b'}}}%%",
        f"flowchart {direction}",
        "    classDef root fill:#7c3aed,stroke:#c4b5fd,color:#ffffff,font-weight:bold,stroke-width:2px",
        "    classDef group fill:#0e7490,stroke:#67e8f9,color:#ecfeff,font-weight:bold",
        "    classDef item fill:#111827,stroke:#38bdf8,color:#f8fafc",
        "    classDef done fill:#14532d,stroke:#4ade80,color:#f0fdf4,font-weight:bold",
        "    classDef current fill:#713f12,stroke:#facc15,color:#fefce8,font-weight:bold",
        "    classDef locked fill:#334155,stroke:#94a3b8,color:#e2e8f0",
        "",
    ]


def generate_mindmap(
    topic: str,
    prerequisites: Iterable[str] = (),
    subunits: Iterable[str] = (),
    completed: Iterable[str] = (),
) -> str:
    """Emit a renderer-safe, styled flowchart for a topic knowledge map.

    The public function keeps the historical name, but uses flowchart syntax
    rather than Mermaid mindmap syntax because flowcharts have broader renderer
    support and allow stable styling and status classes.
    """
    completed_set = {str(item) for item in completed}
    prerequisites = list(prerequisites or ())
    subunits = list(subunits or ())
    lines = _diagram_header("TB")
    lines.append(f'    ROOT["{_label(topic)}"]:::root')
    prior: str | None = None
    for group_index, (group_name, values) in enumerate(
        (("Prerequisites", prerequisites), ("Sub-units", subunits))
    ):
        if not values:
            continue
        group_id = _node_id("G", group_index)
        lines.append(f'    {group_id}["{group_name}"]:::group')
        lines.append(f"    ROOT --> {group_id}")
        for item_index, item in enumerate(values):
            item_id = f"{group_id}I{item_index}"
            status = "done" if str(item) in completed_set else "item"
            lines.append(f'    {item_id}["{_label(item)}"]:::{status}')
            lines.append(f"    {group_id} --> {item_id}")
            prior = item_id
    if prior is None:
        lines.append("    ROOT -.-> EMPTY[\"Add prerequisites or sub-units\"]:::item")
    return "\n".join(lines)


def build_scientist_card(name: str, years: str, discovery: str, significance: str, human_detail: str, quote: str = "") -> dict:
    return {
        "type": "scientist_card", "name": name, "years": years,
        "discovery": discovery, "significance": significance,
        "human_detail": human_detail, "quote": quote,
    }


def render_scientist_card(card: Mapping[str, str], mode: str = "text") -> str:
    if mode == "text":
        quote = f'\n  Quote: "{card["quote"]}"' if card.get("quote") else ""
        return (f"\n{'─' * 50}\n  CHARACTER CARD: {card['name']}\n"
                f"  {card['discovery']}\n{'─' * 50}\n"
                f"  Why it mattered: {card['significance']}\n"
                f"  The person behind it: {card['human_detail']}{quote}\n{'─' * 50}\n")
    quote_row = f"| **Quote** | {card['quote']} |\n" if card.get("quote") else ""
    return (f"## {card['name']} ({card['years']})\n\n| Field | Detail |\n|---|---|\n"
            f"| **Discovery** | {card['discovery']} |\n| **Why It Mattered** | {card['significance']} |\n"
            f"| **The Person** | {card['human_detail']} |\n{quote_row}")


def generate_skill_tree(chapters: list[dict], current_chapter_index: int = -1) -> str:
    """Emit a styled, deterministic progression flowchart."""
    lines = _diagram_header("LR")
    if not chapters:
        return "\n".join(lines + ['    EMPTY["No chapters yet"]:::locked'])
    for index, chapter in enumerate(chapters):
        completed = bool(chapter.get("completed"))
        if completed:
            prefix, style = "✓ ", "done"
        elif index == current_chapter_index:
            prefix, style = "◆ ", "current"
        else:
            prefix, style = "◇ ", "locked"
        title = _label(chapter.get("title", f"Chapter {index + 1}"))
        lines.append(f'    C{index}["{prefix}{title}"]:::{style}')
        if index:
            lines.append(f"    C{index - 1} --> C{index}")
    return "\n".join(lines)


if __name__ == "__main__":
    print("FHP:", fhp_mode_details())
    print(generate_mindmap("Rotational Mechanics", ["Linear Dynamics", "Torque"], ["Angular Velocity", "Moment of Inertia"], ["Angular Velocity"]))
    print(generate_skill_tree([
        {"title": "Linear Dynamics", "completed": True},
        {"title": "Rotational Mechanics", "completed": False},
    ], current_chapter_index=1))
