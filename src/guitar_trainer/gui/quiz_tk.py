from __future__ import annotations

import random
import tkinter as tk
from tkinter import ttk

from guitar_trainer.core.adaptive import choose_adaptive_position
from guitar_trainer.core.mapping import positions_for_note
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
