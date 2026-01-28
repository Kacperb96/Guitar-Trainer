import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from typing import Callable, Tuple

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

        # -----------------------
        # State vars
        # -----------------------
        self.mode_var = tk.StringVar(value="A")
        self.questions_var = tk.StringVar(value="10")
        self.max_fret_var = tk.StringVar(value="12")
        self.practice_minutes_var = tk.StringVar(value="10")

        self.num_strings_var = tk.StringVar(value=str(DEFAULT_NUM_STRINGS))
        self.tuning_var = tk.StringVar(value=get_default_tuning_name(DEFAULT_NUM_STRINGS))
        self.display_var = tk.StringVar(value="Sharps")
        self.custom_tuning_var = tk.StringVar(value="E A D G B E")

        self.plan_var = tk.StringVar(value="None")
        self.plan_goal_acc_var = tk.StringVar(value="0.80")
        self.plan_goal_window_var = tk.StringVar(value="120")
        self.plan_heat_thr_var = tk.StringVar(value="0.60")

        self.stats_path = self._compute_stats_path()
        self.stats = load_stats(self.stats_path)

        # -----------------------
        # Root layout (dashboard)
        # -----------------------
        self.configure(padding=18)

        root = ttk.Frame(self)
        root.pack(fill="both", expand=True)

        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=0)
        root.rowconfigure(1, weight=1)

        # Header
        header = ttk.Frame(root)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        header.columnconfigure(0, weight=1)
        header.columnconfigure(1, weight=0)

        left_hdr = ttk.Frame(header)
        left_hdr.grid(row=0, column=0, sticky="w")

        ttk.Label(left_hdr, text="Guitar Trainer", style="H1.TLabel").grid(row=0, column=0, sticky="w")
        self.profile_label = ttk.Label(left_hdr, text="", style="Mono.TLabel")
        self.profile_label.grid(row=1, column=0, sticky="w", pady=(4, 0))

        right_hdr = ttk.Frame(header)
        right_hdr.grid(row=0, column=1, rowspan=2, sticky="e")

        ttk.Button(right_hdr, text="Start", style="Primary.TButton", command=self._start_clicked).grid(
            row=0, column=0, padx=(0, 10)
        )
        ttk.Button(right_hdr, text="Heatmap…", command=self._heatmap_clicked).grid(row=0, column=1)

        # Main content grid
        content = ttk.Frame(root)
        content.grid(row=1, column=0, sticky="nsew")
        content.columnconfigure(0, weight=0)  # left stack (scrollable)
        content.columnconfigure(1, weight=1)  # right stack (fills)
        content.rowconfigure(0, weight=1)

        # -----------------------
        # LEFT: scrollable column
        # -----------------------
        left_outer = ttk.Frame(content)
        left_outer.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        left_outer.rowconfigure(0, weight=1)
        left_outer.columnconfigure(0, weight=1)

        self._left_canvas = tk.Canvas(left_outer, highlightthickness=0, bd=0)
        self._left_canvas.grid(row=0, column=0, sticky="nsew")

        self._left_scrollbar = ttk.Scrollbar(left_outer, orient="vertical", command=self._left_canvas.yview)
        self._left_scrollbar.grid(row=0, column=1, sticky="ns")

        self._left_canvas.configure(yscrollcommand=self._left_scrollbar.set)

        # The scrollable content frame (where cards live)
        self._left_inner = ttk.Frame(left_outer)
        self._left_inner.columnconfigure(0, weight=1)

        self._left_window_id = self._left_canvas.create_window(
            (0, 0), window=self._left_inner, anchor="nw"
        )

        # Keep scrollregion updated
        self._left_inner.bind("<Configure>", self._on_left_inner_configure)
        self._left_canvas.bind("<Configure>", self._on_left_canvas_configure)

        # Mouse wheel scrolling on the left column only
        self._bind_mousewheel(self._left_canvas)

        # -----------------------
        # RIGHT: normal column
        # -----------------------
        right = ttk.Frame(content)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=0)
        right.rowconfigure(1, weight=1)

        # -----------------------
        # Cards (LEFT)
        # -----------------------
        mode_outer, mode_inner = self._card(self._left_inner, title="Mode", subtitle="Choose how you want to practice.")
        mode_outer.grid(row=0, column=0, sticky="ew", pady=(0, 12))

        self._radio(mode_inner, "Mode A — Guess the note", "A").pack(anchor="w", pady=3)
        self._radio(mode_inner, "Mode B — Find all positions", "B").pack(anchor="w", pady=3)
        self._radio(mode_inner, "Adaptive (Mode A)", "ADAPT").pack(anchor="w", pady=3)
        self._radio(mode_inner, "Practice Session (timed)", "PRACTICE").pack(anchor="w", pady=3)

        settings_outer, settings_inner = self._card(self._left_inner, title="Settings", subtitle="Instrument, tuning and limits.")
        settings_outer.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        self._build_settings_form(settings_inner)

        plan_outer, plan_inner = self._card(self._left_inner, title="Training plan", subtitle="Optional guidance for Practice mode.")
        plan_outer.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        self._build_plan_form(plan_inner)

        custom_outer, custom_inner = self._card(self._left_inner, title="Custom tuning", subtitle="Lowest → Highest (e.g., E A D G B E).")
        custom_outer.grid(row=3, column=0, sticky="ew")
        self.custom_outer = custom_outer
        self._build_custom_tuning(custom_inner)

        # -----------------------
        # Cards (RIGHT)
        # -----------------------
        profile_outer, profile_inner = self._card(right, title="Profile", subtitle="This is what your progress is saved under.")
        profile_outer.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        self._build_profile_summary(profile_inner)

        actions_outer, actions_inner = self._card(right, title="Quick actions", subtitle="Utilities and maintenance.")
        actions_outer.grid(row=1, column=0, sticky="nsew")
        actions_outer.columnconfigure(0, weight=1)
        self._build_actions(actions_inner)

        # -----------------------
        # Bindings / refresh
        # -----------------------
        self.num_strings_var.trace_add("write", lambda *_: self._on_settings_changed())
        self.tuning_var.trace_add("write", lambda *_: self._on_settings_changed())
        self.mode_var.trace_add("write", lambda *_: self._refresh_mode_dependent_ui())

        self._refresh_tuning_options()
        self._refresh_mode_dependent_ui()
        self._refresh_custom_visibility()
        self._update_profile_header()
        self._update_profile_summary()

    # -----------------------
    # Scroll helpers (LEFT column)
    # -----------------------
    def _on_left_inner_configure(self, _event=None) -> None:
        # Update the scrollregion to encompass the inner frame
        try:
            self._left_canvas.configure(scrollregion=self._left_canvas.bbox("all"))
        except Exception:
            return

    def _on_left_canvas_configure(self, event) -> None:
        # Make the inner window match the canvas width (so cards fill the column)
        try:
            self._left_canvas.itemconfigure(self._left_window_id, width=event.width)
        except Exception:
            return

    def _bind_mousewheel(self, widget: tk.Widget) -> None:
        # Windows / macOS use <MouseWheel>, Linux typically uses Button-4/5
        widget.bind("<Enter>", lambda e: self._set_mousewheel_target(True), add="+")
        widget.bind("<Leave>", lambda e: self._set_mousewheel_target(False), add="+")

    def _set_mousewheel_target(self, active: bool) -> None:
        if active:
            self.bind_all("<MouseWheel>", self._on_mousewheel, add="+")
            self.bind_all("<Button-4>", self._on_mousewheel_linux, add="+")
            self.bind_all("<Button-5>", self._on_mousewheel_linux, add="+")
        else:
            try:
                self.unbind_all("<MouseWheel>")
                self.unbind_all("<Button-4>")
                self.unbind_all("<Button-5>")
            except Exception:
                pass

    def _on_mousewheel(self, event) -> None:
        # Windows: event.delta is typically multiples of 120
        try:
            delta = int(-1 * (event.delta / 120))
            self._left_canvas.yview_scroll(delta, "units")
        except Exception:
            return

    def _on_mousewheel_linux(self, event) -> None:
        try:
            if event.num == 4:
                self._left_canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self._left_canvas.yview_scroll(1, "units")
        except Exception:
            return

    # -----------------------
    # UI helpers
    # -----------------------
    def _card(self, parent: ttk.Frame, *, title: str, subtitle: str) -> Tuple[ttk.Frame, ttk.Frame]:
        outer = ttk.Frame(parent, style="Card.TFrame", padding=14)
        outer.columnconfigure(0, weight=1)

        ttk.Label(outer, text=title, style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(outer, text=subtitle, style="CardMuted.TLabel").grid(row=1, column=0, sticky="w", pady=(2, 10))

        inner = ttk.Frame(outer, style="CardInner.TFrame")
        inner.grid(row=2, column=0, sticky="ew")
        inner.columnconfigure(0, weight=1)

        return outer, inner

    def _radio(self, parent: ttk.Frame, text: str, value: str) -> ttk.Radiobutton:
        return ttk.Radiobutton(parent, text=text, value=value, variable=self.mode_var)

    def _form_row(self, parent: ttk.Frame, label: str) -> ttk.Frame:
        row = ttk.Frame(parent, style="CardInner.TFrame")
        row.pack(fill="x", pady=5)
        row.columnconfigure(0, weight=1)
        row.columnconfigure(1, weight=0)

        ttk.Label(row, text=label, style="Card.TLabel").grid(row=0, column=0, sticky="w")
        return row

    def _get_num_strings(self) -> int:
        try:
            n = int(self.num_strings_var.get().strip())
        except Exception:
            return DEFAULT_NUM_STRINGS
        return n if 4 <= n <= 12 else DEFAULT_NUM_STRINGS

    # -----------------------
    # Forms
    # -----------------------
    def _build_settings_form(self, parent: ttk.Frame) -> None:
        r0 = self._form_row(parent, "Instrument (strings)")
        self.num_strings_combo = ttk.Combobox(
            r0, textvariable=self.num_strings_var, values=["6", "7"], width=6, state="readonly"
        )
        self.num_strings_combo.grid(row=0, column=1, sticky="e")

        r1 = self._form_row(parent, "Tuning")
        self.tuning_combo = ttk.Combobox(r1, textvariable=self.tuning_var, values=[], width=22, state="readonly")
        self.tuning_combo.grid(row=0, column=1, sticky="e")

        r2 = self._form_row(parent, "Display")
        self.display_combo = ttk.Combobox(
            r2, textvariable=self.display_var, values=["Sharps", "Flats"], width=10, state="readonly"
        )
        self.display_combo.grid(row=0, column=1, sticky="e")

        r3 = self._form_row(parent, "Questions")
        self.questions_entry = ttk.Entry(r3, textvariable=self.questions_var, width=8)
        self.questions_entry.grid(row=0, column=1, sticky="e")

        r4 = self._form_row(parent, "Practice (min)")
        self.practice_entry = ttk.Entry(r4, textvariable=self.practice_minutes_var, width=8)
        self.practice_entry.grid(row=0, column=1, sticky="e")

        r5 = self._form_row(parent, "Max fret")
        self.max_fret_entry = ttk.Entry(r5, textvariable=self.max_fret_var, width=8)
        self.max_fret_entry.grid(row=0, column=1, sticky="e")

    def _build_plan_form(self, parent: ttk.Frame) -> None:
        r0 = self._form_row(parent, "Profile")
        self.plan_combo = ttk.Combobox(
            r0,
            textvariable=self.plan_var,
            values=[
                "None",
                "Frets 1–5",
                "Weak spots (heatmap > 0.6)",
                "Strings 3–6",
            ],
            width=22,
            state="readonly",
        )
        self.plan_combo.grid(row=0, column=1, sticky="e")

        r1 = self._form_row(parent, "Goal accuracy")
        self.plan_goal_acc_entry = ttk.Entry(r1, textvariable=self.plan_goal_acc_var, width=8)
        self.plan_goal_acc_entry.grid(row=0, column=1, sticky="e")

        r2 = self._form_row(parent, "Goal window (sec)")
        self.plan_goal_window_entry = ttk.Entry(r2, textvariable=self.plan_goal_window_var, width=8)
        self.plan_goal_window_entry.grid(row=0, column=1, sticky="e")

        r3 = self._form_row(parent, "Heatmap threshold")
        self.plan_heat_thr_entry = ttk.Entry(r3, textvariable=self.plan_heat_thr_var, width=8)
        self.plan_heat_thr_entry.grid(row=0, column=1, sticky="e")

        ttk.Label(
            parent,
            text="Tip: 1.0 means unseen/worst (heatmap uses 1 - accuracy).",
            style="CardMuted.TLabel",
        ).pack(anchor="w", pady=(8, 0))

    def _build_custom_tuning(self, parent: ttk.Frame) -> None:
        self.custom_entry = ttk.Entry(parent, textvariable=self.custom_tuning_var)
        self.custom_entry.pack(fill="x")

        ttk.Label(
            parent,
            text="Accepted: sharps/flats (Eb, D#, Ab) • Space or comma separated.",
            style="CardMuted.TLabel",
        ).pack(anchor="w", pady=(8, 0))

    # -----------------------
    # Right side
    # -----------------------
    def _build_profile_summary(self, parent: ttk.Frame) -> None:
        self.active_file_label = ttk.Label(parent, text="", style="CardMono.TLabel")
        self.active_file_label.pack(anchor="w")

        row = ttk.Frame(parent, style="CardInner.TFrame")
        row.pack(fill="x", pady=(10, 2))
        row.columnconfigure(0, weight=1)
        row.columnconfigure(1, weight=1)
        row.columnconfigure(2, weight=1)

        self.attempts_label = ttk.Label(row, text="Attempts: 0", style="Card.TLabel")
        self.attempts_label.grid(row=0, column=0, sticky="w")

        self.correct_label = ttk.Label(row, text="Correct: 0", style="Card.TLabel")
        self.correct_label.grid(row=0, column=1, sticky="w")

        self.acc_label = ttk.Label(row, text="Accuracy: 0.0%", style="Card.TLabel")
        self.acc_label.grid(row=0, column=2, sticky="w")

        self.acc_bar = ttk.Progressbar(parent, orient="horizontal", mode="determinate", maximum=100)
        self.acc_bar.pack(fill="x", pady=(8, 0))

    def _build_actions(self, parent: ttk.Frame) -> None:
        grid = ttk.Frame(parent, style="CardInner.TFrame")
        grid.pack(fill="x")
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        ttk.Button(grid, text="Show stats", command=self._show_stats_clicked).grid(
            row=0, column=0, sticky="ew", padx=(0, 10), pady=(0, 10)
        )
        ttk.Button(grid, text="Reset stats (this profile)", style="Danger.TButton", command=self._reset_stats_clicked).grid(
            row=0, column=1, sticky="ew", pady=(0, 10)
        )

        ttk.Button(grid, text="Quit", command=self._quit_clicked).grid(row=1, column=0, sticky="w")

        ttk.Label(
            parent,
            text="Progress is stored per strings + tuning profile.",
            style="CardMuted.TLabel",
        ).pack(anchor="w", pady=(10, 0))

    # -----------------------
    # Data / refresh
    # -----------------------
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

    def _refresh_custom_visibility(self) -> None:
        if self.tuning_var.get() == CUSTOM_TUNING_NAME:
            self.custom_outer.grid()
        else:
            self.custom_outer.grid_remove()

    def _refresh_mode_dependent_ui(self) -> None:
        is_practice = (self.mode_var.get().strip().upper() == "PRACTICE")
        self.plan_combo.configure(state=("readonly" if is_practice else "disabled"))

        entry_state = ("normal" if is_practice else "disabled")
        for w in (self.plan_goal_acc_entry, self.plan_goal_window_entry, self.plan_heat_thr_entry):
            w.configure(state=entry_state)

        self._update_profile_header()

    def _update_profile_header(self) -> None:
        n = self._get_num_strings()
        tuning = self.tuning_var.get().strip()
        max_fret = self.max_fret_var.get().strip() or "?"
        mode = self.mode_var.get().strip().upper() or "A"
        display = self.display_var.get().strip()
        self.profile_label.configure(
            text=f"Profile: {n}-string  •  {tuning}  •  Max fret {max_fret}  •  {display}  •  Mode {mode}"
        )

    def _update_profile_summary(self) -> None:
        self.active_file_label.configure(text=f"Active stats file: {self.stats_path}")

        attempts = int(getattr(self.stats, "total_attempts", 0))
        correct = int(getattr(self.stats, "total_correct", 0))
        acc = (100.0 * correct / attempts) if attempts > 0 else 0.0

        self.attempts_label.configure(text=f"Attempts: {attempts}")
        self.correct_label.configure(text=f"Correct: {correct}")
        self.acc_label.configure(text=f"Accuracy: {acc:.1f}%")
        self.acc_bar["value"] = max(0.0, min(100.0, acc))

    def _on_settings_changed(self) -> None:
        self._refresh_tuning_options()
        self._refresh_custom_visibility()

        self.stats_path = self._compute_stats_path()
        self.stats = load_stats(self.stats_path)

        self._update_profile_header()
        self._update_profile_summary()

    # -----------------------
    # Actions
    # -----------------------
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
        self._update_profile_summary()

    def _reset_stats_clicked(self) -> None:
        if not messagebox.askyesno(
            "Reset stats",
            f"This will erase stats for this profile:\n{self.stats_path}\n\nContinue?",
        ):
            return
        self.stats = Stats()
        save_stats(self.stats_path, self.stats)
        messagebox.showinfo("Reset stats", f"Stats reset:\n{self.stats_path}")
        self._update_profile_summary()

    def _quit_clicked(self) -> None:
        self.winfo_toplevel().destroy()
