#!/usr/bin/env python3
"""Provider-neutral narration timing and audio-mux helpers for MPVE."""
from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from scripts.video_explainer import Storyboard


@dataclass(frozen=True)
class NarrationTurn:
    text: str
    start_seconds: int
    end_seconds: int
    style: str = "clear, educational, measured"


def build_narration_plan(storyboard: Storyboard) -> list[NarrationTurn]:
    """Split a storyboard into scene-aligned TTS turns.

    A host can map each turn to an ElevenLabs request or concatenate turns using
    the same voice. Timing follows the requested storyboard duration instead of
    assuming a fixed short clip.
    """
    turns: list[NarrationTurn] = []
    cursor = 0
    for scene in storyboard.scenes:
        turns.append(NarrationTurn(scene.narration, cursor, cursor + scene.duration))
        cursor += scene.duration
    return turns


def mix_narration(video_path: str | Path, audio_path: str | Path, output_path: str | Path, duration_seconds: float | None = None) -> Path:
    """Replace the existing audio track with narration and pad/trim to video length."""
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg is required to mix narration")
    video = Path(video_path).resolve()
    audio = Path(audio_path).resolve()
    output = Path(output_path).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    duration_filter = f",atrim=duration={duration_seconds}" if duration_seconds else ""
    command = [
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-i", str(audio),
        "-filter_complex", f"[1:a]apad{duration_filter},asetpts=N/SR/TB[a]",
        "-map", "0:v:0", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(output),
    ]
    subprocess.run(command, check=True)
    if not output.exists() or output.stat().st_size == 0:
        raise RuntimeError("narration mix completed without producing an MP4")
    return output
