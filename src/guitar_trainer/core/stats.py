from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


def _empty_bucket() -> dict[str, int]:
    return {"attempts": 0, "correct": 0}


@dataclass
class Stats:
    total_attempts: int = 0
    total_correct: int = 0

    by_mode: dict[str, dict[str, int]] = field(default_factory=dict)
    by_note: dict[str, dict[str, int]] = field(default_factory=dict)
    by_string: dict[str, dict[str, int]] = field(default_factory=dict)

    # NEW: per-position statistics for heatmap (key: "string,fret")
    by_position: dict[str, dict[str, int]] = field(default_factory=dict)

    # -------- recording --------

    def record_attempt(
        self,
        *,
        mode: str,
        correct: bool,
        note_name: str,
        string_index: int,
    ) -> None:
        if mode not in {"A", "B"}:
            raise ValueError("mode must be 'A' or 'B'")
        if string_index < 0 or string_index > 5:
            raise ValueError("string_index must be between 0 and 5")

        self.total_attempts += 1
        if correct:
            self.total_correct += 1

        self._record_bucket(self.by_mode, mode, correct)
        self._record_bucket(self.by_note, note_name, correct)
        self._record_bucket(self.by_string, str(string_index), correct)

    def record_position_attempt(
        self,
        *,
        correct: bool,
        note_name: str,
        string_index: int,
        fret: int,
    ) -> None:
        """
        Mode A helper: record stats per (string,fret) position for heatmap.
        """
        if fret < 0:
            raise ValueError("fret must be >= 0")
        # this records totals + by_mode/by_note/by_string
        self.record_attempt(
            mode="A",
            correct=correct,
            note_name=note_name,
            string_index=string_index,
        )
        key = f"{string_index},{fret}"
        self._record_bucket(self.by_position, key, correct)

    def record_attempt_mode_b(
        self,
        *,
        correct: bool,
        note_name: str,
    ) -> None:
        self.total_attempts += 1
        if correct:
            self.total_correct += 1

        self._record_bucket(self.by_mode, "B", correct)
        self._record_bucket(self.by_note, note_name, correct)

    # -------- helpers --------

    @staticmethod
    def _record_bucket(
        bucket: dict[str, dict[str, int]],
        key: str,
        correct: bool,
    ) -> None:
        if key not in bucket:
            bucket[key] = _empty_bucket()

        bucket[key]["attempts"] += 1
        if correct:
            bucket[key]["correct"] += 1

    # -------- serialization --------

    def to_dict(self) -> dict:
        return {
            "total_attempts": self.total_attempts,
            "total_correct": self.total_correct,
            "by_mode": self.by_mode,
            "by_note": self.by_note,
            "by_string": self.by_string,
            "by_position": self.by_position,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Stats":
        return cls(
            total_attempts=data.get("total_attempts", 0),
            total_correct=data.get("total_correct", 0),
            by_mode=data.get("by_mode", {}),
            by_note=data.get("by_note", {}),
            by_string=data.get("by_string", {}),
            by_position=data.get("by_position", {}),
        )

    # -------- presentation --------

    def summary(self) -> str:
        lines: list[str] = []

        if self.total_attempts == 0:
            return "No statistics yet."

        accuracy = 100 * self.total_correct / self.total_attempts
        lines.append(
            f"Total: {self.total_attempts} attempts, "
            f"{self.total_correct} correct ({accuracy:.1f}%)"
        )

        for mode, data in self.by_mode.items():
            if data["attempts"] == 0:
                continue
            acc = 100 * data["correct"] / data["attempts"]
            lines.append(
                f"Mode {mode}: {data['attempts']} "
                f"({data['correct']} correct, {acc:.1f}%)"
            )

        lines.append("\nNotes (most practiced):")
        for note, data in sorted(
            self.by_note.items(),
            key=lambda x: x[1]["attempts"],
            reverse=True,
        )[:5]:
            acc = 100 * data["correct"] / data["attempts"]
            lines.append(f"  {note}: {data['attempts']} attempts ({acc:.1f}%)")

        lines.append("")
        lines.append(f"Heatmap data points (positions): {len(self.by_position)}")

        return "\n".join(lines)


# -------- file IO --------

def load_stats(path: str) -> Stats:
    p = Path(path)
    if not p.exists():
        return Stats()

    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return Stats.from_dict(data)


def save_stats(path: str, stats: Stats) -> None:
    p = Path(path)
    with p.open("w", encoding="utf-8") as f:
        json.dump(stats.to_dict(), f, indent=2, sort_keys=True)
