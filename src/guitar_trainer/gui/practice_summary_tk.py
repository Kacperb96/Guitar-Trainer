from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass


@dataclass(frozen=True)
class PracticeSummary:
    minutes: int
    max_fret: int
    tuning_name: str

    answered: int
    correct: int
    accuracy_percent: float
    avg_time_sec: float


class PracticeSummaryFrame(tk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        *,
        summary: PracticeSummary,
        on_show_heatmap: callable | None = None,  # callback(max_fret)
        on_repeat: callable | None = None,        # callback()
        on_back: callable | None = None,          # callback()
    ) -> None:
        super().__init__(master)

        title = tk.Label(self, text="Practice Summary", font=("Arial", 15))
        title.pack(pady=(0, 10))

        subtitle = tk.Label(
            self,
            text=f"{summary.minutes} min | Max fret: {summary.max_fret} | Tuning: {summary.tuning_name}",
            fg="gray",
        )
        subtitle.pack(pady=(0, 12))

        card = tk.LabelFrame(self, text="Results")
        card.pack(fill="x", padx=12, pady=8)

        def row(label: str, value: str) -> None:
            r = tk.Frame(card)
            r.pack(fill="x", padx=10, pady=4)
            tk.Label(r, text=label).pack(side="left")
            tk.Label(r, text=value, font=("Arial", 11, "bold")).pack(side="right")

        row("Answered", str(summary.answered))
        row("Correct", f"{summary.correct}")
        row("Accuracy", f"{summary.accuracy_percent:.1f}%")
        row("Avg response time", f"{summary.avg_time_sec:.2f}s")

        actions = tk.Frame(self)
        actions.pack(pady=14)

        btn_heatmap = tk.Button(
            actions,
            text="Show heatmap",
            width=14,
            command=(lambda: on_show_heatmap(summary.max_fret)) if on_show_heatmap else None,
            state=tk.NORMAL if on_show_heatmap else tk.DISABLED,
        )
        btn_heatmap.pack(side="left", padx=6)

        btn_repeat = tk.Button(
            actions,
            text="Repeat session",
            width=14,
            command=on_repeat if on_repeat else None,
            state=tk.NORMAL if on_repeat else tk.DISABLED,
        )
        btn_repeat.pack(side="left", padx=6)

        btn_back = tk.Button(
            actions,
            text="Back to menu",
            width=14,
            command=on_back if on_back else None,
            state=tk.NORMAL if on_back else tk.DISABLED,
        )
        btn_back.pack(side="left", padx=6)
