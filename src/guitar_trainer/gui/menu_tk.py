import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from typing import Callable

from guitar_trainer.core.stats import Stats, load_stats, save_stats
from guitar_trainer.core.tuning import (
    get_tuning_presets,
    get_default_tuning_name,
    DEFAULT_NUM_STRINGS,
    CUSTOM_TUNING_NAME,
    parse_custom_tuning_text,
)
from guitar_trainer.core.settings import (
    build_settings_from_menu,
    parse_int_field,
    MAX_FRET_MIN,
    MAX_FRET_MAX,
)


class MenuFrame(ttk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        *,
        stats_path_resolver: Callable[[int, str, list[int] | None], str],
        on_start: callable,     # callback(..., custom_tuning, plan_config)
        on_heatmap: callable,   # callback(max_fret)
    ) -> None:
        super().__init__(master)

        self.stats_path_resolver = stats_path_resolver
        self.on_start = on_start
        self.on_heatmap = on_heatmap

        # Vars
        self.mode_var = tk.StringVar(value="A")
        self.questions_var = tk.StringVar(value="10")
        self.max_fret_var = tk.StringVar(value="12")
        self.practice_minutes_var = tk.StringVar(value="10")

        self.num_strings_var = tk.StringVar(value=str(DEFAULT_NUM_STRINGS))
        self.tuning_var = tk.StringVar(value=get_default_tuning_name(DEFAULT_NUM_STRINGS))
        self.display_var = tk.StringVar(value="Sharps")
        self.custom_tuning_var = tk.StringVar(value="E A D G B E")

        # Training plan (Practice only)
        self.plan_var = tk.StringVar(value="None")
        self.plan_goal_acc_var = tk.StringVar(value="0.80")
        self.plan_goal_window_var = tk.StringVar(value="120")
        self.plan_heat_thr_var = tk.StringVar(value="0.60")

        # initial stats path based on current selection
        self.stats_path = self._compute_stats_path()
        self.stats = load_stats(self.stats_path)

        # Layout
        root = ttk.Frame(self)
        root.pack(fill="both", expand=True)

        left = ttk.Frame(root)
        left.pack(side="left", fill="y", padx=(0, 14))
        left.configure(padding=16)

        right = ttk.Frame(root)
        right.pack(side="left", fill="both", expand=True)
        right.configure(padding=16)

        ttk.Label(left, text="Guitar Trainer", font=("Arial", 18, "bold")).pack(anchor="w")
        ttk.Label(
            left,
            text="Progress is separate per instrument AND tuning.",
            foreground="#9aa2b6",
        ).pack(anchor="w", pady=(2, 14))

        # Mode
        mode_box = ttk.Labelframe(left, text="Mode")
        mode_box.pack(fill="x", pady=(0, 14))
        ttk.Radiobutton(mode_box, text="Mode A — Guess the note", value="A", variable=self.mode_var).pack(anchor="w", pady=2)
        ttk.Radiobutton(mode_box, text="Mode B — Find all positions", value="B", variable=self.mode_var).pack(anchor="w", pady=2)
        ttk.Radiobutton(mode_box, text="Adaptive (Mode A)", value="ADAPT", variable=self.mode_var).pack(anchor="w", pady=2)
        ttk.Radiobutton(mode_box, text="Practice Session (timed)", value="PRACTICE", variable=self.mode_var).pack(anchor="w", pady=2)

        # Settings
        settings = ttk.Labelframe(left, text="Settings")
        settings.pack(fill="x", pady=(0, 14))

        def row(parent, label: str):
            r = ttk.Frame(parent)
            r.pack(fill="x", pady=4)
            ttk.Label(r, text=label).pack(side="left")
            return r

        r0 = row(settings, "Instrument (strings)")
        self.num_strings_combo = ttk.Combobox(
            r0, textvariable=self.num_strings_var, values=["6", "7"], width=6, state="readonly"
        )
        self.num_strings_combo.pack(side="right")

        r1 = row(settings, "Tuning")
        self.tuning_combo = ttk.Combobox(r1, textvariable=self.tuning_var, values=[], width=26, state="readonly")
        self.tuning_combo.pack(side="right")

        r2 = row(settings, "Display")
        ttk.Combobox(r2, textvariable=self.display_var, values=["Sharps", "Flats"], width=10, state="readonly").pack(side="right")

        r3 = row(settings, "Questions")
        ttk.Entry(r3, textvariable=self.questions_var, width=8).pack(side="right")

        r4 = row(settings, "Practice (min)")
        ttk.Entry(r4, textvariable=self.practice_minutes_var, width=8).pack(side="right")

        r5 = row(settings, "Max fret")
        ttk.Entry(r5, textvariable=self.max_fret_var, width=8).pack(side="right")

        # Training plan
        plan_box = ttk.Labelframe(left, text="Training plan (Practice)")
        plan_box.pack(fill="x", pady=(0, 14))

        def prow(label: str):
            rr = ttk.Frame(plan_box)
            rr.pack(fill="x", pady=4)
            ttk.Label(rr, text=label).pack(side="left")
            return rr

        pr0 = prow("Profile")
        self.plan_combo = ttk.Combobox(
            pr0,
            textvariable=self.plan_var,
            values=[
                "None",
                "Frets 1–5",
                "Weak spots (heatmap > 0.6)",
                "Strings 3–6",
            ],
            width=26,
            state="readonly",
        )
        self.plan_combo.pack(side="right")

        pr1 = prow("Goal accuracy")
        self.plan_goal_acc_entry = ttk.Entry(pr1, textvariable=self.plan_goal_acc_var, width=8)
        self.plan_goal_acc_entry.pack(side="right")
        ttk.Label(
            plan_box,
            text="Example: 0.80 means 80% over the goal window.",
            foreground="#9aa2b6",
        ).pack(anchor="w", pady=(2, 0))

        pr2 = prow("Goal window (sec)")
        self.plan_goal_window_entry = ttk.Entry(pr2, textvariable=self.plan_goal_window_var, width=8)
        self.plan_goal_window_entry.pack(side="right")

        pr3 = prow("Heatmap threshold")
        self.plan_heat_thr_entry = ttk.Entry(pr3, textvariable=self.plan_heat_thr_var, width=8)
        self.plan_heat_thr_entry.pack(side="right")
        ttk.Label(
            plan_box,
            text="0..1, where 1 = unseen/worst (heatmap scale).",
            foreground="#9aa2b6",
        ).pack(anchor="w", pady=(2, 0))

        # Custom tuning
        custom_box = ttk.Labelframe(left, text="Custom tuning")
        custom_box.pack(fill="x", pady=(0, 12))
        ttk.Label(custom_box, text="Lowest → Highest", foreground="#9aa2b6").pack(anchor="w")
        self.custom_entry = ttk.Entry(custom_box, textvariable=self.custom_tuning_var)
        self.custom_entry.pack(fill="x", pady=(6, 0))
        ttk.Label(
            custom_box,
            text="Example: E A D G B E  |  You can use Eb, D#, Ab, etc.",
            foreground="#9aa2b6",
        ).pack(anchor="w", pady=(6, 0))

        self.custom_box = custom_box
        self._refresh_tuning_options()
        self._refresh_custom_visibility()

        # Right actions
        ttk.Label(right, text="Actions", font=("Arial", 14, "bold")).pack(anchor="w")
        ttk.Label(right, text="Heatmaps are stored per strings+tuning.", foreground="#9aa2b6").pack(anchor="w", pady=(2, 10))

        self.active_stats_label = ttk.Label(right, text="", foreground="#9aa2b6")
        self.active_stats_label.pack(anchor="w", pady=(0, 14))
        self._update_active_stats_label()

        actions = ttk.Frame(right)
        actions.pack(fill="x")

        row1 = ttk.Frame(actions)
        row1.pack(fill="x", pady=(0, 10))
        ttk.Button(row1, text="▶ Start", command=self._start_clicked).pack(side="left", fill="x", expand=True, padx=(0, 10))
        ttk.Button(row1, text="🔥 Heatmap…", command=self._heatmap_clicked).pack(side="left", fill="x", expand=True)

        row2 = ttk.Frame(actions)
        row2.pack(fill="x", pady=(0, 10))
        ttk.Button(row2, text="📊 Show stats", command=self._show_stats_clicked).pack(side="left", fill="x", expand=True, padx=(0, 10))
        ttk.Button(row2, text="🧹 Reset stats (this profile)", command=self._reset_stats_clicked).pack(side="left", fill="x", expand=True)

        ttk.Button(actions, text="✖ Quit", command=self._quit_clicked).pack(anchor="w", pady=(6, 0))

        # Bindings
        self.num_strings_var.trace_add("write", lambda *_: self._on_settings_changed())
        self.tuning_var.trace_add("write", lambda *_: self._on_settings_changed())
        self.mode_var.trace_add("write", lambda *_: self._refresh_plan_controls())

        self._refresh_plan_controls()

    def _get_num_strings(self) -> int:
        # Keep this robust and independent of settings.py symbols.
        try:
            n = int(self.num_strings_var.get().strip())
        except Exception:
            return DEFAULT_NUM_STRINGS
        return n if 4 <= n <= 12 else DEFAULT_NUM_STRINGS

    def _refresh_tuning_options(self) -> None:
        n = self._get_num_strings()
        presets = get_tuning_presets(num_strings=n)
        values = list(presets.keys())
        if CUSTOM_TUNING_NAME not in values:
            values.append(CUSTOM_TUNING_NAME)
        self.tuning_combo.configure(values=values)

        cur = self.tuning_var.get()
        if cur not in values:
            self.tuning_var.set(get_default_tuning_name(n))

    def _refresh_custom_visibility(self) -> None:
        if self.tuning_var.get() == CUSTOM_TUNING_NAME:
            self.custom_box.pack(fill="x", pady=(0, 12))
        else:
            self.custom_box.pack_forget()

    def _compute_custom_tuning(self) -> list[int] | None:
        tuning_name = self.tuning_var.get().strip()
        if tuning_name != CUSTOM_TUNING_NAME:
            return None
        num_strings = self._get_num_strings()
        return parse_custom_tuning_text(self.custom_tuning_var.get(), num_strings=num_strings)

    def _compute_stats_path(self) -> str:
        num_strings = self._get_num_strings()
        tuning_name = self.tuning_var.get().strip()
        custom_tuning = None
        if tuning_name == CUSTOM_TUNING_NAME:
            try:
                custom_tuning = self._compute_custom_tuning()
            except Exception:
                custom_tuning = None
        return self.stats_path_resolver(num_strings, tuning_name, custom_tuning)

    def _update_active_stats_label(self) -> None:
        self.active_stats_label.configure(text=f"Active stats file: {self.stats_path}")

    def _on_settings_changed(self) -> None:
        self._refresh_tuning_options()
        self._refresh_custom_visibility()

        self.stats_path = self._compute_stats_path()
        self.stats = load_stats(self.stats_path)
        self._update_active_stats_label()

    def _refresh_plan_controls(self) -> None:
        is_practice = (self.mode_var.get().strip().upper() == "PRACTICE")
        self.plan_combo.configure(state=("readonly" if is_practice else "disabled"))
        entry_state = ("normal" if is_practice else "disabled")
        for w in (self.plan_goal_acc_entry, self.plan_goal_window_entry, self.plan_heat_thr_entry):
            w.configure(state=entry_state)

    def _start_clicked(self) -> None:
        try:
            settings = build_settings_from_menu(
                mode_raw=self.mode_var.get(),
                questions_raw=self.questions_var.get(),
                practice_minutes_raw=self.practice_minutes_var.get(),
                max_fret_raw=self.max_fret_var.get(),
                num_strings_raw=self.num_strings_var.get(),
                tuning_name_raw=self.tuning_var.get(),
                display_raw=self.display_var.get(),
                custom_tuning_raw=self.custom_tuning_var.get(),
                plan_name_raw=self.plan_var.get(),
                plan_goal_acc_raw=self.plan_goal_acc_var.get(),
                plan_goal_window_raw=self.plan_goal_window_var.get(),
                plan_heat_thr_raw=self.plan_heat_thr_var.get(),
            )
        except ValueError as e:
            messagebox.showerror("Invalid settings", str(e))
            return

        self.on_start(
            settings.mode,
            settings.num_questions,
            settings.max_fret,
            settings.tuning_name,
            settings.practice_minutes,
            settings.prefer_flats,
            settings.num_strings,
            settings.custom_tuning,
            settings.plan_config,
        )

    def _heatmap_clicked(self) -> None:
        try:
            max_fret = parse_int_field(
                self.max_fret_var.get(),
                min_value=MAX_FRET_MIN,
                max_value=MAX_FRET_MAX,
                field_name="Max fret",
            )
        except ValueError as e:
            messagebox.showerror("Invalid settings", str(e))
            return
        self.on_heatmap(max_fret)

    def _show_stats_clicked(self) -> None:
        self.stats = load_stats(self.stats_path)
        attempts = int(self.stats.total_attempts)
        correct = int(self.stats.total_correct)
        acc = (100.0 * correct / attempts) if attempts > 0 else 0.0
        messagebox.showinfo(
            "Stats",
            f"Stats file: {self.stats_path}\n\nAttempts: {attempts}\nCorrect: {correct}\nAccuracy: {acc:.1f}%",
        )

    def _reset_stats_clicked(self) -> None:
        if not messagebox.askyesno(
            "Reset stats",
            f"This will erase stats for this profile:\n{self.stats_path}\n\nContinue?",
        ):
            return
        self.stats = Stats()
        save_stats(self.stats_path, self.stats)
        messagebox.showinfo("Reset stats", f"Stats reset:\n{self.stats_path}")

    def _quit_clicked(self) -> None:
        self.winfo_toplevel().destroy()
