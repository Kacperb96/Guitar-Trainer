import tkinter as tk
from tkinter import ttk

from guitar_trainer.core.stats import Stats
from guitar_trainer.gui.fretboard import Fretboard


def _pos_key(s: int, f: int) -> str:
    return f"{s},{f}"


class StatsHeatmapFrame(tk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        *,
        stats: Stats,
        max_fret: int,
        on_back=None,
        title_suffix: str | None = None,
    ) -> None:
        super().__init__(master)

        self.stats = stats
        self.max_fret = int(max_fret)
        self.on_back = on_back

        meta = stats.meta or {}
        num_strings = meta.get("num_strings", 6)
        tuning_name = meta.get("tuning_name", "Unknown tuning")
        stats_file = meta.get("stats_file", "")

        attempts = int(stats.total_attempts)
        correct = int(stats.total_correct)
        acc = (100.0 * correct / attempts) if attempts > 0 else 0.0

        header = ttk.Frame(self)
        header.pack(fill="x", pady=(0, 8))

        title = f"Heatmap | {num_strings}-string | {tuning_name} | up to fret {self.max_fret}"
        if title_suffix:
            title += f" | {title_suffix}"
        ttk.Label(header, text=title, font=("Arial", 13)).pack(side="left")

        if self.on_back:
            ttk.Button(header, text="Back", command=self.on_back).pack(side="right")

        info = ttk.Frame(self)
        info.pack(fill="x", pady=(0, 6))
        ttk.Label(info, text=f"Attempts: {attempts}   Accuracy: {acc:.1f}%", foreground="#9aa2b6").pack(side="left")
        if stats_file:
            ttk.Label(info, text=f"File: {stats_file}", foreground="#9aa2b6").pack(side="right")

        # Use dummy tuning for drawing correct string count
        tuning = [0] * int(num_strings)
        self.fretboard = Fretboard(self, num_frets=self.max_fret, tuning=tuning, enable_click_reporting=False)
        self.fretboard.pack(fill="both", expand=True, padx=10, pady=10)

        self._apply_heatmap(num_strings=int(num_strings))

    def _apply_heatmap(self, *, num_strings: int) -> None:
        values: dict[tuple[int, int], float] = {}

        for s in range(num_strings):
            for f in range(self.max_fret + 1):
                data = self.stats.by_position.get(_pos_key(s, f))
                if not data:
                    values[(s, f)] = 1.0  # unseen -> highlight
                    continue

                attempts = int(data.get("attempts", 0))
                correct = int(data.get("correct", 0))
                if attempts <= 0:
                    values[(s, f)] = 1.0
                else:
                    acc = correct / attempts
                    values[(s, f)] = float(1.0 - acc)

        self.fretboard.set_heatmap(values)
