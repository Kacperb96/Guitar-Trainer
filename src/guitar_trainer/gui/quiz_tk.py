from __future__ import annotations

import random
import tkinter as tk
from tkinter import ttk

from guitar_trainer.core.adaptive import choose_adaptive_position
from guitar_trainer.core.mapping import positions_for_note, note_index_at
from guitar_trainer.core.notes import index_to_name
from guitar_trainer.core.quiz import (
    random_position,
    question_name_at_position,
    check_note_name_answer,
    check_positions_answer,
)
from guitar_trainer.core.stats import Stats, save_stats
from guitar_trainer.gui.fretboard import Fretboard, Position


class NoteQuizFrame(ttk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        *,
        stats: Stats,
        stats_path: str,
        num_questions: int = 10,
        max_fret: int = 12,
        tuning: list[int],
        tuning_name: str,
        prefer_flats: bool = False,
        rng_seed: int | None = None,
        on_back=None,
    ) -> None:
        super().__init__(master)

        self.stats = stats
        self.stats_path = stats_path
        self.num_questions = int(num_questions)
        self.max_fret = int(max_fret)
        self.tuning = list(tuning)
        self.tuning_name = tuning_name
        self.prefer_flats = bool(prefer_flats)
        self.num_strings = len(self.tuning)

        self.rng = random.Random(rng_seed) if rng_seed is not None else random.Random()
        self.on_back = on_back

        self.current_index = 0
        self.score = 0
        self.current_position: Position | None = None
        self.current_correct_name: str | None = None

        # Header
        header = ttk.Frame(self)
        header.pack(fill="x", pady=(0, 10))
        header.columnconfigure(0, weight=1)

        display = "Flats" if self.prefer_flats else "Sharps"
        ttk.Label(header, text=f"Mode A", style="H2.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(header, text=f"{tuning_name} • {display}", style="Hint.TLabel").grid(row=1, column=0, sticky="w", pady=(2, 0))

        if self.on_back:
            ttk.Button(header, text="Back", command=self._back).grid(row=0, column=1, rowspan=2, sticky="e")

        self.progress = ttk.Label(self, text="", style="Muted.TLabel")
        self.progress.pack(anchor="w", pady=(0, 8))

        # Fretboard
        self.fretboard = Fretboard(self, num_frets=self.max_fret, tuning=self.tuning, enable_click_reporting=False)
        self.fretboard.pack(fill="both", expand=True, padx=12, pady=12)

        # Controls under fretboard
        controls = ttk.Frame(self)
        controls.pack(fill="x", pady=(0, 8))
        controls.columnconfigure(0, weight=1)

        self._fret_nums_btn = ttk.Button(controls, text="Hide fret numbers", command=self._toggle_fret_numbers)
        self._fret_nums_btn.grid(row=0, column=0, sticky="w")

        # Answer row
        entry_row = ttk.Frame(self)
        entry_row.pack(fill="x", pady=(4, 2))
        ttk.Label(entry_row, text="Your answer:").pack(side="left")

        self.answer_var = tk.StringVar()
        self.answer_entry = ttk.Entry(entry_row, textvariable=self.answer_var, width=12)
        self.answer_entry.pack(side="left", padx=(8, 0))

        self.submit_btn = ttk.Button(entry_row, text="Submit", style="Primary.TButton", command=self.submit_answer)
        self.submit_btn.pack(side="left", padx=(10, 0))

        self.feedback = ttk.Label(self, text="", style="Hint.TLabel")
        self.feedback.pack(anchor="w", pady=(8, 0))

        self.answer_entry.bind("<Return>", lambda _e: self.submit_answer())
        self.next_question()

    def _toggle_fret_numbers(self) -> None:
        is_showing = self.fretboard.toggle_fret_numbers()
        self._fret_nums_btn.configure(text="Hide fret numbers" if is_showing else "Show fret numbers")

    def _back(self) -> None:
        save_stats(self.stats_path, self.stats)
        self.on_back()

    def update_progress(self) -> None:
        self.progress.configure(
            text=f"Question {self.current_index}/{self.num_questions} • Score {self.score}/{max(1, self.current_index)}"
        )

    def pick_next_position(self) -> Position:
        return random_position(self.max_fret, tuning=self.tuning, rng=self.rng)

    def next_question(self) -> None:
        if self.current_index >= self.num_questions:
            self.finish()
            return

        self.current_index += 1
        self.update_progress()

        self.current_position = self.pick_next_position()
        self.current_correct_name = question_name_at_position(
            self.current_position,
            tuning=self.tuning,
            prefer_flats=self.prefer_flats,
        )

        self.fretboard.highlight_position(self.current_position)
        self.answer_var.set("")
        self.feedback.configure(text="", style="Hint.TLabel")
        self.answer_entry.focus_set()

    def submit_answer(self) -> None:
        if not self.current_position or not self.current_correct_name:
            return

        user_answer = self.answer_var.get()
        correct = check_note_name_answer(self.current_correct_name, user_answer)

        s, f = self.current_position
        self.stats.record_position_attempt(
            correct=correct,
            note_name=self.current_correct_name,
            string_index=s,
            fret=f,
        )

        if correct:
            self.score += 1
            self.feedback.configure(text="Correct ✓", style="Success.TLabel")
        else:
            self.feedback.configure(text=f"Wrong ✕  Correct: {self.current_correct_name}", style="DangerText.TLabel")

        self.update_progress()
        self.after(650, self.next_question)

    def finish(self) -> None:
        self.fretboard.clear_single_highlight()
        save_stats(self.stats_path, self.stats)
        self.progress.configure(text=f"Finished • Score {self.score}/{self.num_questions}")
        self.feedback.configure(text="Statistics saved.", style="Hint.TLabel")
        self.submit_btn.configure(state="disabled")
        self.answer_entry.configure(state="disabled")


class AdaptiveNoteQuizFrame(NoteQuizFrame):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        hint = ttk.Label(self, text="Adaptive: focuses on weak / unseen positions", style="Hint.TLabel")
        hint.pack(anchor="w", pady=(0, 6))

    def pick_next_position(self) -> Position:
        # keep original signature used in your project
        return choose_adaptive_position(self.stats, self.max_fret, self.rng, num_strings=self.num_strings)


class PositionsQuizFrame(ttk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        *,
        stats: Stats,
        stats_path: str,
        num_questions: int = 5,
        max_fret: int = 12,
        tuning: list[int],
        tuning_name: str,
        prefer_flats: bool = False,
        rng_seed: int | None = None,
        on_back=None,
    ) -> None:
        super().__init__(master)

        self.stats = stats
        self.stats_path = stats_path
        self.num_questions = int(num_questions)
        self.max_fret = int(max_fret)
        self.tuning = list(tuning)
        self.tuning_name = tuning_name
        self.prefer_flats = bool(prefer_flats)
        self.num_strings = len(self.tuning)

        self.rng = random.Random(rng_seed) if rng_seed is not None else random.Random()
        self.on_back = on_back

        self.current_index = 0
        self.score = 0
        self.locked = False

        self.target_note_index: int | None = None
        self.target_note_name: str | None = None
        self.selected: set[Position] = set()

        # Header
        header = ttk.Frame(self)
        header.pack(fill="x", pady=(0, 10))
        header.columnconfigure(0, weight=1)

        display = "Flats" if self.prefer_flats else "Sharps"
        ttk.Label(header, text="Mode B", style="H2.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(header, text=f"{tuning_name} • {display}", style="Hint.TLabel").grid(row=1, column=0, sticky="w", pady=(2, 0))

        if self.on_back:
            ttk.Button(header, text="Back", command=self._back).grid(row=0, column=1, rowspan=2, sticky="e")

        self.progress = ttk.Label(self, text="", style="Muted.TLabel")
        self.progress.pack(anchor="w", pady=(0, 6))

        self.task = ttk.Label(self, text="", style="Hint.TLabel")
        self.task.pack(anchor="w", pady=(0, 10))

        self.fretboard = Fretboard(self, num_frets=self.max_fret, tuning=self.tuning, enable_click_reporting=True)
        self.fretboard.set_click_callback(self.on_fretboard_click)
        self.fretboard.pack(fill="both", expand=True, padx=12, pady=12)

        controls = ttk.Frame(self)
        controls.pack(fill="x", pady=(6, 2))
        self._fret_nums_btn = ttk.Button(controls, text="Hide fret numbers", command=self._toggle_fret_numbers)
        self._fret_nums_btn.pack(side="left")

        self.clear_btn = ttk.Button(controls, text="Clear", command=self.clear_selection)
        self.clear_btn.pack(side="left", padx=(10, 0))

        self.submit_btn = ttk.Button(controls, text="Submit", style="Primary.TButton", command=self.submit_selection)
        self.submit_btn.pack(side="left", padx=(10, 0))

        self.feedback = ttk.Label(self, text="", style="Hint.TLabel")
        self.feedback.pack(anchor="w", pady=(10, 0))

        self.next_question()

    def _toggle_fret_numbers(self) -> None:
        is_showing = self.fretboard.toggle_fret_numbers()
        self._fret_nums_btn.configure(text="Hide fret numbers" if is_showing else "Show fret numbers")

    def _back(self) -> None:
        save_stats(self.stats_path, self.stats)
        self.on_back()

    def update_progress(self) -> None:
        self.progress.configure(
            text=f"Question {self.current_index}/{self.num_questions} • Score {self.score}/{max(1, self.current_index)}"
        )

    def next_question(self) -> None:
        if self.current_index >= self.num_questions:
            self.finish()
            return

        self.locked = False
        self.current_index += 1
        self.selected.clear()
        self.fretboard.clear_all_cell_markers()
        self.feedback.configure(text="", style="Hint.TLabel")
        self.update_progress()

        self.target_note_index = self.rng.randint(0, 11)
        self.target_note_name = index_to_name(self.target_note_index, prefer_flats=self.prefer_flats)
        self.task.configure(text=f"Click ALL positions for {self.target_note_name} (up to fret {self.max_fret})")

    def clear_selection(self) -> None:
        if self.locked:
            return
        self.selected.clear()
        self.fretboard.clear_all_cell_markers()
        self.feedback.configure(text="", style="Hint.TLabel")

    def on_fretboard_click(self, position: Position) -> None:
        if self.locked:
            return
        if position in self.selected:
            self.selected.remove(position)
            self.fretboard.clear_cell_marker(position)
        else:
            self.selected.add(position)
            self.fretboard.set_cell_marker(position, outline="red")

        self.feedback.configure(text=f"Selected: {len(self.selected)}", style="Hint.TLabel")

    def submit_selection(self) -> None:
        if self.locked or self.target_note_index is None:
            return

        correct = check_positions_answer(self.target_note_index, self.max_fret, list(self.selected), tuning=self.tuning)
        self.stats.record_attempt_mode_b(correct=correct, note_name=self.target_note_name)

        correct_positions = set(positions_for_note(self.target_note_index, self.max_fret, tuning=self.tuning))
        self.locked = True
        self.fretboard.clear_all_cell_markers()

        if correct:
            self.score += 1
            self.feedback.configure(text="Correct ✓", style="Success.TLabel")
            self.after(750, self.next_question)
            return

        wrong = self.selected - correct_positions
        good = self.selected & correct_positions
        missing = correct_positions - self.selected

        for p in good:
            self.fretboard.set_cell_marker(p, outline="green")
        for p in wrong:
            self.fretboard.set_cell_marker(p, outline="red")
        for p in list(missing)[:30]:
            self.fretboard.set_cell_marker(p, outline="orange")

        self.feedback.configure(
            text=f"Wrong ✕  correct: {len(correct_positions)} • selected: {len(self.selected)} • wrong: {len(wrong)} • missing: {len(missing)}",
            style="DangerText.TLabel",
        )
        self.after(1400, self.next_question)

    def finish(self) -> None:
        self.fretboard.clear_all_cell_markers()
        save_stats(self.stats_path, self.stats)
        self.progress.configure(text=f"Finished • Score {self.score}/{self.num_questions}")
        self.task.configure(text="")
        self.feedback.configure(text="Statistics saved.", style="Hint.TLabel")
        self.submit_btn.configure(state="disabled")
        self.clear_btn.configure(state="disabled")
        self.locked = True


class StringOnStringQuizFrame(ttk.Frame):
    """Mode C: pick the correct fret for a target note on a highlighted string."""

    def __init__(
        self,
        master: tk.Misc,
        *,
        stats: Stats,
        stats_path: str,
        num_questions: int = 10,
        max_fret: int = 12,
        tuning: list[int],
        tuning_name: str,
        prefer_flats: bool = False,
        include_strings: list[int] | None = None,
        rng_seed: int | None = None,
        on_back=None,
    ) -> None:
        super().__init__(master)

        self.stats = stats
        self.stats_path = stats_path
        self.num_questions = int(num_questions)
        self.max_fret = int(max_fret)
        self.tuning = list(tuning)
        self.tuning_name = tuning_name
        self.prefer_flats = bool(prefer_flats)
        self.num_strings = len(self.tuning)

        self.include_strings = (
            sorted({int(x) for x in include_strings}) if include_strings else list(range(self.num_strings))
        )
        self.include_strings = [s for s in self.include_strings if 0 <= s < self.num_strings]
        if not self.include_strings:
            self.include_strings = list(range(self.num_strings))

        self.rng = random.Random(rng_seed) if rng_seed is not None else random.Random()
        self.on_back = on_back

        self.current_index = 0
        self.score = 0
        self.locked = False

        self.target_note_index: int | None = None
        self.target_note_name: str | None = None
        self.target_string: int | None = None

        # Header
        header = ttk.Frame(self)
        header.pack(fill="x", pady=(0, 10))
        header.columnconfigure(0, weight=1)

        display = "Flats" if self.prefer_flats else "Sharps"
        ttk.Label(header, text="Mode C", style="H2.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(header, text=f"{tuning_name} • {display}", style="Hint.TLabel").grid(
            row=1, column=0, sticky="w", pady=(2, 0)
        )

        if self.on_back:
            ttk.Button(header, text="Back", command=self._back).grid(row=0, column=1, rowspan=2, sticky="e")

        self.task = ttk.Label(self, text="", style="Hint.TLabel")
        self.task.pack(anchor="w", pady=(0, 6))

        self.progress = ttk.Label(self, text="", style="Muted.TLabel")
        self.progress.pack(anchor="w", pady=(0, 8))

        # Fretboard
        self.fretboard = Fretboard(self, num_frets=self.max_fret, tuning=self.tuning, enable_click_reporting=True)
        self.fretboard.set_click_callback(self.on_fretboard_click)
        self.fretboard.pack(fill="both", expand=True, padx=12, pady=12)

        controls = ttk.Frame(self)
        controls.pack(fill="x", pady=(0, 8))
        controls.columnconfigure(0, weight=1)

        self._fret_nums_btn = ttk.Button(controls, text="Hide fret numbers", command=self._toggle_fret_numbers)
        self._fret_nums_btn.grid(row=0, column=0, sticky="w")

        self.reset_btn = ttk.Button(controls, text="Reset", command=self.reset_progress)
        self.reset_btn.grid(row=0, column=1, sticky="w", padx=(10, 0))

        # Options (simple, like your screenshot)
        opts = ttk.Frame(self)
        opts.pack(fill="x", pady=(6, 0))
        opts.columnconfigure(0, weight=1)

        self._prefer_flats_var = tk.BooleanVar(value=self.prefer_flats)
        ttk.Checkbutton(
            opts,
            text="Include Flats/sharps:",
            variable=self._prefer_flats_var,
            command=self._on_toggle_flats,
        ).grid(row=0, column=0, sticky="w")

        ttk.Label(opts, text="Number of frets:").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self._max_fret_var = tk.IntVar(value=self.max_fret)
        max_fret_box = ttk.Combobox(
            opts,
            textvariable=self._max_fret_var,
            values=[6, 8, 10, 12, 15, 18, 21, 24],
            width=6,
            state="readonly",
        )
        max_fret_box.grid(row=1, column=0, sticky="e", pady=(6, 0))
        max_fret_box.bind("<<ComboboxSelected>>", lambda _e: self._on_change_max_fret())

        ttk.Label(opts, text="Include strings:").grid(row=2, column=0, sticky="w", pady=(10, 0))
        str_row = ttk.Frame(opts)
        str_row.grid(row=3, column=0, sticky="w", pady=(4, 0))

        self._string_vars: list[tk.BooleanVar] = []
        for i in range(self.num_strings):
            v = tk.BooleanVar(value=(i in self.include_strings))
            self._string_vars.append(v)
            ttk.Checkbutton(
                str_row,
                text=str(i + 1),
                variable=v,
                command=self._on_change_included_strings,
            ).pack(side="left", padx=2)

        self.feedback = ttk.Label(self, text="", style="Hint.TLabel")
        self.feedback.pack(anchor="w", pady=(10, 0))

        self.next_question()

    def _toggle_fret_numbers(self) -> None:
        is_showing = self.fretboard.toggle_fret_numbers()
        self._fret_nums_btn.configure(text="Hide fret numbers" if is_showing else "Show fret numbers")

    def _on_toggle_flats(self) -> None:
        self.prefer_flats = bool(self._prefer_flats_var.get())
        if self.target_note_index is not None:
            self.target_note_name = index_to_name(self.target_note_index, prefer_flats=self.prefer_flats)
            self._update_task_text()

    def _on_change_max_fret(self) -> None:
        self.max_fret = int(self._max_fret_var.get())
        self.fretboard.destroy()
        self.fretboard = Fretboard(self, num_frets=self.max_fret, tuning=self.tuning, enable_click_reporting=True)
        self.fretboard.set_click_callback(self.on_fretboard_click)
        # place it in the same region (above controls)
        self.fretboard.pack(fill="both", expand=True, padx=12, pady=12, before=self.reset_btn.master)
        self.locked = False
        self.feedback.configure(text="", style="Hint.TLabel")
        self.next_question()

    def _on_change_included_strings(self) -> None:
        included = [i for i, v in enumerate(self._string_vars) if bool(v.get())]
        if not included:
            self._string_vars[0].set(True)
            included = [0]
        self.include_strings = included
        if self.target_string is not None and self.target_string not in self.include_strings:
            self.next_question()

    def _back(self) -> None:
        save_stats(self.stats_path, self.stats)
        self.on_back()

    def reset_progress(self) -> None:
        self.current_index = 0
        self.score = 0
        self.locked = False
        self.feedback.configure(text="", style="Hint.TLabel")
        self.fretboard.clear_all_cell_markers()
        self.next_question()

    def _update_task_text(self) -> None:
        if self.target_note_name is None:
            self.task.configure(text="")
            return
        if self.target_string is None:
            s_label = "?"
        else:
            gui_row = (self.num_strings - 1) - self.target_string
            s_label = str(gui_row + 1)
        self.task.configure(text=f"Select note on the highlighted string (string {s_label}): {self.target_note_name}")

    def update_progress(self) -> None:
        answered = max(0, self.current_index - 1)
        pct = int(100 * self.score / answered) if answered else 0
        self.progress.configure(text=f"{self.score} / {answered} ({pct}%)")

    def next_question(self) -> None:
        if self.current_index >= self.num_questions:
            self.finish()
            return

        self.locked = False
        self.current_index += 1

        self.fretboard.clear_all_cell_markers()

        self.target_note_index = self.rng.randint(0, 11)
        self.target_note_name = index_to_name(self.target_note_index, prefer_flats=self.prefer_flats)
        self.target_string = self.rng.choice(self.include_strings)

        self.fretboard.set_highlighted_string(self.target_string)
        self._update_task_text()
        self.update_progress()
        self.feedback.configure(text="", style="Hint.TLabel")

    def on_fretboard_click(self, position: Position) -> None:
        if self.locked or self.target_note_index is None or self.target_string is None or self.target_note_name is None:
            return

        s, f = position
        if s != self.target_string:
            self.feedback.configure(text="Click the highlighted string.", style="Hint.TLabel")
            return

        clicked_idx = note_index_at(s, f, tuning=self.tuning)
        correct = clicked_idx == int(self.target_note_index)

        self.stats.record_position_attempt(
            correct=correct,
            note_name=self.target_note_name,
            string_index=s,
            fret=f,
            mode="C",
        )

        self.locked = True
        self.fretboard.clear_all_cell_markers()

        if correct:
            self.score += 1
            self.fretboard.set_cell_marker((s, f), outline="green")
            self.feedback.configure(text="Correct ✓", style="Success.TLabel")
            self.update_progress()
            self.after(700, self.next_question)
            return

        self.fretboard.set_cell_marker((s, f), outline="red")
        correct_positions = [
            p for p in positions_for_note(self.target_note_index, self.max_fret, tuning=self.tuning) if p[0] == s
        ]
        for p in correct_positions:
            self.fretboard.set_cell_marker(p, outline="orange")

        if correct_positions:
            frets = sorted({pf for _s, pf in correct_positions})
            self.feedback.configure(
                text=f"Wrong ✕  Correct fret(s): {', '.join(map(str, frets))}",
                style="DangerText.TLabel",
            )
        else:
            self.feedback.configure(text="Wrong ✕  (No occurrences in range)", style="DangerText.TLabel")

        self.update_progress()
        self.after(1200, self.next_question)

    def finish(self) -> None:
        self.fretboard.clear_all_cell_markers()
        self.fretboard.clear_highlighted_string()
        save_stats(self.stats_path, self.stats)
        self.task.configure(text="")
        self.progress.configure(text=f"Finished • Score {self.score}/{self.num_questions}")
        self.feedback.configure(text="Statistics saved.", style="Hint.TLabel")
        self.locked = True
        self.reset_btn.configure(state="disabled")
