from __future__ import annotations

import glob
import os
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional

from guitar_trainer.core.stats import load_stats, save_stats, Stats


def _safe_float(a: int, b: int) -> float:
    return (a / b) if b > 0 else 0.0


class HeatmapPickerFrame(ttk.Frame):
    """
    Lets the user choose which heatmap to open:
      - separates by num_strings + tuning (from filename + meta if present)
      - shows attempts + accuracy
      - allows deleting the selected stats file (optional but useful)
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        max_fret: int,
        on_open: Callable[[str, int], None],  # (stats_path, max_fret) -> None
        on_back: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(master)

        self.max_fret = int(max_fret)
        self.on_open = on_open
        self.on_back = on_back

        header = ttk.Frame(self)
        header.pack(fill="x", pady=(0, 10))

        ttk.Label(header, text="Choose heatmap profile", font=("Arial", 14, "bold")).pack(side="left")
        if self.on_back:
            ttk.Button(header, text="Back", command=self.on_back).pack(side="right")

        # Max fret control (so you can view smaller/bigger range without leaving)
        controls = ttk.Frame(self)
        controls.pack(fill="x", pady=(0, 10))

        ttk.Label(controls, text="Max fret to display:").pack(side="left")
        self.max_fret_var = tk.StringVar(value=str(self.max_fret))
        ttk.Entry(controls, textvariable=self.max_fret_var, width=6).pack(side="left", padx=(8, 16))
        ttk.Button(controls, text="Refresh list", command=self._refresh).pack(side="left")

        # Table
        self.tree = ttk.Treeview(self, columns=("instrument", "tuning", "attempts", "accuracy", "file"), show="headings")
        self.tree.heading("instrument", text="Instrument")
        self.tree.heading("tuning", text="Tuning")
        self.tree.heading("attempts", text="Attempts")
        self.tree.heading("accuracy", text="Accuracy")
        self.tree.heading("file", text="Stats file")

        self.tree.column("instrument", width=120, anchor="w")
        self.tree.column("tuning", width=220, anchor="w")
        self.tree.column("attempts", width=90, anchor="e")
        self.tree.column("accuracy", width=90, anchor="e")
        self.tree.column("file", width=280, anchor="w")

        self.tree.pack(fill="both", expand=True)

        btns = ttk.Frame(self)
        btns.pack(fill="x", pady=(10, 0))

        ttk.Button(btns, text="Open selected", command=self._open_selected).pack(side="left")
        ttk.Button(btns, text="Delete selected stats", command=self._delete_selected).pack(side="left", padx=(10, 0))

        ttk.Label(btns, text="Tip: stats are stored per strings+tuning.", foreground="#9aa2b6").pack(side="right")

        self._refresh()

    def _scan_stats_files(self) -> list[str]:
        # We keep it simple: scan current working directory for stats_*.json
        # This matches how your app already writes stats in repo folder.
        paths = sorted(glob.glob("stats_*.json"))
        return [p for p in paths if os.path.isfile(p)]

    def _refresh(self) -> None:
        for iid in self.tree.get_children():
            self.tree.delete(iid)

        try:
            max_fret = int(self.max_fret_var.get().strip())
            if max_fret < 0 or max_fret > 24:
                raise ValueError
            self.max_fret = max_fret
        except Exception:
            messagebox.showerror("Invalid max fret", "Max fret must be an integer between 0 and 24.")
            return

        paths = self._scan_stats_files()
        if not paths:
            self.tree.insert("", "end", values=("—", "—", "0", "0.0%", "No stats_*.json found"))
            return

        for p in paths:
            st = load_stats(p)
            meta = st.meta or {}
            num_strings = meta.get("num_strings")
            tuning_name = meta.get("tuning_name")

            instrument = f"{num_strings}-string" if isinstance(num_strings, int) else "?"
            tuning = str(tuning_name) if tuning_name else "(unknown tuning)"

            attempts = int(st.total_attempts)
            acc = 100.0 * _safe_float(int(st.total_correct), attempts)
            self.tree.insert("", "end", values=(instrument, tuning, str(attempts), f"{acc:.1f}%", p))

    def _selected_path(self) -> Optional[str]:
        sel = self.tree.selection()
        if not sel:
            return None
        vals = self.tree.item(sel[0], "values")
        if not vals:
            return None
        p = vals[-1]
        if not isinstance(p, str):
            return None
        if not os.path.isfile(p):
            return None
        return p

    def _open_selected(self) -> None:
        p = self._selected_path()
        if not p:
            messagebox.showinfo("Select a row", "Select a stats profile first.")
            return
        self.on_open(p, self.max_fret)

    def _delete_selected(self) -> None:
        p = self._selected_path()
        if not p:
            messagebox.showinfo("Select a row", "Select a stats profile first.")
            return
        if not messagebox.askyesno("Delete stats", f"Delete stats file?\n\n{p}"):
            return
        try:
            os.remove(p)
        except Exception as e:
            messagebox.showerror("Delete failed", str(e))
            return
        self._refresh()
