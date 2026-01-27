from __future__ import annotations

import random
import time
import tkinter as tk
from typing import List, Tuple, Optional, Set

from guitar_trainer.core.adaptive import choose_adaptive_position
from guitar_trainer.core.quiz import question_name_at_position, check_note_name_answer
from guitar_trainer.core.stats import Stats, save_stats
from guitar_trainer.core.tuning import STANDARD_TUNING
from guitar_trainer.gui.fretboard import Fretboard, Position
from guitar_trainer.gui.practice_summary_tk import PracticeSummary


def _pos_key(s: int, f: int) -> str:
    return f"{s},{f}"


def _get_attempts_correct(stats: Stats, s: int, f: int) -> tuple[int, int]:
    data = stats.by_position.get(_pos_key(s, f))
    if not data:
        return 0, 0
    attempts = int(data.get("attempts", 0))
    correct = int(data.get("correct", 0))
    return attempts, correct


def _rank_weak_items(items: List[Tuple[str, int, float | None]], top_n: int = 3) -> List[Tuple[str, int, float | None]]:
    """
    Sorting rule:
    - not practiced (attempts==0) first
    - then lowest accuracy
    - tie-breaker: fewer attempts first
    """
    def key_fn(it: Tuple[str, int, float | None]):
        _label, attempts, acc = it
        not_practiced = 0 if attempts == 0 else 1
        acc_val = acc if acc is not None else 0.0
        return (not_practiced, acc_val, attempts)

    return sorted(items, key=key_fn)[:top_n]


