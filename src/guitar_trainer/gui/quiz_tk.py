import random
import tkinter as tk

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
from guitar_trainer.core.tuning import STANDARD_TUNING
from guitar_trainer.gui.fretboard import Fretboard, Position


class NoteQuizFrame(tk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        *,
        stats: Stats,
        stats_path: str,
        num_questions: int = 10,
        max_fret: int = 12,
        tuning: list[int] = STANDARD_TUNING,
        tuning_name: str = "E Standard",
        rng_seed: int | None = None,
        on_back=None,
    ) -> None:
        super().__init__(master)

        self.stats = stats
        self.stats_path = stats_path
        self.num_questions = num_questions
        self.max_fret = max_fret
        self.tuning = tuning
        self.tuning_name = tuning_name

        self.rng = random.Random(rng_seed) if rng_seed is not None else random.Random()

        self.on_back = on_back
        self.current_index = 0
        self.score = 0
        self.current_position: Position | None = None
        self.current_correct_name: str | None = None

        header = tk.Frame(self)
        header.pack(fill="x", pady=(0, 8))

        tk.Label(header, text=f"Mode A: Guess the note  |  {self.tuning_name}", font=("Arial", 13)).pack(side="left")
        if self.on_back:
            tk.Button(header, text="Back to menu", command=self._back).pack(side="right")

        self.progress = tk.Label(self, text="")
        self.progress.pack(pady=(0, 6))

        self.fretboard = Fretboard(self, num_frets=max_fret, tuning=self.tuning, enable_click_reporting=False)
        self.fretboard.pack(fill="both", expand=True, padx=10, pady=10)

        entry_row = tk.Frame(self)
        entry_row.pack(pady=(6, 2))

        tk.Label(entry_row, text="Your answer:").pack(side=tk.LEFT)
        self.answer_var = tk.StringVar()
        self.answer_entry = tk.Entry(entry_row, textvariable=self.answer_var, width=10)
        self.answer_entry.pack(side=tk.LEFT, padx=(6, 0))

        self.submit_btn = tk.Button(entry_row, text="Submit", command=self.submit_answer)
        self.submit_btn.pack(side=tk.LEFT, padx=(8, 0))

        self.feedback = tk.Label(self, text="")
        self.feedback.pack(pady=(6, 0))

        self.answer_entry.bind("<Return>", lambda _e: self.submit_answer())
        self.next_question()

    def _back(self) -> None:
        save_stats(self.stats_path, self.stats)
        self.on_back()

    def update_progress(self) -> None:
        self.progress.config(
            text=f"Question {self.current_index}/{self.num_questions} | Score: {self.score}/{self.current_index}"
        )

    def pick_next_position(self) -> Position:
        return random_position(self.max_fret, rng=self.rng)

    def next_question(self) -> None:
        if self.current_index >= self.num_questions:
            self.finish()
            return

        self.current_index += 1
        self.update_progress()

        self.current_position = self.pick_next_position()
        self.current_correct_name = question_name_at_position(self.current_position, tuning=self.tuning)

        self.fretboard.highlight_position(self.current_position)
        self.answer_var.set("")
        self.feedback.config(text="")
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
            self.feedback.config(text="✅ Correct")
        else:
            self.feedback.config(text=f"❌ Wrong. Correct: {self.current_correct_name}")

        self.update_progress()
        self.after(600, self.next_question)

    def finish(self) -> None:
        self.fretboard.clear_single_highlight()
        save_stats(self.stats_path, self.stats)
        self.progress.config(text=f"Finished | Score: {self.score}/{self.num_questions}")
        self.feedback.config(text="Statistics saved.")
        self.submit_btn.config(state=tk.DISABLED)
        self.answer_entry.config(state=tk.DISABLED)


class AdaptiveNoteQuizFrame(NoteQuizFrame):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        tk.Label(self, text="Adaptive mode: focuses weak / unseen positions", fg="gray").pack(pady=(0, 6))

    def pick_next_position(self) -> Position:
        return choose_adaptive_position(self.stats, self.max_fret, self.rng)


