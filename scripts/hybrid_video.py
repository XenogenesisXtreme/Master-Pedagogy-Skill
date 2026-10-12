#!/usr/bin/env python3
"""Hybrid local-first video rendering for Master Pedagogy explainers.

Provider order:
1. Local deterministic cinematic renderer (Pillow + FFmpeg).
2. An optional caller-supplied hosted renderer.
3. Checked SVG scene-card fallback.

The local path is intentionally physics-first rather than generative: equations,
labels, vectors, and object motion are drawn from the validated storyboard so
educational visuals remain stable when hosted AI credits are unavailable.
"""

from __future__ import annotations

import json
import math
import shutil
import subprocess
import tempfile
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from PIL import Image, ImageDraw, ImageFont

from scripts.video_explainer import Storyboard, render_static_fallback, validate_storyboard

WIDTH, HEIGHT = 1280, 720
DEFAULT_FPS = 24


@dataclass
class RenderResult:
    provider: str
    output_path: Path | None
    duration_seconds: int
    aspect_ratio: str
    audio: bool
    fallback_assets: list[Path]
    errors: list[str]

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "output_path": str(self.output_path) if self.output_path else None,
            "duration_seconds": self.duration_seconds,
            "aspect_ratio": self.aspect_ratio,
            "audio": self.audio,
            "fallback_assets": [str(path) for path in self.fallback_assets],
            "errors": self.errors,
        }


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    )
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def _gradient(width: int, height: int, top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    image = Image.new("RGB", (width, height))
    pixels = image.load()
    for y in range(height):
        ratio = y / max(1, height - 1)
        color = tuple(int(top[index] * (1 - ratio) + bottom[index] * ratio) for index in range(3))
        for x in range(width):
            pixels[x, y] = color
    return image


def _wrapped(draw: ImageDraw.ImageDraw, text: str, width: int, font: ImageFont.ImageFont) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=font) <= width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _arrow(draw: ImageDraw.ImageDraw, start: tuple[float, float], end: tuple[float, float], color: str, width: int = 5) -> None:
    draw.line((start, end), fill=color, width=width)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    size = 16
    left = (end[0] - size * math.cos(angle - math.pi / 6), end[1] - size * math.sin(angle - math.pi / 6))
    right = (end[0] - size * math.cos(angle + math.pi / 6), end[1] - size * math.sin(angle + math.pi / 6))
    draw.polygon([end, left, right], fill=color)


def _draw_rolling_scene(draw: ImageDraw.ImageDraw, progress: float, topic: str) -> None:
    """Draw a constrained rolling-body animation when the lesson is about rolling."""
    x0, y0 = 140, 560
    x1, y1 = 690, 420
    x = x0 + (x1 - x0) * progress
    y = y0 + (y1 - y0) * progress
    radius = 58
    # incline and contact shadow
    draw.line((x0 - 80, y0 + 65, x1 + 100, y1 + 65), fill="#334155", width=5)
    draw.line((x0, y0, x1, y1), fill="#67e8f9", width=7)
    draw.ellipse((x - radius, y - radius + 12, x + radius, y + radius + 12), fill="#020617")
    # solid cylinder
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill="#163451", outline="#f472b6", width=6)
    draw.line((x, y - radius + 8, x, y + radius - 8), fill="#facc15", width=5)
    angle = progress * math.tau * 2
    spoke_x = x + math.cos(angle) * radius * 0.78
    spoke_y = y + math.sin(angle) * radius * 0.78
    draw.line((x, y, spoke_x, spoke_y), fill="#facc15", width=5)
    _arrow(draw, (x - 150, y + 72), (x - 25, y + 72), "#22d3ee", 6)
    draw.text((x - 205, y + 85), "v", fill="#22d3ee", font=_font(28, True))
    draw.arc((x - 42, y - 42, x + 42, y + 42), int(math.degrees(angle)), int(math.degrees(angle) + 100), fill="#a78bfa", width=5)
    draw.text((x + 70, y - 42), "ω", fill="#a78bfa", font=_font(32, True))
    label_x = max(80, min(int(x - 120), 660))
    draw.text((label_x, y - radius - 62), "solid cylinder", fill="#f8fafc", font=_font(25))
    draw.text((label_x, y - radius - 30), "v = ωR", fill="#facc15", font=_font(28, True))


def _draw_generic_scene(draw: ImageDraw.ImageDraw, progress: float) -> None:
    """Draw a cinematic abstract motion layer for non-rolling storyboards."""
    cx = 260 + int(progress * 650)
    cy = 410 - int(progress * 130)
    draw.ellipse((cx - 70, cy - 70, cx + 70, cy + 70), outline="#22d3ee", width=7, fill="#132a45")
    draw.ellipse((cx - 22, cy - 22, cx + 22, cy + 22), fill="#facc15")
    _arrow(draw, (cx - 150, cy + 85), (cx - 25, cy + 85), "#22d3ee", 6)
    draw.text((cx + 92, cy - 20), "verified motion", fill="#f8fafc", font=_font(28))


