"""OpenMontage-inspired, repository-native production artifacts.

This module intentionally reimplements the artifact contract rather than
importing OpenMontage code. It keeps Master Pedagogy independent of AGPL code
while making each render auditable and provider-swappable.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from scripts.video_explainer import Storyboard


@dataclass
class ProviderDecision:
    provider: str
    priority: int
    available: bool
    selected: bool
    reason: str


@dataclass
class ProductionManifest:
    version: str
    pipeline: str
    render_runtime: str
    storyboard: dict[str, Any]
    provider_order: list[str]
    provider_decisions: list[ProviderDecision] = field(default_factory=list)
    required_tools: list[str] = field(default_factory=list)
    quality_gates: list[str] = field(default_factory=list)
    outputs: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def write(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return target


def make_manifest(storyboard: Storyboard, *, hosted_available: bool = False) -> ProductionManifest:
    decisions = [
        ProviderDecision("local-cinematic", 1, shutil.which("ffmpeg") is not None, False, "Deterministic physics-first local renderer."),
        ProviderDecision("hosted-provider", 2, hosted_available, False, "Optional external provider adapter."),
        ProviderDecision("static-svg-fallback", 3, True, False, "Always-available checked scene-card fallback."),
    ]
    return ProductionManifest(
        version="1.0",
        pipeline="master-pedagogy-cinematic-hybrid",
        render_runtime="python-ffmpeg",
        storyboard=storyboard.to_dict(),
        provider_order=[decision.provider for decision in decisions],
        provider_decisions=decisions,
        required_tools=["ffmpeg", "ffprobe"],
        quality_gates=[
            "storyboard validation",
            "16:9 dimensions",
            "15-45 second duration",
            "playable H.264 output",
            "representative-frame-inspection",
            "mastery check present",
        ],
    )


def select_provider(manifest: ProductionManifest, provider: str) -> ProductionManifest:
    for decision in manifest.provider_decisions:
        decision.selected = decision.provider == provider
    return manifest
