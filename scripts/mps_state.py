#!/usr/bin/env python3
"""Small durable learner-session store for local MPS orchestration."""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from threading import RLock
from typing import Any


@dataclass
class LearnerSessionState:
    session_id: str = field(default_factory=lambda: f"session-{uuid.uuid4().hex[:12]}")
    current_subject: str | None = None
    current_chapter: str | None = None
    current_subtopic: str | None = None
    exam_profile: str = "General / Conceptual Learning"
    learning_mode: str = "standard"
    prerequisite_confidence: dict[str, str] = field(default_factory=dict)
    active_route: str | None = None
    misconceptions: dict[str, dict[str, Any]] = field(default_factory=dict)
    mastery: dict[str, dict[str, Any]] = field(default_factory=dict)
    consecutive_incorrect: dict[str, int] = field(default_factory=dict)
    pending_mastery_question: str | None = None
    video_jobs: dict[str, dict[str, Any]] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    updated_at: float = field(default_factory=time.time)

    def record_event(self, event: str, **data: Any) -> None:
        self.events.append({"event": event, "at": time.time(), **data})
        self.events = self.events[-200:]
        self.updated_at = time.time()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LearnerSessionState":
        known = {key: value for key, value in data.items() if key in cls.__dataclass_fields__}
        return cls(**known)


class LearnerStateStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()

    def load(self) -> LearnerSessionState:
        with self._lock:
            if not self.path.exists():
                return LearnerSessionState()
            return LearnerSessionState.from_dict(json.loads(self.path.read_text(encoding="utf-8")))

    def save(self, state: LearnerSessionState) -> LearnerSessionState:
        with self._lock:
            state.updated_at = time.time()
            self.path.write_text(json.dumps(state.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            return state

    def update(self, **changes: Any) -> LearnerSessionState:
        state = self.load()
        for key, value in changes.items():
            if not hasattr(state, key):
                raise KeyError(key)
            setattr(state, key, value)
        return self.save(state)
