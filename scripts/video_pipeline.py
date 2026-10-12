#!/usr/bin/env python3
"""Run the local-first hybrid video pipeline with a rolling-bodies demo."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.hybrid_video import render_hybrid, render_result_manifest
from scripts.video_explainer import build_storyboard


def rolling_bodies_storyboard(duration: int, learner_interest: str | None, analogy_consent: bool):
    return build_storyboard(
        topic="Rolling Bodies",
        objective="Explain how translational and rotational kinetic energy determine the speed of a rolling body.",
        narration=(
            "A rolling body has two kinds of motion: translation of its center and rotation about its center. "
            "Like a game object whose forward movement and spin are coupled, the no-slip condition gives v equals omega R. "
            "Energy is shared between translation and rotation. The total is one-half M v squared plus one-half I omega squared. "
            "The solid cylinder reaches the bottom before the ring because its moment of inertia is smaller."
        ),
        mastery_check="Which reaches the bottom first, a solid cylinder or a ring, and why?",
        equations=["v = ωR", "K = ½Mv² + ½Iω²"],
        learner_interest=learner_interest,
        analogy_consent=analogy_consent,
        duration=duration,
        derived=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("build/video-demo/rolling-bodies-hybrid.mp4"))
    parser.add_argument("--duration", type=int, default=30, help="Explainer duration from 15 to 45 seconds.")
    parser.add_argument("--learner-interest", default="coding and game development")
    parser.add_argument("--analogy-consent", action="store_true", default=True)
    args = parser.parse_args()

    storyboard = rolling_bodies_storyboard(args.duration, args.learner_interest, args.analogy_consent)
    result = render_hybrid(storyboard, args.output)
    manifest = render_result_manifest(result, args.output.with_suffix(".manifest.json"))
    print(json.dumps({"storyboard": storyboard.to_dict(), "render": result.to_dict(), "manifest": str(manifest)}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
