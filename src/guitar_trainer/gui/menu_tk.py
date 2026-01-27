import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

from guitar_trainer.gui.theme import BG
from guitar_trainer.core.stats import Stats, load_stats, save_stats
from guitar_trainer.core.tuning import (
    get_tuning_presets,
    get_default_tuning_name,
    DEFAULT_NUM_STRINGS,
    CUSTOM_TUNING_NAME,
    parse_custom_tuning_text,
)


class MenuFrame(ttk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        *,
        stats_path: str,
        on_start: callable,   # callback(mode, num_questions, max_fret, tuning_name, practice_minutes, prefer_flats, num_strings, custom_tuning)
        on_heatmap: callable, # callback(max_fret, num_strings)
    ) -> None:
        super().__init__(master)

        self.stats_path = stats_path
        self.on_start = on_start
        self.on_heatmap = on_heatmap
        self.stats = load_stats(self.stats_path)

        # Vars
        self.mode_var = tk.StringVar(value="A")
        self.questions_var = tk.StringVar(value="10")
        self.max_fret_var = tk.StringVar(value="12")
        self.practice_minutes_var = tk.StringVar(value="10")

        self.num_strings_var = tk.StringVar(value=str(DEFAULT_NUM_STRINGS))  # "6" or "7"
        self.tuning_var = tk.StringVar(value=get_default_tuning_name(DEFAULT_NUM_STRINGS))
        self.display_var = tk.StringVar(value="Sharps")  # or "Flats"
        self.custom_tuning_var = tk.StringVar(value="E A D G B E")

        # Layout: two columns (left settings, right actions/info)
        root = ttk.Frame(self)
        root.pack(fill="both", expand=True)

        left = ttk.Frame(root, style="Panel.TFrame")
        left.pack(side="left", fill="y", padx=(0, 14))
        left.configure(padding=16)

        right = ttk.Frame(root, style="Panel2.TFrame")
        right.pack(side="left", fill="both", expand=True)
        right.configure(padding=16)

        # Title
        ttk.Label(left, text="Guitar Trainer", style="Title.TLabel").pack(anchor="w")
        ttk.Label(left, text="Dark • Modern • Practice-focused", style="Muted.TLabel").pack(anchor="w", pady=(2, 14))

        # Mode box
        mode_box = ttk.Labelframe(left, text="Mode")
        mode_box.pack(fill="x", pady=(0, 12))

        ttk.Radiobutton(mode_box, text="Mode A — Guess the note", variable=self.mode_var, value="A").pack(anchor="w", pady=2)
        ttk.Radiobutton(mode_box, text="Mode B — Find all positions", variable=self.mode_var, value="B").pack(anchor="w", pady=2)
        ttk.Radiobutton(mode_box, text="Adaptive (Mode A)", variable=self.mode_var, value="ADAPT").pack(anchor="w", pady=2)
        ttk.Radiobutton(mode_box, text="Practice Session (timed)", variable=self.mode_var, value="PRACTICE").pack(anchor="w", pady=2)

        # Settings box
        settings = ttk.Labelframe(left, text="Settings")
        settings.pack(fill="x", pady=(0, 12))

        def row(parent, label: str):
            r = ttk.Frame(parent)
            r.pack(fill="x", pady=6)
            ttk.Label(r, text=label).pack(side="left")
            return r

        r0 = row(settings, "Instrument")
        ttk.Combobox(r0, textvariable=self.num_strings_var, values=["6", "7"], width=6, state="readonly").pack(side="right")

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

        # Custom tuning box (shows only when Custom... is selected)
        custom_box = ttk.Labelframe(left, text="Custom tuning")
        custom_box.pack(fill="x", pady=(0, 12))
        ttk.Label(custom_box, text="Lowest → Highest", style="Muted.TLabel").pack(anchor="w")
        self.custom_entry = ttk.Entry(custom_box, textvariable=self.custom_tuning_var)
        self.custom_entry.pack(fill="x", pady=(6, 4))
        self.custom_hint = ttk.Label(custom_box, text="", style="Muted.TLabel")
        self.custom_hint.pack(anchor="w")

        # Buttons on the right
        ttk.Label(right, text="Quick actions", style="Title.TLabel").pack(anchor="w")
        ttk.Label(right, text="Start training or explore your stats.", style="Muted.TLabel").pack(anchor="w", pady=(2, 16))

        btn_grid = ttk.Frame(right)
        btn_grid.pack(fill="x")

        start_btn = ttk.Button(btn_grid, text="▶ Start", style="Primary.TButton", command=self._start_clicked)
        start_btn.grid(row=0, column=0, sticky="ew", padx=(0, 10), pady=(0, 10))

        heat_btn = ttk.Button(btn_grid, text="🔥 Heatmap", command=self._heatmap_clicked)
        heat_btn.grid(row=0, column=1, sticky="ew", pady=(0, 10))

        stats_btn = ttk.Button(btn_grid, text="📊 Show stats", command=self._show_stats)
        stats_btn.grid(row=1, column=0, sticky="ew", padx=(0, 10), pady=(0, 10))

        reset_btn = ttk.Button(btn_grid, text="🧹 Reset stats", style="Danger.TButton", command=self._reset_stats)
        reset_btn.grid(row=1, column=1, sticky="ew", pady=(0, 10))

        quit_btn = ttk.Button(right, text="✖ Quit", command=self._quit)
        quit_btn.pack(anchor="w", pady=(6, 0))

        btn_grid.columnconfigure(0, weight=1)
        btn_grid.columnconfigure(1, weight=1)

        # Tip
        tip = ttk.Label(
            right,
            text="Tip: Strings are numbered like on a diagram — 1 at top (thinnest), N at bottom (thickest).",
            style="Muted.TLabel",
            wraplength=520,
        )
        tip.pack(anchor="w", pady=(18, 0))

        # bindings
        self.num_strings_var.trace_add("write", lambda *_: self._refresh_tuning_options())
        self.tuning_var.trace_add("write", lambda *_: self._refresh_custom_visibility())

        self._refresh_tuning_options()
        self._refresh_custom_visibility()

    def _parse_int(self, value: str, *, min_value: int, max_value: int, field_name: str) -> int:
        value = value.strip()
        try:
            x = int(value)
        except ValueError:
            raise ValueError(f"{field_name} must be an integer.")
        if x < min_value or x > max_value:
            raise ValueError(f"{field_name} must be between {min_value} and {max_value}.")
        return x

    def _get_num_strings(self) -> int:
        v = self.num_strings_var.get().strip()
        return 7 if v == "7" else 6

    def _refresh_tuning_options(self) -> None:
        n = self._get_num_strings()
        presets = get_tuning_presets(n)
        options = list(presets.keys()) + [CUSTOM_TUNING_NAME]

        self.tuning_combo["values"] = options

        cur = self.tuning_var.get()
        if cur not in options:
            self.tuning_var.set(get_default_tuning_name(n))

        if n == 7:
            self.custom_tuning_var.set("B E A D G B E")
            self.custom_hint.config(text="Example: B E A D G B E  |  You can use Eb, D#, Ab, etc.")
        else:
            self.custom_tuning_var.set("E A D G B E")
            self.custom_hint.config(text="Example: E A D G B E  |  You can use Eb, D#, Ab, etc.")

        self._refresh_custom_visibility()

    def _refresh_custom_visibility(self) -> None:
        is_custom = (self.tuning_var.get().strip() == CUSTOM_TUNING_NAME)
        state = "normal" if is_custom else "disabled"
        self.custom_entry.configure(state=state)

    def _start_clicked(self) -> None:
        try:
            mode = self.mode_var.get().strip().upper()
            num_questions = self._parse_int(self.questions_var.get(), min_value=1, max_value=200, field_name="Questions")
            practice_minutes = self._parse_int(self.practice_minutes_var.get(), min_value=1, max_value=120, field_name="Practice minutes")
            max_fret = self._parse_int(self.max_fret_var.get(), min_value=0, max_value=24, field_name="Max fret")
        except ValueError as e:
            messagebox.showerror("Invalid settings", str(e))
            return

        num_strings = self._get_num_strings()
        tuning_name = self.tuning_var.get().strip()
        prefer_flats = (self.display_var.get().strip().lower() == "flats")

        custom_tuning = None
        if tuning_name == CUSTOM_TUNING_NAME:
            try:
                custom_tuning = parse_custom_tuning_text(self.custom_tuning_var.get(), num_strings=num_strings)
            except ValueError as e:
                messagebox.showerror("Invalid custom tuning", str(e))
                return

        if mode not in {"A", "B", "ADAPT", "PRACTICE"}:
            messagebox.showerror("Invalid mode", "Mode must be A, B, ADAPT or PRACTICE.")
            return

        self.on_start(mode, num_questions, max_fret, tuning_name, practice_minutes, prefer_flats, num_strings, custom_tuning)

    def _heatmap_clicked(self) -> None:
        try:
            max_fret = self._parse_int(self.max_fret_var.get(), min_value=0, max_value=24, field_name="Max fret")
        except ValueError as e:
            messagebox.showerror("Invalid settings", str(e))
            return
        num_strings = self._get_num_strings()
        self.on_heatmap(max_fret, num_strings)

    def _show_stats(self) -> None:
        self.stats = load_stats(self.stats_path)
        messagebox.showinfo("Statistics", self.stats.summary())

    def _reset_stats(self) -> None:
        answer = messagebox.askyesno("Reset stats", "Are you sure you want to reset statistics?")
        if not answer:
            return
        self.stats = Stats()
        save_stats(self.stats_path, self.stats)
        messagebox.showinfo("Reset stats", "Statistics have been reset.")

    def _quit(self) -> None:
        self.master.destroy()
