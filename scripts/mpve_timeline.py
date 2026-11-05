#!/usr/bin/env python3
"""Independent, render-neutral MPVE timeline contract.

This is an MPS-owned IR: pedagogy remains in Storyboard while render concerns
are represented as optional typed clips and timed overlays.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class TimelineClip:
    clip_id: str
    start_seconds: float
    duration_seconds: float
    visual_kind: str = "text"
    props: dict[str, Any] = field(default_factory=dict)
    transition_in: str = "cut"
    transition_out: str = "cut"
    transition_seconds: float = 0.0
    layer: int = 0

    def end_seconds(self) -> float:
        return self.start_seconds + self.duration_seconds


@dataclass
class TimedOverlay:
    overlay_id: str
    start_seconds: float
    duration_seconds: float
    text: str
    layer: int = 100


@dataclass
class Timeline:
    fps: int = 24
    width: int = 1280
    height: int = 720
    clips: list[TimelineClip] = field(default_factory=list)
    overlays: list[TimedOverlay] = field(default_factory=list)

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.fps <= 0:
            errors.append("fps must be positive")
        if self.width <= 0 or self.height <= 0:
            errors.append("canvas dimensions must be positive")
        seen: set[str] = set()
        for clip in self.clips:
            if not clip.clip_id or clip.clip_id in seen:
                errors.append(f"duplicate or empty clip id: {clip.clip_id!r}")
            seen.add(clip.clip_id)
            if clip.start_seconds < 0 or clip.duration_seconds <= 0:
                errors.append(f"{clip.clip_id} must have non-negative start and positive duration")
            if clip.transition_seconds < 0:
                errors.append(f"{clip.clip_id} transition_seconds must be non-negative")
            if clip.transition_seconds > clip.duration_seconds / 2:
                errors.append(f"{clip.clip_id} transition exceeds half of local duration")
            if clip.visual_kind not in {"text", "equation", "diagram", "media", "metric", "comparison"}:
                errors.append(f"unsupported visual_kind: {clip.visual_kind}")
        for overlay in self.overlays:
            if overlay.start_seconds < 0 or overlay.duration_seconds <= 0 or not overlay.text.strip():
                errors.append(f"invalid overlay: {overlay.overlay_id}")
        return errors

    def frame(self, seconds: float) -> int:
        return max(0, round(seconds * self.fps))

    def duration_seconds(self, tail_seconds: float = 0.0) -> float:
        end = max((clip.end_seconds() for clip in self.clips), default=0.0)
        end = max(end, max((o.start_seconds + o.duration_seconds for o in self.overlays), default=0.0))
        return end + max(0.0, tail_seconds)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def transition_window(clip: TimelineClip, fps: int) -> dict[str, int]:
    """Return local transition frames; cut/none never fade."""
    duration = max(1, round(clip.duration_seconds * fps))
    token_in = clip.transition_in.strip().lower()
    token_out = clip.transition_out.strip().lower()
    hard = {"", "cut", "none"}
    frames = max(1, round(clip.transition_seconds * fps)) if clip.transition_seconds > 0 else 0
    frames = min(frames, max(0, duration // 2))
    return {
        "duration_frames": duration,
        "fade_in_frames": 0 if token_in in hard else frames,
        "fade_out_frames": 0 if token_out in hard else frames,
    }
