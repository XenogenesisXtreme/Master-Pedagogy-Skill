#!/usr/bin/env python3
"""MPS-owned Remotion adapter.

The adapter translates the pedagogical Storyboard into the small MPVE render
contract. It does not import or depend on OpenMontage source code.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from scripts.video_explainer import Storyboard, validate_storyboard


REMOTION_DIR = Path(__file__).resolve().parents[1] / "remotion"


def _scene_visual(storyboard: Storyboard, assets: list[str]) -> dict[str, str]:
    topic = storyboard.topic.lower()
    if "float" in topic or "buoy" in topic:
        return {"kind": "floatation"}
    if "roll" in topic or any("roll" in asset.lower() for asset in assets):
        return {"kind": "rolling"}
    return {"kind": "generic"}


def storyboard_props(storyboard: Storyboard, caption_words: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    errors = validate_storyboard(storyboard)
    if errors:
        raise ValueError("Cannot translate invalid storyboard: " + "; ".join(errors))
    cursor = 0
    scenes = []
    for scene in storyboard.scenes:
        scenes.append({
            "id": scene.id,
            "start_seconds": cursor,
            "duration_seconds": scene.duration,
            "label": scene.id.replace("-", " ").upper(),
            "title": scene.visual_goal,
            "explanation": scene.narration,
            "equation": scene.equations[0] if scene.equations else "",
            "equations": scene.equations,
            "visual": _scene_visual(storyboard, scene.assets),
        })
        cursor += scene.duration
    return {"topic": storyboard.topic, "profile": storyboard.exam_profile, "scenes": scenes, "captionWords": caption_words or []}


def render_remotion(storyboard: Storyboard, output_path: str | Path, *, caption_words: list[dict[str, Any]] | None = None, remotion_dir: str | Path = REMOTION_DIR) -> Path:
    root = Path(remotion_dir)
    output = Path(output_path).resolve()
    if shutil.which("node") is None or shutil.which("npx") is None:
        raise RuntimeError("Node.js and npx are required for the Remotion renderer")
    if not (root / "node_modules").exists():
        raise RuntimeError("Remotion dependencies are not installed; run npm install in remotion/")
    props_path = root / "props.mpve.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    props_path.write_text(json.dumps(storyboard_props(storyboard, caption_words), indent=2) + "\n", encoding="utf-8")
    try:
        duration = sum(scene.duration for scene in storyboard.scenes)
        frames = max(1, duration * 30)
        command = ["npx", "remotion", "render", "src/main.jsx", "MPVE", str(output), f"--props={props_path}", f"--frames=0-{frames - 1}", "--codec=h264", "--pixel-format=yuv420p", "--log=error"]
        subprocess.run(command, cwd=root, check=True)
        if not output.exists() or output.stat().st_size == 0:
            raise RuntimeError("Remotion completed without producing an MP4")
        return output
    finally:
        props_path.unlink(missing_ok=True)
