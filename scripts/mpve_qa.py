#!/usr/bin/env python3
"""Independent post-render technical and representative-frame QA for MPVE."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=False, capture_output=True, text=True)


def inspect_media(path: str | Path, expected_duration: int | None = None, expected_width: int = 1280, expected_height: int = 720, expected_fps: int = 24, sample_dir: str | Path | None = None) -> dict[str, Any]:
    output = Path(path)
    errors: list[str] = []
    warnings: list[str] = []
    probe: dict[str, Any] = {}
    if not output.exists() or output.stat().st_size == 0:
        errors.append("output file is missing or empty")
    elif shutil.which("ffprobe") is None:
        errors.append("ffprobe is required for media QA")
    else:
        result = _run(["ffprobe", "-v", "error", "-show_entries", "format=duration,size:stream=index,codec_type,codec_name,width,height,r_frame_rate,channels", "-of", "json", str(output)])
        if result.returncode != 0:
            errors.append("ffprobe could not decode the output")
            warnings.append(result.stderr.strip()[:500])
        else:
            try:
                probe = json.loads(result.stdout)
            except json.JSONDecodeError:
                errors.append("ffprobe returned invalid JSON")
    streams = probe.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    if not video:
        errors.append("no video stream found")
    else:
        if video.get("codec_name") not in {"h264", "hevc", "vp9", "av1"}:
            warnings.append(f"unusual video codec: {video.get('codec_name')}")
        if expected_width and video.get("width") != expected_width:
            errors.append(f"width {video.get('width')} != expected {expected_width}")
        if expected_height and video.get("height") != expected_height:
            errors.append(f"height {video.get('height')} != expected {expected_height}")
        rate = str(video.get("r_frame_rate", ""))
        if expected_fps and rate and rate.split("/")[0].isdigit() and rate.split("/")[1].isdigit():
            numerator, denominator = map(int, rate.split("/"))
            if denominator and abs(numerator / denominator - expected_fps) > 0.5:
                warnings.append(f"frame rate {rate} differs from expected {expected_fps}")
    duration = float(probe.get("format", {}).get("duration", 0) or 0)
    if duration <= 0:
        errors.append("duration is missing or non-positive")
    if expected_duration is not None and abs(duration - expected_duration) > 1.0:
        errors.append(f"duration {duration:.3f}s differs from expected {expected_duration}s")
    samples: list[str] = []
    sample_root = Path(sample_dir) if sample_dir else output.parent / "qa-frames"
    if not errors and shutil.which("ffmpeg"):
        sample_root.mkdir(parents=True, exist_ok=True)
        for label, fraction in (("opening", 0.05), ("middle", 0.5), ("late", 0.8), ("ending", 0.95)):
            frame = sample_root / f"{label}.jpg"
            seek = max(0.0, duration * fraction)
            result = _run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{seek:.3f}", "-i", str(output), "-frames:v", "1", str(frame)])
            if result.returncode == 0 and frame.exists() and frame.stat().st_size > 0:
                samples.append(str(frame))
            else:
                errors.append(f"could not extract {label} QA frame")
    if len(samples) < 4 and not errors:
        errors.append("fewer than four representative frames were produced")
    return {
        "status": "pass" if not errors else "fail",
        "output_path": str(output),
        "file_size_bytes": output.stat().st_size if output.exists() else 0,
        "probe": probe,
        "duration_seconds": duration,
        "video_stream": video,
        "audio_streams": [s for s in streams if s.get("codec_type") == "audio"],
        "representative_frames": samples,
        "errors": errors,
        "warnings": warnings,
        "checks": ["file exists", "ffprobe decode", "video stream", "dimensions", "duration", "four representative frames"],
    }


def write_final_review(qa: dict[str, Any], path: str | Path, provider: str, requested_duration: int, requested_aspect: str) -> Path:
    review = {
        "version": "1.0",
        "status": "pass" if qa["status"] == "pass" else "fail",
        "provider": provider,
        "requested": {"duration_seconds": requested_duration, "aspect_ratio": requested_aspect},
        "technical": qa,
        "visual": {"status": "sampled", "representative_frames": qa.get("representative_frames", [])},
        "audio": {"status": "present" if qa.get("audio_streams") else "silent", "stream_count": len(qa.get("audio_streams", []))},
        "recommended_action": "present" if qa["status"] == "pass" else "re-render",
    }
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(review, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return destination