def _draw_frame(storyboard: Storyboard, frame_index: int, total_frames: int) -> Image.Image:
    image = _gradient(WIDTH, HEIGHT, (5, 12, 30), (35, 16, 70))
    draw = ImageDraw.Draw(image)
    global_progress = frame_index / max(1, total_frames - 1)
    scene_count = len(storyboard.scenes)
    scene_index = min(scene_count - 1, int(global_progress * scene_count))
    scene = storyboard.scenes[scene_index]
    local_progress = (global_progress * scene_count) - scene_index

    draw.text((54, 36), f"MASTER PEDAGOGY • CINEMATIC LOCAL • {scene.id}", fill="#67e8f9", font=_font(22, True))
    draw.text((54, 78), storyboard.topic, fill="#f8fafc", font=_font(42, True))
    draw.text((54, 132), storyboard.exam_profile, fill="#c4b5fd", font=_font(23))

    panel_x, panel_y, panel_w, panel_h = 790, 190, 440, 390
    draw.rounded_rectangle((panel_x, panel_y, panel_x + panel_w, panel_y + panel_h), radius=24, fill="#0b1730", outline="#a78bfa", width=3)
    if "rolling" in storyboard.topic.lower() or any("rolling" in asset.lower() for asset in scene.assets):
        _draw_rolling_scene(draw, local_progress, storyboard.topic)
    else:
        _draw_generic_scene(draw, local_progress)

    draw.rounded_rectangle((panel_x, panel_y, panel_x + panel_w, panel_y + panel_h), radius=24, fill="#0b1730", outline="#a78bfa", width=3)
    goal_font = _font(23, True)
    body_font = _font(21)
    goal_lines = _wrapped(draw, scene.visual_goal, panel_w - 56, goal_font)
    for line_index, line in enumerate(goal_lines[:2]):
        draw.text((panel_x + 28, panel_y + 26 + line_index * 29), line, fill="#c4b5fd", font=goal_font)
    y = panel_y + 88 + max(0, len(goal_lines[:2]) - 1) * 29
    for line in _wrapped(draw, scene.narration, panel_w - 56, body_font)[:7]:
        draw.text((panel_x + 28, y), line, fill="#e2e8f0", font=body_font)
        y += 31
    if scene.equations:
        y += 12
        for equation in scene.equations[:2]:
            draw.text((panel_x + 28, y), equation, fill="#facc15", font=_font(28, True))
            y += 38

    draw.text((54, HEIGHT - 52), "16:9 • deterministic physics visuals • local-first hybrid pipeline", fill="#94a3b8", font=_font(18))
    return image


def render_local_cinematic(storyboard: Storyboard, output_path: str | Path, work_dir: str | Path | None = None, fps: int = DEFAULT_FPS) -> RenderResult:
    """Render a playable local MP4 from a validated Cinematic storyboard."""
    errors = validate_storyboard(storyboard)
    if errors:
        raise ValueError("Cannot render invalid storyboard: " + "; ".join(errors))
    if storyboard.style != "cinematic":
        raise ValueError("The local cinematic renderer requires style='cinematic'.")
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg is required for the local renderer.")
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    owned_temp = work_dir is None
    temp_context = tempfile.TemporaryDirectory(prefix="mps-local-video-") if owned_temp else None
    frames_dir = Path(temp_context.name if temp_context else work_dir)
    frames_dir.mkdir(parents=True, exist_ok=True)
    try:
        total_seconds = sum(scene.duration for scene in storyboard.scenes)
        total_frames = total_seconds * fps
        for frame_index in range(total_frames):
            frame = _draw_frame(storyboard, frame_index, total_frames)
            frame.save(frames_dir / f"frame-{frame_index:06d}.png")
        command = [
            "ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps),
            "-i", str(frames_dir / "frame-%06d.png"), "-c:v", "libx264",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output),
        ]
        subprocess.run(command, check=True)
        return RenderResult("local-cinematic", output, total_seconds, storyboard.aspect_ratio, False, [], [])
    finally:
        if temp_context:
            temp_context.cleanup()


def render_hybrid(
    storyboard: Storyboard,
    output_path: str | Path,
    *,
    hosted_renderer: Callable[[Storyboard, Path], Path] | None = None,
    fallback_dir: str | Path | None = None,
) -> RenderResult:
    """Try local rendering, then an optional hosted adapter, then SVG fallback."""
    errors: list[str] = []
    output = Path(output_path)
    try:
        return render_local_cinematic(storyboard, output)
    except Exception as exc:  # provider fallback is intentional and reported
        errors.append(f"local-cinematic: {exc}")
    if hosted_renderer:
        try:
            hosted_output = Path(hosted_renderer(storyboard, output))
            return RenderResult("hosted-provider", hosted_output, sum(scene.duration for scene in storyboard.scenes), storyboard.aspect_ratio, True, [], errors)
        except Exception as exc:
            errors.append(f"hosted-provider: {exc}")
    fallback_path = Path(fallback_dir or output.parent / f"{output.stem}-fallback")
    assets = render_static_fallback(storyboard, fallback_path)
    return RenderResult("static-svg-fallback", None, sum(scene.duration for scene in storyboard.scenes), storyboard.aspect_ratio, False, assets, errors)


def render_result_manifest(result: RenderResult, path: str | Path) -> Path:
    manifest = Path(path)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(result.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest
