#!/usr/bin/env python3
"""Verified lesson-to-video planning pipeline for Master Pedagogy.

This module does not invent physics. It turns an already-authored lesson into a
validated storyboard and deterministic SVG scene cards that can be supplied to
an external video backend or used as a no-video fallback.
"""

from __future__ import annotations

import argparse
import html
import json
import sys
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.logic_engine import FHP_MODE, resolve_learning_mode

SUPPORTED_STYLES = ("whiteboard", "short", "cinematic", "fhp")
SUPPORTED_PROFILES = ("General / Conceptual Learning", "NEET", "JEE", "IOQM", "NSEJS")


@dataclass
class Scene:
    id: str
    duration: int
    narration: str
    visual_goal: str
    equations: list[str] = field(default_factory=list)
    assets: list[str] = field(default_factory=list)
    validation_checks: list[str] = field(default_factory=list)


@dataclass
class Storyboard:
    topic: str
    objective: str
    exam_profile: str
    mode: str
    style: str
    aspect_ratio: str
    narration_language: str
    scenes: list[Scene]
    mastery_check: str
    source_refs: list[str] = field(default_factory=list)
    derived: bool = False
    provider: str = "provider-neutral"

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


def _clean(value: str, fallback: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip() or fallback


def _split_narration(text: str, count: int) -> list[str]:
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", _clean(text, "Review the concept.")) if part.strip()]
    if not sentences:
        sentences = ["Review the concept."]
    buckets = [[] for _ in range(count)]
    for index, sentence in enumerate(sentences):
        buckets[min(index * count // len(sentences), count - 1)].append(sentence)
    return [" ".join(bucket) or sentences[min(index, len(sentences) - 1)] for index, bucket in enumerate(buckets)]


def _scene_count(style: str) -> int:
    return {"short": 3, "whiteboard": 5, "cinematic": 5, "fhp": 6}[style]


def build_storyboard(
    *,
    topic: str,
    objective: str,
    narration: str,
    mastery_check: str,
    exam_profile: str = "General / Conceptual Learning",
    mode: str = "standard",
    style: str = "whiteboard",
    equations: Iterable[str] = (),
    visual_assets: Iterable[str] = (),
    source_refs: Iterable[str] = (),
    derived: bool = False,
    duration: int | None = None,
) -> Storyboard:
    """Build a storyboard while keeping physics claims supplied by the lesson."""
    resolved_mode = resolve_learning_mode(mode)
    normalized_style = style.strip().lower()
    if normalized_style not in SUPPORTED_STYLES:
        raise ValueError(f"Unknown video style {style!r}; choose {', '.join(SUPPORTED_STYLES)}.")
    if exam_profile not in SUPPORTED_PROFILES:
        raise ValueError(f"Unknown exam profile {exam_profile!r}.")
    if resolved_mode == FHP_MODE and not derived:
        raise ValueError("FHP video generation requires derived=True after the written derivation is complete.")
    count = _scene_count(normalized_style)
    total = max(10, int(duration or (count * 6)))
    base = total // count
    remainder = total % count
    narrations = _split_narration(narration, count)
    equation_list = [str(item).strip() for item in equations if str(item).strip()]
    asset_list = [str(item).strip() for item in visual_assets if str(item).strip()]
    goals = [
        "State the observable phenomenon and learning objective.",
        "Show the definitions, variables, and assumptions.",
        "Animate or reveal the verified diagram and relationships.",
        "Walk through the result and check units, signs, and limits.",
        "Apply the result to a new case and leave the learner a mastery check.",
    ]
    if count == 3:
        goals = [goals[0], goals[2], goals[4]]
    elif normalized_style == "fhp":
        goals = [
            "Recall the observed phenomenon and the question.",
            "List knowns, unknowns, and minimum assumptions.",
            "Test a simple or limiting case.",
            "Reveal the model and derivation already completed in text.",
            "Run dimensional and consistency checks.",
            "Apply the result and state its limits.",
        ]
    scenes = []
    for index in range(count):
        scene_equations = equation_list if index in (2, 3) else []
        scenes.append(Scene(
            id=f"scene-{index + 1:02d}",
            duration=base + (1 if index < remainder else 0),
            narration=narrations[index],
            visual_goal=goals[index],
            equations=scene_equations,
            assets=asset_list if index in (1, 2, 3) else [],
            validation_checks=["all labels readable", "visual matches narration"] + (["FHP derivation already completed"] if resolved_mode == FHP_MODE else []),
        ))
    storyboard = Storyboard(
        topic=_clean(topic, "Untitled topic"), objective=_clean(objective, "Understand the topic."),
        exam_profile=exam_profile, mode=resolved_mode, style=normalized_style,
        aspect_ratio="16:9", narration_language="English", scenes=scenes,
        mastery_check=_clean(mastery_check, "Explain the result in your own words."),
        source_refs=list(source_refs), derived=derived,
    )
    errors = validate_storyboard(storyboard)
    if errors:
        raise ValueError("Invalid storyboard: " + "; ".join(errors))
    return storyboard


def validate_storyboard(storyboard: Storyboard) -> list[str]:
    """Return validation errors instead of hiding unsafe or incomplete output."""
    errors: list[str] = []
    if storyboard.aspect_ratio != "16:9":
        errors.append("video must use 16:9 landscape")
    if not storyboard.scenes:
        errors.append("storyboard must contain at least one scene")
    if sum(scene.duration for scene in storyboard.scenes) < 10:
        errors.append("video must be at least 10 seconds")
    if not storyboard.mastery_check.strip():
        errors.append("storyboard must end with a mastery check")
    if storyboard.mode == FHP_MODE and not storyboard.derived:
        errors.append("FHP storyboard requires completed written derivation")
    for scene in storyboard.scenes:
        if scene.duration <= 0:
            errors.append(f"{scene.id} has a non-positive duration")
        if not scene.narration.strip() or not scene.visual_goal.strip():
            errors.append(f"{scene.id} needs narration and a visual goal")
    return errors


def render_static_fallback(storyboard: Storyboard, output_dir: str | Path) -> list[Path]:
    """Render accessible neon SVG scene cards when no video backend is available."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for scene in storyboard.scenes:
        title = html.escape(storyboard.topic)
        goal = html.escape(scene.visual_goal)
        narration = html.escape(scene.narration)
        equations = "<br/>".join(html.escape(item) for item in scene.equations) or "Visual explanation"
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 900">
<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#070b1f"/><stop offset="1" stop-color="#241047"/></linearGradient></defs>
<rect width="1600" height="900" fill="url(#bg)"/><path d="M80 760 C420 580 650 820 980 560 S1350 450 1540 220" fill="none" stroke="#22d3ee" stroke-width="6" opacity=".65"/>
<text x="100" y="130" fill="#67e8f9" font-family="Inter,Segoe UI,sans-serif" font-size="30">MASTER PEDAGOGY • {html.escape(storyboard.style.upper())} • {scene.id}</text>
<text x="100" y="220" fill="#f8fafc" font-family="Inter,Segoe UI,sans-serif" font-weight="700" font-size="66">{title}</text>
<text x="100" y="330" fill="#c4b5fd" font-family="Inter,Segoe UI,sans-serif" font-size="34">{goal}</text>
<text x="100" y="500" fill="#facc15" font-family="Inter,Segoe UI,sans-serif" font-size="42">{equations}</text>
<foreignObject x="100" y="610" width="1400" height="160"><div xmlns="http://www.w3.org/1999/xhtml" style="color:#e2e8f0;font:28px Inter,Segoe UI,sans-serif;line-height:1.35">{narration}</div></foreignObject>
</svg>'''
        path = output / f"{scene.id}.svg"
        path.write_text(svg, encoding="utf-8")
        paths.append(path)
    manifest = output / "manifest.json"
    manifest.write_text(json.dumps({"storyboard": storyboard.to_dict(), "files": [p.name for p in paths]}, indent=2, ensure_ascii=False), encoding="utf-8")
    paths.append(manifest)
    return paths


def _demo() -> Storyboard:
    return build_storyboard(
        topic="Newton's Second Law", objective="Relate net force, mass, and acceleration.",
        narration="Observe the motion. Ask what determines the acceleration. Define the variables and reveal the verified relationship F equals m times a. Check units and apply it to a new case.",
        mastery_check="Predict how acceleration changes when the net force doubles.",
        exam_profile="JEE", mode="standard", style="whiteboard", equations=["F = ma"], derived=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=None, help="Write a demo storyboard and static fallback assets here.")
    args = parser.parse_args()
    storyboard = _demo()
    print(storyboard.to_json())
    if args.output:
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / "storyboard.json").write_text(storyboard.to_json() + "\n", encoding="utf-8")
        for path in render_static_fallback(storyboard, args.output / "scenes"):
            print(path)


if __name__ == "__main__":
    main()
