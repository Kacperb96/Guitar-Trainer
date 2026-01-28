from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Any
import json
import logging
import os
from pathlib import Path
import tempfile

from guitar_trainer.core.position_key import pos_key


logger = logging.getLogger("guitar_trainer.stats")


def _ensure_bucket(d: Dict[str, Dict[str, int]], key: str) -> Dict[str, int]:
    bucket = d.get(key)
    if bucket is None:
        bucket = {"attempts": 0, "correct": 0}
        d[key] = bucket
    else:
        bucket.setdefault("attempts", 0)
        bucket.setdefault("correct", 0)
    return bucket


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return int(default)


def _atomic_write_json(path: str, data: dict) -> None:
    """Write JSON atomically (temp file + replace)."""
    p = Path(path)
    parent = p.parent

    # Ensure directory exists (if path contains directories).
    if str(parent) not in ("", "."):
        parent.mkdir(parents=True, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(prefix=p.name + ".", suffix=".tmp", dir=str(parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, str(p))
    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass


@dataclass
class Stats:
    total_attempts: int = 0
    total_correct: int = 0

    by_mode: Dict[str, Dict[str, int]] = field(default_factory=dict)
    by_note: Dict[str, Dict[str, int]] = field(default_factory=dict)
    by_position: Dict[str, Dict[str, int]] = field(default_factory=dict)

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
        # Defensive: ignore obviously invalid indices (do not crash).
        if string_index is not None and _safe_int(string_index, -1) < 0:
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
        string_index = _safe_int(string_index, -1)
        fret = _safe_int(fret, -1)
        if string_index < 0 or fret < 0:
            return

        self.record_attempt(mode=mode, correct=correct, note_name=note_name, string_index=string_index)

        key = pos_key(string_index, fret)
        bucket = _ensure_bucket(self.by_position, key)
        bucket["attempts"] += 1
        if correct:
            bucket["correct"] += 1


def _default_stats() -> Stats:
    s = Stats()
    _ensure_bucket(s.by_mode, "A")
    _ensure_bucket(s.by_mode, "B")
    return s


def load_stats(path: str) -> Stats:
    """Safely load stats from JSON.

    - Missing file => default stats
    - Invalid JSON => default stats (no crash)
    - Permission/IO errors => default stats (no crash)
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        if not isinstance(raw, dict):
            return _default_stats()

        stats = Stats(
            total_attempts=_safe_int(raw.get("total_attempts", 0), 0),
            total_correct=_safe_int(raw.get("total_correct", 0), 0),
            by_mode=dict(raw.get("by_mode", {}) or {}),
            by_note=dict(raw.get("by_note", {}) or {}),
            by_position=dict(raw.get("by_position", {}) or {}),
            meta=dict(raw.get("meta", {}) or {}),
        )

        _ensure_bucket(stats.by_mode, "A")
        _ensure_bucket(stats.by_mode, "B")
        return stats

    except FileNotFoundError:
        return _default_stats()
    except (json.JSONDecodeError, ValueError, TypeError, OSError) as e:
        logger.warning("Failed to load stats from '%s': %s", path, e)
        return _default_stats()
    except Exception as e:
        logger.exception("Unexpected error while loading stats from '%s': %s", path, e)
        return _default_stats()


def save_stats(path: str, stats: Stats) -> None:
    """Safely save stats to JSON (atomic write, no crash on failure)."""
    payload = {
        "total_attempts": _safe_int(stats.total_attempts, 0),
        "total_correct": _safe_int(stats.total_correct, 0),
        "by_mode": stats.by_mode,
        "by_note": stats.by_note,
        "by_position": stats.by_position,
        "meta": stats.meta,
    }

    try:
        _atomic_write_json(path, payload)
    except Exception as e:
        logger.warning("Failed to save stats to '%s': %s", path, e)
        return
