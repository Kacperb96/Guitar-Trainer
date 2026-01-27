from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from typing import List, Tuple


@dataclass(frozen=True)
class PracticeSummary:
    minutes: int
    max_fret: int
    tuning_name: str

    answered: int
    correct: int
    accuracy_percent: float
    avg_time_sec: float

    # items: (label, attempts, accuracy_percent_or_None)
    weak_strings: List[Tuple[str, int, float | None]]
    weak_frets: List[Tuple[str, int, float | None]]


class PracticeSummaryFrame(tk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        *,
        summary: PracticeSummary,
        on_show_heatmap: callable | None = None,      # callback(max_fret)
        on_train_weak_strings: callable | None = None,  # callback()
        on_train_weak_frets: callable | None = None,    # callback()
        on_repeat: callable | None = None,            # callback()
        on_back: callable | None = None,              # callback()
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

        # ---- Results ----
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

        # ---- Weak areas ----
        weak = tk.LabelFrame(self, text="Weak areas (based on your saved stats)")
        weak.pack(fill="x", padx=12, pady=8)

        def fmt_item(label: str, attempts: int, acc: float | None) -> str:
            if attempts == 0:
                return f"{label}: not practiced yet"
            if acc is None:
                return f"{label}: attempts={attempts}"
            return f"{label}: {acc:.1f}% (attempts={attempts})"

        left = tk.Frame(weak)
        left.pack(side="left", fill="both", expand=True, padx=10, pady=8)

        right = tk.Frame(weak)
        right.pack(side="left", fill="both", expand=True, padx=10, pady=8)

        tk.Label(left, text="Weak strings", font=("Arial", 11, "bold")).pack(anchor="w")
        if summary.weak_strings:
            for label, attempts, acc in summary.weak_strings:
                tk.Label(left, text="• " + fmt_item(label, attempts, acc), fg="gray").pack(anchor="w")
        else:
            tk.Label(left, text="No data yet.", fg="gray").pack(anchor="w")

        tk.Label(right, text="Weak frets", font=("Arial", 11, "bold")).pack(anchor="w")
        if summary.weak_frets:
            for label, attempts, acc in summary.weak_frets:
                tk.Label(right, text="• " + fmt_item(label, attempts, acc), fg="gray").pack(anchor="w")
        else:
            tk.Label(right, text="No data yet.", fg="gray").pack(anchor="w")

        # ---- Actions ----
        actions = tk.Frame(self)
        actions.pack(pady=14)

        tk.Button(
            actions,
            text="Show heatmap",
            width=16,
            command=(lambda: on_show_heatmap(summary.max_fret)) if on_show_heatmap else None,
            state=tk.NORMAL if on_show_heatmap else tk.DISABLED,
        ).pack(side="left", padx=6)

        tk.Button(
            actions,
            text="Train weak strings",
            width=16,
            command=on_train_weak_strings if on_train_weak_strings else None,
            state=tk.NORMAL if on_train_weak_strings else tk.DISABLED,
        ).pack(side="left", padx=6)

        tk.Button(
            actions,
            text="Train weak frets",
            width=16,
            command=on_train_weak_frets if on_train_weak_frets else None,
            state=tk.NORMAL if on_train_weak_frets else tk.DISABLED,
        ).pack(side="left", padx=6)

        tk.Button(
            actions,
            text="Repeat session",
            width=16,
            command=on_repeat if on_repeat else None,
            state=tk.NORMAL if on_repeat else tk.DISABLED,
        ).pack(side="left", padx=6)

        tk.Button(
            actions,
            text="Back to menu",
            width=16,
            command=on_back if on_back else None,
            state=tk.NORMAL if on_back else tk.DISABLED,
        ).pack(side="left", padx=6)
