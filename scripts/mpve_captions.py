#!/usr/bin/env python3
"""Provider-neutral timed-caption utilities for MPVE."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class CaptionWord:
    text: str
    start_ms: int
    end_ms: int
    page_break_after: bool = False

    def validate(self) -> str | None:
        if not self.text.strip():
            return "caption text must not be empty"
        if self.start_ms < 0 or self.end_ms <= self.start_ms:
            return "caption timestamps must be non-negative and end after start"
        return None


def validate_words(words: Iterable[CaptionWord]) -> list[str]:
    errors: list[str] = []
    previous = -1
    for index, word in enumerate(words):
        error = word.validate()
        if error:
            errors.append(f"word {index}: {error}")
        if word.start_ms < previous:
            errors.append(f"word {index}: start time moves backwards")
        previous = max(previous, word.start_ms)
    return errors


def _stamp(ms: int, separator: str = ",") -> str:
    ms = max(0, int(ms))
    hours, ms = divmod(ms, 3_600_000)
    minutes, ms = divmod(ms, 60_000)
    seconds, millis = divmod(ms, 1_000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}{separator}{millis:03d}"


def _cues(words: list[CaptionWord], words_per_cue: int = 6) -> list[tuple[int, int, str]]:
    if words_per_cue <= 0:
        raise ValueError("words_per_cue must be positive")
    cues: list[tuple[int, int, str]] = []
    bucket: list[CaptionWord] = []
    for word in words:
        bucket.append(word)
        if len(bucket) >= words_per_cue or word.page_break_after:
            cues.append((bucket[0].start_ms, bucket[-1].end_ms, " ".join(w.text for w in bucket)))
            bucket = []
    if bucket:
        cues.append((bucket[0].start_ms, bucket[-1].end_ms, " ".join(w.text for w in bucket)))
    return cues


def write_sidecars(words: Iterable[CaptionWord], output_dir: str | Path, words_per_cue: int = 6, direction: str = "auto") -> dict:
    normalized = list(words)
    errors = validate_words(normalized)
    if errors:
        raise ValueError("; ".join(errors))
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    cues = _cues(normalized, words_per_cue)
    srt_lines: list[str] = []
    vtt_lines = ["WEBVTT", ""]
    for index, (start, end, text) in enumerate(cues, 1):
        srt_lines.extend([str(index), f"{_stamp(start)} --> {_stamp(end)}", text, ""])
        vtt_lines.extend([f"{_stamp(start, '.')} --> {_stamp(end, '.')}", text, ""])
    srt = output / "captions.srt"
    vtt = output / "captions.vtt"
    json_path = output / "captions.json"
    srt.write_text("\n".join(srt_lines), encoding="utf-8")
    vtt.write_text("\n".join(vtt_lines), encoding="utf-8")
    json_path.write_text(json.dumps({"version": "1.0", "direction": direction, "words": [asdict(w) for w in normalized], "cues": len(cues)}, indent=2) + "\n", encoding="utf-8")
    return {"srt": str(srt), "vtt": str(vtt), "json": str(json_path), "cue_count": len(cues), "direction": direction}