class PracticeSessionFrame(tk.Frame):
    """
    Timed practice session (adaptive notes):
    - Records stats.by_position
    - Tracks session totals + avg response time
    - Optional filters:
        allowed_strings: core string_index set (0..5)
        allowed_frets: fret set (0..max_fret)
    - prefer_flats: affects displayed correct note name (input accepts both anyway)
    - On finish calls: on_finish(PracticeSummary)
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        stats: Stats,
        stats_path: str,
        minutes: int,
        max_fret: int,
        tuning: list[int] = STANDARD_TUNING,
        tuning_name: str = "E Standard",
        prefer_flats: bool = False,
        rng_seed: int | None = None,
        allowed_strings: Optional[Set[int]] = None,
        allowed_frets: Optional[Set[int]] = None,
        on_back=None,
        on_finish=None,  # callback(summary: PracticeSummary)
    ) -> None:
        super().__init__(master)

        if minutes <= 0:
            raise ValueError("minutes must be > 0")
        if max_fret < 0:
            raise ValueError("max_fret must be >= 0")

        self.stats = stats
        self.stats_path = stats_path
        self.minutes = minutes
        self.max_fret = max_fret
        self.tuning = tuning
        self.tuning_name = tuning_name
        self.prefer_flats = prefer_flats
        self.on_back = on_back
        self.on_finish = on_finish

        self.allowed_strings = set(allowed_strings) if allowed_strings is not None else None
        self.allowed_frets = set(allowed_frets) if allowed_frets is not None else None

        # sanitize filters
        if self.allowed_strings is not None:
            self.allowed_strings = {s for s in self.allowed_strings if 0 <= s <= 5}
            if not self.allowed_strings:
                self.allowed_strings = None
        if self.allowed_frets is not None:
            self.allowed_frets = {f for f in self.allowed_frets if 0 <= f <= max_fret}
            if not self.allowed_frets:
                self.allowed_frets = None

        self.rng = random.Random(rng_seed) if rng_seed is not None else random.Random()

        # session state
        self.total = 0
        self.correct = 0
        self.total_time_sec = 0.0

        self.session_seconds = minutes * 60
        self.end_time = time.monotonic() + self.session_seconds
        self._timer_job: str | None = None

        self.current_position: Position | None = None
        self.current_correct_name: str | None = None
        self.question_start_time = time.monotonic()

        # ---------- header ----------
        header = tk.Frame(self)
        header.pack(fill="x", pady=(0, 8))

        subtitle = "Adaptive Notes"
        if self.allowed_strings is not None:
            gui_nums = sorted({6 - s for s in self.allowed_strings})  # GUI: 1..6
            subtitle += f" | Strings {', '.join(map(str, gui_nums))}"
        if self.allowed_frets is not None and self.allowed_frets:
            subtitle += f" | Frets {min(self.allowed_frets)}–{max(self.allowed_frets)}"

        display = "Flats" if self.prefer_flats else "Sharps"
        tk.Label(
            header,
            text=f"Practice Session ({minutes} min) | {subtitle} | {tuning_name} | {display}",
            font=("Arial", 13),
        ).pack(side="left")

        btns = tk.Frame(header)
        btns.pack(side="right")

        if self.on_back:
            tk.Button(btns, text="Back to menu", command=self._back).pack(side="left", padx=(0, 6))

        tk.Button(btns, text="End session", command=self._end_early).pack(side="left")

        # ---------- info row ----------
        info = tk.Frame(self)
        info.pack(fill="x", pady=(0, 6))

        self.time_left_label = tk.Label(info, text="")
        self.time_left_label.pack(side="left")

        self.score_label = tk.Label(info, text="")
        self.score_label.pack(side="right")

        # ---------- fretboard ----------
        self.fretboard = Fretboard(self, num_frets=max_fret, tuning=tuning, enable_click_reporting=False)
        self.fretboard.pack(fill="both", expand=True, padx=10, pady=10)

        # ---------- input ----------
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

        # start
        self._update_ui_labels()
        self._tick_timer()
        self.next_question()

    # ---------- navigation ----------

    def _back(self) -> None:
        self._stop_timer()
        save_stats(self.stats_path, self.stats)
        self.on_back()

    def _stop_timer(self) -> None:
        if self._timer_job is not None:
            try:
                self.after_cancel(self._timer_job)
            except Exception:
                pass
            self._timer_job = None

    def _end_early(self) -> None:
        self._stop_timer()
        self.finish()

    # ---------- timer ----------

    def _tick_timer(self) -> None:
        remaining = int(self.end_time - time.monotonic())
        if remaining <= 0:
            self.finish()
            return

        self._update_ui_labels()
        self._timer_job = self.after(250, self._tick_timer)

    def _format_time(self, seconds: int) -> str:
        m = seconds // 60
        s = seconds % 60
        return f"{m:02d}:{s:02d}"

    def _update_ui_labels(self) -> None:
        remaining = max(0, int(self.end_time - time.monotonic()))
        self.time_left_label.config(text=f"Time left: {self._format_time(remaining)}")
        self.score_label.config(text=f"Correct: {self.correct}/{self.total}")

    # ---------- adaptive pick with filters ----------

    def pick_next_position(self) -> Position:
        """
        Try adaptive positions until filters match.
        Fallback: uniform random among allowed positions if filters are too strict.
        """
        if self.allowed_strings is None and self.allowed_frets is None:
            return choose_adaptive_position(self.stats, self.max_fret, self.rng)

        for _ in range(200):
            s, f = choose_adaptive_position(self.stats, self.max_fret, self.rng)
            if self.allowed_strings is not None and s not in self.allowed_strings:
                continue
            if self.allowed_frets is not None and f not in self.allowed_frets:
                continue
            return (s, f)

        candidates: list[Position] = []
        strings = self.allowed_strings if self.allowed_strings is not None else set(range(6))
        frets = self.allowed_frets if self.allowed_frets is not None else set(range(self.max_fret + 1))
        for s in strings:
            for f in frets:
                candidates.append((s, f))

        if not candidates:
            return choose_adaptive_position(self.stats, self.max_fret, self.rng)

        return self.rng.choice(candidates)

    # ---------- session flow ----------

    def next_question(self) -> None:
        if time.monotonic() >= self.end_time:
            self.finish()
            return

        self.current_position = self.pick_next_position()
        self.current_correct_name = question_name_at_position(
            self.current_position,
            tuning=self.tuning,
            prefer_flats=self.prefer_flats,
        )

        self.fretboard.highlight_position(self.current_position)
        self.feedback.config(text="")
        self.answer_var.set("")
        self.answer_entry.focus_set()
        self.question_start_time = time.monotonic()

    def submit_answer(self) -> None:
        if self.current_position is None or self.current_correct_name is None:
            return
        if time.monotonic() >= self.end_time:
            self.finish()
            return

        dt = time.monotonic() - self.question_start_time
        self.total_time_sec += dt

        user_answer = self.answer_var.get()
        is_correct = check_note_name_answer(self.current_correct_name, user_answer)

        self.total += 1
        if is_correct:
            self.correct += 1

        s, f = self.current_position
        self.stats.record_position_attempt(
            correct=is_correct,
            note_name=self.current_correct_name,
            string_index=s,
            fret=f,
        )

        self.feedback.config(text="✅ Correct" if is_correct else f"❌ Wrong. Correct: {self.current_correct_name}")
        self._update_ui_labels()

        self.after(450, self.next_question)

    # ---------- weak areas computation (from saved stats) ----------

    def _compute_weak_strings(self) -> List[Tuple[str, int, float | None]]:
        items: List[Tuple[str, int, float | None]] = []
        for s in range(6):
            attempts_sum = 0
            correct_sum = 0
            for f in range(self.max_fret + 1):
                a, c = _get_attempts_correct(self.stats, s, f)
                attempts_sum += a
                correct_sum += c

            gui_string_number = 6 - s  # core: s=5->GUI 1, s=0->GUI 6
            label = f"String {gui_string_number}"
            if attempts_sum == 0:
                items.append((label, 0, None))
            else:
                acc = (correct_sum / attempts_sum) * 100.0
                items.append((label, attempts_sum, acc))

        return _rank_weak_items(items, top_n=3)

    def _compute_weak_frets(self) -> List[Tuple[str, int, float | None]]:
        items: List[Tuple[str, int, float | None]] = []
        for f in range(self.max_fret + 1):
            attempts_sum = 0
            correct_sum = 0
            for s in range(6):
                a, c = _get_attempts_correct(self.stats, s, f)
                attempts_sum += a
                correct_sum += c

            label = f"Fret {f}"
            if attempts_sum == 0:
                items.append((label, 0, None))
            else:
                acc = (correct_sum / attempts_sum) * 100.0
                items.append((label, attempts_sum, acc))

        return _rank_weak_items(items, top_n=3)

    # ---------- finish ----------

    def finish(self) -> None:
        self._stop_timer()
        self.fretboard.clear_single_highlight()

        save_stats(self.stats_path, self.stats)

        self.submit_btn.config(state=tk.DISABLED)
        self.answer_entry.config(state=tk.DISABLED)

        answered = self.total
        correct = self.correct
        avg_time = (self.total_time_sec / answered) if answered > 0 else 0.0
        acc = (correct / answered * 100.0) if answered > 0 else 0.0

        summary = PracticeSummary(
            minutes=self.minutes,
            max_fret=self.max_fret,
            tuning_name=self.tuning_name,
            answered=answered,
            correct=correct,
            accuracy_percent=acc,
            avg_time_sec=avg_time,
            weak_strings=self._compute_weak_strings(),
            weak_frets=self._compute_weak_frets(),
        )

        if self.on_finish is not None:
            self.on_finish(summary)
        else:
            self.feedback.config(
                text=(
                    f"Session finished. Answered: {answered}, Correct: {correct} ({acc:.1f}%), "
                    f"Avg time: {avg_time:.2f}s"
                )
            )
