import tkinter as tk
from tkinter import messagebox

from guitar_trainer.core.stats import Stats, load_stats, save_stats
from guitar_trainer.core.tuning import TUNING_PRESETS, DEFAULT_TUNING_NAME


class MenuFrame(tk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        *,
        stats_path: str,
        on_start: callable,      # callback(mode, num_questions, max_fret, tuning_name, practice_minutes, prefer_flats)
        on_heatmap: callable,    # callback(max_fret)
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
        self.tuning_var = tk.StringVar(value=DEFAULT_TUNING_NAME)

        # New: display style
        self.display_var = tk.StringVar(value="Sharps")  # or "Flats"

        title = tk.Label(self, text="Guitar Trainer – Start Menu", font=("Arial", 14))
        title.pack(pady=(0, 10))

        mode_box = tk.LabelFrame(self, text="Mode")
        mode_box.pack(fill="x", padx=10, pady=6)

        tk.Radiobutton(mode_box, text="Mode A: Guess the note", variable=self.mode_var, value="A").pack(
            anchor="w", padx=10, pady=2
        )
        tk.Radiobutton(mode_box, text="Mode B: Find all positions", variable=self.mode_var, value="B").pack(
            anchor="w", padx=10, pady=2
        )
        tk.Radiobutton(mode_box, text="Adaptive (Mode A): Focus weak positions", variable=self.mode_var, value="ADAPT").pack(
            anchor="w", padx=10, pady=2
        )
        tk.Radiobutton(mode_box, text="Practice Session (timed, Adaptive Notes)", variable=self.mode_var, value="PRACTICE").pack(
            anchor="w", padx=10, pady=2
        )

        settings = tk.LabelFrame(self, text="Settings")
        settings.pack(fill="x", padx=10, pady=6)

        row1 = tk.Frame(settings)
        row1.pack(fill="x", padx=10, pady=4)
        tk.Label(row1, text="Number of questions (A/B/ADAPT):").pack(side="left")
        tk.Entry(row1, textvariable=self.questions_var, width=8).pack(side="left", padx=8)

        row2 = tk.Frame(settings)
        row2.pack(fill="x", padx=10, pady=4)
        tk.Label(row2, text="Practice minutes (PRACTICE):").pack(side="left")
        tk.Entry(row2, textvariable=self.practice_minutes_var, width=8).pack(side="left", padx=8)

        row3 = tk.Frame(settings)
        row3.pack(fill="x", padx=10, pady=4)
        tk.Label(row3, text="Max fret (0–24):").pack(side="left")
        tk.Entry(row3, textvariable=self.max_fret_var, width=8).pack(side="left", padx=8)

        row4 = tk.Frame(settings)
        row4.pack(fill="x", padx=10, pady=4)
        tk.Label(row4, text="Tuning:").pack(side="left")
        options = list(TUNING_PRESETS.keys())
        tk.OptionMenu(row4, self.tuning_var, *options).pack(side="left", padx=8)

        # New: display
        row5 = tk.Frame(settings)
        row5.pack(fill="x", padx=10, pady=4)
        tk.Label(row5, text="Display notes as:").pack(side="left")
        tk.OptionMenu(row5, self.display_var, "Sharps", "Flats").pack(side="left", padx=8)

        btns = tk.Frame(self)
        btns.pack(pady=10)

        tk.Button(btns, text="Start", width=12, command=self._start_clicked).pack(side="left", padx=6)
        tk.Button(btns, text="Heatmap", width=12, command=self._heatmap_clicked).pack(side="left", padx=6)
        tk.Button(btns, text="Show stats", width=12, command=self._show_stats).pack(side="left", padx=6)
        tk.Button(btns, text="Reset stats", width=12, command=self._reset_stats).pack(side="left", padx=6)
        tk.Button(btns, text="Quit", width=12, command=self._quit).pack(side="left", padx=6)

        hint = tk.Label(
            self,
            text="Strings: 1 (top, high e) ... 6 (bottom, low E).",
            fg="gray",
        )
        hint.pack(pady=(5, 0))

    def _parse_int(self, value: str, *, min_value: int, max_value: int, field_name: str) -> int:
        value = value.strip()
        try:
            x = int(value)
        except ValueError:
            raise ValueError(f"{field_name} must be an integer.")
        if x < min_value or x > max_value:
            raise ValueError(f"{field_name} must be between {min_value} and {max_value}.")
        return x

    def _start_clicked(self) -> None:
        try:
            mode = self.mode_var.get().strip().upper()
            num_questions = self._parse_int(self.questions_var.get(), min_value=1, max_value=200, field_name="Number of questions")
            practice_minutes = self._parse_int(self.practice_minutes_var.get(), min_value=1, max_value=120, field_name="Practice minutes")
            max_fret = self._parse_int(self.max_fret_var.get(), min_value=0, max_value=24, field_name="Max fret")
        except ValueError as e:
            messagebox.showerror("Invalid settings", str(e))
            return

        tuning_name = self.tuning_var.get().strip()
        if tuning_name not in TUNING_PRESETS:
            tuning_name = DEFAULT_TUNING_NAME

        display = self.display_var.get().strip()
        prefer_flats = (display.lower() == "flats")

        if mode not in {"A", "B", "ADAPT", "PRACTICE"}:
            messagebox.showerror("Invalid mode", "Mode must be A, B, ADAPT or PRACTICE.")
            return

        self.on_start(mode, num_questions, max_fret, tuning_name, practice_minutes, prefer_flats)

    def _heatmap_clicked(self) -> None:
        try:
            max_fret = self._parse_int(self.max_fret_var.get(), min_value=0, max_value=24, field_name="Max fret")
        except ValueError as e:
            messagebox.showerror("Invalid settings", str(e))
            return
        self.on_heatmap(max_fret)

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
