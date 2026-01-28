from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Any


def _pos_key(string_index: int, fret: int) -> str:
    return f"{string_index},{fret}"


def _ensure_bucket(d: Dict[str, Dict[str, int]], key: str) -> Dict[str, int]:
    bucket = d.get(key)
    if bucket is None:
        bucket = {"attempts": 0, "correct": 0}
        d[key] = bucket
    else:
        bucket.setdefault("attempts", 0)
        bucket.setdefault("correct", 0)
    return bucket


@dataclass
class Stats:
    total_attempts: int = 0
    total_correct: int = 0

    # required by tests
    by_mode: Dict[str, Dict[str, int]] = field(default_factory=dict)

    # used by CLI + GUI
    by_note: Dict[str, Dict[str, int]] = field(default_factory=dict)
    by_position: Dict[str, Dict[str, int]] = field(default_factory=dict)

    # NEW: metadata for instrument/tuning separation
    meta: Dict[str, Any] = field(default_factory=dict)

    def _record_mode(self, mode: str, correct: bool) -> None:
        mode = (mode or "A").strip().upper()
        bucket = _ensure_bucket(self.by_mode, mode)
        bucket["attempts"] += 1
        if correct:
            bucket["correct"] += 1

    def _record_note(self, note_name: str, correct: bool) -> None:
        note_name = str(note_name)
        bucket = _ensure_bucket(self.by_note, note_name)
        bucket["attempts"] += 1
        if correct:
            bucket["correct"] += 1

    def record_attempt(
        self,
        *,
        mode: str,
        correct: bool,
        note_name: str,
        string_index: Optional[int] = None,
    ) -> None:
        # Defensive: ignore obviously invalid indices (don't crash)
        if string_index is not None and int(string_index) < 0:
            return

        self.total_attempts += 1
        if correct:
            self.total_correct += 1

        self._record_mode(mode, correct)
        self._record_note(note_name, correct)

    def record_attempt_mode_b(self, *, correct: bool, note_name: str) -> None:
        self.record_attempt(mode="B", correct=correct, note_name=note_name, string_index=None)

    def record_position_attempt(
        self,
        *,
        correct: bool,
        note_name: str,
        string_index: int,
        fret: int,
        mode: str = "A",
    ) -> None:
        string_index = int(string_index)
        fret = int(fret)
        if string_index < 0 or fret < 0:
            return

        self.record_attempt(mode=mode, correct=correct, note_name=note_name, string_index=string_index)

        key = _pos_key(string_index, fret)
        bucket = _ensure_bucket(self.by_position, key)
        bucket["attempts"] += 1
        if correct:
            bucket["correct"] += 1


def load_stats(path: str) -> Stats:
    import json

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        stats = Stats(
            total_attempts=int(raw.get("total_attempts", 0)),
            total_correct=int(raw.get("total_correct", 0)),
            by_mode=dict(raw.get("by_mode", {})),
            by_note=dict(raw.get("by_note", {})),
            by_position=dict(raw.get("by_position", {})),
            meta=dict(raw.get("meta", {})),
        )

        _ensure_bucket(stats.by_mode, "A")
        _ensure_bucket(stats.by_mode, "B")
        return stats

    except FileNotFoundError:
        s = Stats()
        _ensure_bucket(s.by_mode, "A")
        _ensure_bucket(s.by_mode, "B")
        return s


def save_stats(path: str, stats: Stats) -> None:
    import json

    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "total_attempts": int(stats.total_attempts),
                "total_correct": int(stats.total_correct),
                "by_mode": stats.by_mode,
                "by_note": stats.by_note,
                "by_position": stats.by_position,
                "meta": stats.meta,
            },
            f,
            indent=2,
        )
