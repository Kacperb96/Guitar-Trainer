import tkinter as tk
from tkinter import messagebox

from guitar_trainer.core.stats import Stats, load_stats, save_stats
from guitar_trainer.core.tuning import (
    get_tuning_presets,
    get_default_tuning_name,
    DEFAULT_NUM_STRINGS,
    CUSTOM_TUNING_NAME,
    parse_custom_tuning_text,
)


class MenuFrame(tk.Frame):
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

        self.mode_var = tk.StringVar(value="A")
        self.questions_var = tk.StringVar(value="10")
        self.max_fret_var = tk.StringVar(value="12")
        self.practice_minutes_var = tk.StringVar(value="10")

        self.num_strings_var = tk.StringVar(value=str(DEFAULT_NUM_STRINGS))  # "6" or "7"
        self.tuning_var = tk.StringVar(value=get_default_tuning_name(DEFAULT_NUM_STRINGS))

        self.display_var = tk.StringVar(value="Sharps")  # or "Flats"

        # custom tuning input
        self.custom_tuning_var = tk.StringVar(value="E A D G B E")

        title = tk.Label(self, text="Guitar Trainer – Start Menu", font=("Arial", 14))
        title.pack(pady=(0, 10))

        mode_box = tk.LabelFrame(self, text="Mode")
        mode_box.pack(fill="x", padx=10, pady=6)

        tk.Radiobutton(mode_box, text="Mode A: Guess the note", variable=self.mode_var, value="A").pack(anchor="w", padx=10, pady=2)
        tk.Radiobutton(mode_box, text="Mode B: Find all positions", variable=self.mode_var, value="B").pack(anchor="w", padx=10, pady=2)
        tk.Radiobutton(mode_box, text="Adaptive (Mode A): Focus weak positions", variable=self.mode_var, value="ADAPT").pack(anchor="w", padx=10, pady=2)
        tk.Radiobutton(mode_box, text="Practice Session (timed, Adaptive Notes)", variable=self.mode_var, value="PRACTICE").pack(anchor="w", padx=10, pady=2)

        settings = tk.LabelFrame(self, text="Settings")
        settings.pack(fill="x", padx=10, pady=6)

        # instrument
        row0 = tk.Frame(settings)
        row0.pack(fill="x", padx=10, pady=4)
        tk.Label(row0, text="Instrument:").pack(side="left")
        tk.OptionMenu(row0, self.num_strings_var, "6", "7").pack(side="left", padx=8)

        # tuning dropdown (dynamic)
        row_t = tk.Frame(settings)
        row_t.pack(fill="x", padx=10, pady=4)
        tk.Label(row_t, text="Tuning:").pack(side="left")
        self._tuning_option = tk.OptionMenu(row_t, self.tuning_var, "")
        self._tuning_option.pack(side="left", padx=8)

        # custom tuning entry
        row_c = tk.Frame(settings)
        row_c.pack(fill="x", padx=10, pady=4)
        tk.Label(row_c, text="Custom tuning (lowest → highest):").pack(side="left")
        self.custom_entry = tk.Entry(row_c, textvariable=self.custom_tuning_var, width=32)
        self.custom_entry.pack(side="left", padx=8)
        self.custom_hint = tk.Label(row_c, text="", fg="gray")
        self.custom_hint.pack(side="left")

        # display
        rowd = tk.Frame(settings)
        rowd.pack(fill="x", padx=10, pady=4)
        tk.Label(rowd, text="Display notes as:").pack(side="left")
        tk.OptionMenu(rowd, self.display_var, "Sharps", "Flats").pack(side="left", padx=8)

        # questions
        row1 = tk.Frame(settings)
        row1.pack(fill="x", padx=10, pady=4)
        tk.Label(row1, text="Number of questions (A/B/ADAPT):").pack(side="left")
        tk.Entry(row1, textvariable=self.questions_var, width=8).pack(side="left", padx=8)

        # practice minutes
        row2 = tk.Frame(settings)
        row2.pack(fill="x", padx=10, pady=4)
        tk.Label(row2, text="Practice minutes (PRACTICE):").pack(side="left")
        tk.Entry(row2, textvariable=self.practice_minutes_var, width=8).pack(side="left", padx=8)

        # max fret
        row3 = tk.Frame(settings)
        row3.pack(fill="x", padx=10, pady=4)
        tk.Label(row3, text="Max fret (0–24):").pack(side="left")
        tk.Entry(row3, textvariable=self.max_fret_var, width=8).pack(side="left", padx=8)

        btns = tk.Frame(self)
        btns.pack(pady=10)
        tk.Button(btns, text="Start", width=12, command=self._start_clicked).pack(side="left", padx=6)
        tk.Button(btns, text="Heatmap", width=12, command=self._heatmap_clicked).pack(side="left", padx=6)
        tk.Button(btns, text="Show stats", width=12, command=self._show_stats).pack(side="left", padx=6)
        tk.Button(btns, text="Reset stats", width=12, command=self._reset_stats).pack(side="left", padx=6)
        tk.Button(btns, text="Quit", width=12, command=self._quit).pack(side="left", padx=6)

        hint = tk.Label(self, text="Strings: 1 (top, highest) ... N (bottom, lowest).", fg="gray")
        hint.pack(pady=(5, 0))

        # populate tuning menu initially + on instrument change
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

        menu = self._tuning_option["menu"]
        menu.delete(0, "end")
        for name in options:
            menu.add_command(label=name, command=tk._setit(self.tuning_var, name))

        cur = self.tuning_var.get()
        if cur not in options:
            self.tuning_var.set(get_default_tuning_name(n))

        # update default custom text example
        if n == 7:
            self.custom_tuning_var.set("B E A D G B E")
        else:
            self.custom_tuning_var.set("E A D G B E")

        self._refresh_custom_visibility()

    def _refresh_custom_visibility(self) -> None:
        n = self._get_num_strings()
        is_custom = (self.tuning_var.get().strip() == CUSTOM_TUNING_NAME)

        state = tk.NORMAL if is_custom else tk.DISABLED
        self.custom_entry.config(state=state)
        if n == 7:
            self.custom_hint.config(text="e.g. B E A D G B E")
        else:
            self.custom_hint.config(text="e.g. E A D G B E")

    def _start_clicked(self) -> None:
        try:
            mode = self.mode_var.get().strip().upper()
            num_questions = self._parse_int(self.questions_var.get(), min_value=1, max_value=200, field_name="Number of questions")
            practice_minutes = self._parse_int(self.practice_minutes_var.get(), min_value=1, max_value=120, field_name="Practice minutes")
            max_fret = self._parse_int(self.max_fret_var.get(), min_value=0, max_value=24, field_name="Max fret")
        except ValueError as e:
            messagebox.showerror("Invalid settings", str(e))
            return

        num_strings = self._get_num_strings()
        tuning_name = self.tuning_var.get().strip()
        display = self.display_var.get().strip()
        prefer_flats = (display.lower() == "flats")

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
