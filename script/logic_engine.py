#!/usr/bin/env python3
"""Backward-compatible import/CLI shim.

The canonical implementation lives in ``scripts.logic_engine``. Keeping this
shim prevents older consumers that import ``script.logic_engine`` from missing
FHP mode or receiving the old, unstyled diagram output.
"""

from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from scripts.logic_engine import *  # noqa: F401,F403
from scripts.logic_engine import generate_mindmap, resolve_learning_mode


def first_principles_logic(formula_or_concept, hobby=None):
    """Legacy API retained for callers of the original singular path."""
    truths = {
        "F=ma": "Push strength depends on mass and desired acceleration.",
        "E=mc^2": "Energy and matter are two forms of the same thing.",
        "V=IR": "Voltage equals current multiplied by resistance.",
        "PV=nRT": "Pressure and volume depend on the gas amount and temperature.",
        "a^2 + b^2 = c^2": "The square of the hypotenuse equals the sum of the other squares.",
        "Torque": "Turning effect depends on force and distance from the pivot.",
    }
    result = truths.get(formula_or_concept, f"Core Truth for '{formula_or_concept}': derive it from physical constraints.")
    if hobby:
        result += f" Analogy seed: {build_analogy_seed(hobby)['traits'][0]}."
    return result


def generate_mind_map(topic, sections):
    """Legacy API adapter using the canonical renderer-safe diagram generator."""
    prerequisites = sections.get("Prerequisites", []) if isinstance(sections, dict) else []
    subunits = [unit for name, values in sections.items() if name != "Prerequisites" for unit in values]
    return generate_mindmap(topic, prerequisites, subunits)


def celebration_function():
    return "MASTERY ACHIEVED — keep going."


def adapt_narrative(topic, narrative_type):
    return {
        "title": narrative_type,
        "hook": f"A challenge involving {topic} blocks the next stage.",
        "teaching_method": f"Use {topic} as the system to inspect, test, and improve.",
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 script/logic_engine.py <first_principles|mind_map|fhp> ...")
        raise SystemExit(1)
    action = sys.argv[1]
    if action == "first_principles":
        print(first_principles_logic(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None))
    elif action == "mind_map":
        data = json.loads(sys.argv[2])
        print(generate_mind_map(data["topic"], data["sections"]))
    elif action == "fhp":
        print(fhp_mode_details())
    else:
        raise SystemExit(f"Unknown action: {action}")
