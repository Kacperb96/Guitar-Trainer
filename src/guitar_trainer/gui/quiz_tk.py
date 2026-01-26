import random
import tkinter as tk

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


class NoteQuizFrame(tk.Frame):
    """
    GUI Mode A:
    - show a dot at a random (string,fret)
    - user types note name (e.g. F#) and submits
    - shows feedback and keeps score
    - updates Stats and saves at the end
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        stats: Stats,
        stats_path: str,
        num_questions: int = 10,
        max_fret: int = 12,
        rng_seed: int | None = None,
    ) -> None:
        super().__init__(master)

        self.stats = stats
        self.stats_path = stats_path
        self.num_questions = num_questions
        self.max_fret = max_fret
        self.rng = random.Random(rng_seed) if rng_seed is not None else random.Random()

        self.current_index = 0
        self.score = 0
        self.current_position: Position | None = None
        self.current_correct_name: str | None = None

        self.header = tk.Label(self, text="Guitar Trainer – GUI Mode A (Guess the note)")
        self.header.pack(pady=(0, 8))

        self.progress = tk.Label(self, text="Question 0/0 | Score: 0/0")
        self.progress.pack(pady=(0, 6))

        self.fretboard = Fretboard(self, num_frets=max_fret, enable_click_reporting=False)
        self.fretboard.pack(padx=10, pady=10)

        entry_row = tk.Frame(self)
        entry_row.pack(pady=(6, 2))

        tk.Label(entry_row, text="Your answer: ").pack(side=tk.LEFT)
        self.answer_var = tk.StringVar()
        self.answer_entry = tk.Entry(entry_row, textvariable=self.answer_var, width=10)
        self.answer_entry.pack(side=tk.LEFT)

        self.submit_btn = tk.Button(entry_row, text="Submit", command=self.submit_answer)
        self.submit_btn.pack(side=tk.LEFT, padx=(8, 0))

        self.feedback = tk.Label(self, text="")
        self.feedback.pack(pady=(6, 0))

        self.answer_entry.bind("<Return>", lambda _e: self.submit_answer())

        self.next_question()

    def update_progress(self) -> None:
        self.progress.config(
            text=f"Question {self.current_index}/{self.num_questions} | Score: {self.score}/{self.current_index}"
        )

    def next_question(self) -> None:
        if self.current_index >= self.num_questions:
            self.finish()
            return

        self.current_index += 1
        self.update_progress()

        self.current_position = random_position(self.max_fret, rng=self.rng)
        self.current_correct_name = question_name_at_position(self.current_position)

        self.fretboard.highlight_position(self.current_position)
        self.feedback.config(text="")
        self.answer_var.set("")
        self.answer_entry.focus_set()

    def submit_answer(self) -> None:
        if self.current_position is None or self.current_correct_name is None:
            return

        user_answer = self.answer_var.get()
        correct = check_note_name_answer(self.current_correct_name, user_answer)

        string_index, _fret = self.current_position
        self.stats.record_attempt(
            mode="A",
            correct=correct,
            note_name=self.current_correct_name,
            string_index=string_index,
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
        self.feedback.config(text="Saved statistics. You can close the window.")
        self.submit_btn.config(state=tk.DISABLED)
        self.answer_entry.config(state=tk.DISABLED)


class PositionsQuizFrame(tk.Frame):
    """
    GUI Mode B:
    - shows a target note name (e.g. F#)
    - user clicks ALL positions on the fretboard up to max_fret
    - submit checks correctness (set equality)
    - shows feedback and highlights results
    - updates Stats and saves at the end
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        stats: Stats,
        stats_path: str,
        num_questions: int = 5,
        max_fret: int = 12,
        rng_seed: int | None = None,
    ) -> None:
        super().__init__(master)

        self.stats = stats
        self.stats_path = stats_path
        self.num_questions = num_questions
        self.max_fret = max_fret
        self.rng = random.Random(rng_seed) if rng_seed is not None else random.Random()

        self.current_index = 0
        self.score = 0

        self.target_note_index: int | None = None
        self.target_note_name: str | None = None

        self.selected: set[Position] = set()
        self.locked = False  # lock clicks while showing results

        self.header = tk.Label(self, text="Guitar Trainer – GUI Mode B (Find all positions)")
        self.header.pack(pady=(0, 8))

        self.progress = tk.Label(self, text="Question 0/0 | Score: 0/0")
        self.progress.pack(pady=(0, 6))

        self.task = tk.Label(self, text="Task: ...")
        self.task.pack(pady=(0, 6))

        self.fretboard = Fretboard(self, num_frets=max_fret, enable_click_reporting=True)
        self.fretboard.set_click_callback(self.on_fretboard_click)
        self.fretboard.pack(padx=10, pady=10)

        controls = tk.Frame(self)
        controls.pack(pady=(6, 2))

        self.clear_btn = tk.Button(controls, text="Clear", command=self.clear_selection)
        self.clear_btn.pack(side=tk.LEFT)

        self.submit_btn = tk.Button(controls, text="Submit", command=self.submit_selection)
        self.submit_btn.pack(side=tk.LEFT, padx=(8, 0))

        self.feedback = tk.Label(self, text="")
        self.feedback.pack(pady=(6, 0))

        self.next_question()

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

        self.task.config(
            text=f"Click ALL positions for note {self.target_note_name} (up to fret {self.max_fret})."
        )

    def clear_selection(self) -> None:
        if self.locked:
            return
        self.selected.clear()
        self.fretboard.clear_all_cell_markers()
        self.feedback.config(text="")

    def on_fretboard_click(self, position: Position) -> None:
        if self.locked:
            return

        # Toggle selection
        if position in self.selected:
            self.selected.remove(position)
            self.fretboard.clear_cell_marker(position)
        else:
            self.selected.add(position)
            self.fretboard.set_cell_marker(position, outline="blue")

        self.feedback.config(text=f"Selected: {len(self.selected)}")

    def submit_selection(self) -> None:
        if self.locked:
            return
        if self.target_note_index is None or self.target_note_name is None:
            return

        user_positions = list(self.selected)
        correct = check_positions_answer(self.target_note_index, self.max_fret, user_positions)

        # record stats for Mode B (no per-string)
        self.stats.record_attempt_mode_b(correct=correct, note_name=self.target_note_name)

        correct_positions = set(positions_for_note(self.target_note_index, self.max_fret))

        if correct:
            self.score += 1
            self.feedback.config(text="✅ Correct")
            self.locked = True
            self.after(700, self.next_question)
            return

        # Wrong answer: show feedback + highlight results
        self.locked = True
        self.fretboard.clear_all_cell_markers()

        # user selected but wrong (red)
        wrong_selected = self.selected - correct_positions
        # correct and selected (green)
        correct_selected = self.selected & correct_positions
        # correct but missing (orange)
        missing = correct_positions - self.selected

        for pos in correct_selected:
            self.fretboard.set_cell_marker(pos, outline="green")
        for pos in wrong_selected:
            self.fretboard.set_cell_marker(pos, outline="red")
        for pos in list(missing)[:30]:
            # limit to avoid clutter if max_fret is high; still shows enough examples
            self.fretboard.set_cell_marker(pos, outline="orange")

        self.feedback.config(
            text=(
                f"❌ Wrong. Correct count: {len(correct_positions)} | "
                f"You selected: {len(self.selected)} | "
                f"Wrong selected: {len(wrong_selected)} | Missing: {len(missing)}"
            )
        )

        # proceed after a short pause
        self.after(1400, self.next_question)

    def finish(self) -> None:
        self.fretboard.clear_single_highlight()
        self.fretboard.clear_all_cell_markers()
        save_stats(self.stats_path, self.stats)
        self.progress.config(text=f"Finished | Score: {self.score}/{self.num_questions}")
        self.task.config(text="")
        self.feedback.config(text="Saved statistics. You can close the window.")
        self.submit_btn.config(state=tk.DISABLED)
        self.clear_btn.config(state=tk.DISABLED)
        self.locked = True