class PositionsQuizFrame(tk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        *,
        stats: Stats,
        stats_path: str,
        num_questions: int = 5,
        max_fret: int = 12,
        tuning: list[int] = STANDARD_TUNING,
        tuning_name: str = "E Standard",
        rng_seed: int | None = None,
        on_back=None,
    ) -> None:
        super().__init__(master)

        self.stats = stats
        self.stats_path = stats_path
        self.num_questions = num_questions
        self.max_fret = max_fret
        self.tuning = tuning
        self.tuning_name = tuning_name

        self.rng = random.Random(rng_seed) if rng_seed is not None else random.Random()
        self.on_back = on_back

        self.current_index = 0
        self.score = 0
        self.locked = False

        self.target_note_index: int | None = None
        self.target_note_name: str | None = None
        self.selected: set[Position] = set()

        header = tk.Frame(self)
        header.pack(fill="x", pady=(0, 8))

        tk.Label(header, text=f"Mode B: Find all positions  |  {self.tuning_name}", font=("Arial", 13)).pack(side="left")
        if self.on_back:
            tk.Button(header, text="Back to menu", command=self._back).pack(side="right")

        self.progress = tk.Label(self, text="")
        self.progress.pack(pady=(0, 6))

        self.task = tk.Label(self, text="")
        self.task.pack(pady=(0, 6))

        self.fretboard = Fretboard(self, num_frets=max_fret, tuning=self.tuning, enable_click_reporting=True)
        self.fretboard.set_click_callback(self.on_fretboard_click)
        self.fretboard.pack(fill="both", expand=True, padx=10, pady=10)

        controls = tk.Frame(self)
        controls.pack(pady=(6, 2))

        self.clear_btn = tk.Button(controls, text="Clear", command=self.clear_selection)
        self.clear_btn.pack(side=tk.LEFT)

        self.submit_btn = tk.Button(controls, text="Submit", command=self.submit_selection)
        self.submit_btn.pack(side=tk.LEFT, padx=(8, 0))

        self.feedback = tk.Label(self, text="")
        self.feedback.pack(pady=(6, 0))

        self.next_question()

    def _back(self) -> None:
        save_stats(self.stats_path, self.stats)
        self.on_back()

    def update_progress(self) -> None:
        self.progress.config(
            text=f"Question {self.current_index}/{self.num_questions} | Score: {self.score}/{self.current_index}"
        )

    def next_question(self) -> None:
        if self.current_index >= self.num_questions:
            self.finish()
            return

        self.locked = False
        self.current_index += 1
        self.selected.clear()
        self.fretboard.clear_all_cell_markers()
        self.feedback.config(text="")
        self.update_progress()

        self.target_note_index = self.rng.randint(0, 11)
        self.target_note_name = index_to_name(self.target_note_index)

        self.task.config(text=f"Click ALL positions for note {self.target_note_name} (up to fret {self.max_fret})")

    def clear_selection(self) -> None:
        if self.locked:
            return
        self.selected.clear()
        self.fretboard.clear_all_cell_markers()
        self.feedback.config(text="")

    def on_fretboard_click(self, position: Position) -> None:
        if self.locked:
            return

        if position in self.selected:
            self.selected.remove(position)
            self.fretboard.clear_cell_marker(position)
        else:
            self.selected.add(position)
            self.fretboard.set_cell_marker(position, outline="blue")

        self.feedback.config(text=f"Selected: {len(self.selected)}")

    def submit_selection(self) -> None:
        if self.locked or self.target_note_index is None:
            return

        correct = check_positions_answer(
            self.target_note_index,
            self.max_fret,
            list(self.selected),
            tuning=self.tuning,
        )

        self.stats.record_attempt_mode_b(
            correct=correct,
            note_name=self.target_note_name,
        )

        correct_positions = set(positions_for_note(self.target_note_index, self.max_fret, tuning=self.tuning))

        self.locked = True
        self.fretboard.clear_all_cell_markers()

        if correct:
            self.score += 1
            self.feedback.config(text="✅ Correct")
            self.after(700, self.next_question)
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

        self.feedback.config(
            text=f"❌ Wrong | correct: {len(correct_positions)} | selected: {len(self.selected)} | wrong: {len(wrong)} | missing: {len(missing)}"
        )

        self.after(1400, self.next_question)

    def finish(self) -> None:
        self.fretboard.clear_all_cell_markers()
        save_stats(self.stats_path, self.stats)
        self.progress.config(text=f"Finished | Score: {self.score}/{self.num_questions}")
        self.task.config(text="")
        self.feedback.config(text="Statistics saved.")
        self.submit_btn.config(state=tk.DISABLED)
        self.clear_btn.config(state=tk.DISABLED)
        self.locked = True
