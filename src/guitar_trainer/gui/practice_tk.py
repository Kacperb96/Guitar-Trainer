from __future__ import annotations

import random
import time
import tkinter as tk
from collections import deque
from dataclasses import dataclass
from typing import Deque, List, Optional, Set, Tuple

from guitar_trainer.core.adaptive import choose_adaptive_position
from guitar_trainer.core.quiz import question_name_at_position, check_note_name_answer
from guitar_trainer.core.stats import Stats, save_stats
from guitar_trainer.core.position_key import pos_key
from guitar_trainer.core.training_plan import TrainingPlanConfig
from guitar_trainer.gui.fretboard import Fretboard, Position
from guitar_trainer.gui.practice_summary_tk import PracticeSummary


def _get_attempts_correct(stats: Stats, s: int, f: int) -> tuple[int, int]:
    data = stats.by_position.get(pos_key(s, f))
    if not data:
        return 0, 0
    attempts = int(data.get("attempts", 0))
    correct = int(data.get("correct", 0))
    return attempts, correct


def _rank_weak_items(items: List[Tuple[str, int, float | None]], top_n: int = 3) -> List[Tuple[str, int, float | None]]:
    def key_fn(it: Tuple[str, int, float | None]):
        _label, attempts, acc = it
        not_practiced = 0 if attempts == 0 else 1
        acc_val = acc if acc is not None else 0.0
        return (not_practiced, acc_val, attempts)

    return sorted(items, key=key_fn)[:top_n]


class TrainingPlanState:
    def __init__(self, cfg: TrainingPlanConfig, *, max_fret: int, num_strings: int) -> None:
        self.cfg = cfg
        self.max_fret = max_fret
        self.num_strings = num_strings

        # dynamic state
        self.current_end_fret = min(max_fret, max(cfg.end_fret, cfg.start_fret))
        self.current_strings_gui_from = max(1, min(cfg.strings_gui_from, num_strings))
        self.current_strings_gui_to = max(1, min(cfg.strings_gui_to, num_strings))
        if self.current_strings_gui_from > self.current_strings_gui_to:
            self.current_strings_gui_from, self.current_strings_gui_to = self.current_strings_gui_to, self.current_strings_gui_from

        self.current_heat_threshold = float(cfg.heat_threshold)
        self.last_level_up_time = time.monotonic()

    def describe(self) -> str:
        if self.cfg.profile == "FRETS_1_5":
            return f"Plan: Frets {self.cfg.start_fret}–{self.current_end_fret}"
        if self.cfg.profile == "STRINGS_3_6":
            return f"Plan: Strings {self.current_strings_gui_from}–{self.current_strings_gui_to}"
        if self.cfg.profile == "WEAK_HEATMAP":
            return f"Plan: Weak spots (heatmap ≥ {self.current_heat_threshold:.2f})"
        return "Plan: None"

    def constraints(self, stats: Stats) -> tuple[Optional[Set[int]], Optional[Set[int]], Optional[Set[Position]]]:
        # returns (allowed_strings_core, allowed_frets, allowed_positions)
        if self.cfg.profile == "FRETS_1_5":
            start = max(0, int(self.cfg.start_fret))
            end = max(start, int(self.current_end_fret))
            frets = {f for f in range(start, min(self.max_fret, end) + 1)}
            return None, frets, None

        if self.cfg.profile == "STRINGS_3_6":
            # Convert GUI numbering (1=top) to core indices (0=bottom):
            gui_from = int(self.current_strings_gui_from)
            gui_to = int(self.current_strings_gui_to)
            core_set: Set[int] = set()
            for gui_n in range(gui_from, gui_to + 1):
                core_idx = self.num_strings - gui_n
                if 0 <= core_idx < self.num_strings:
                    core_set.add(core_idx)
            return core_set or None, None, None

        if self.cfg.profile == "WEAK_HEATMAP":
            pos: Set[Position] = set()
            thr = max(0.0, min(1.0, float(self.current_heat_threshold)))
            for s in range(self.num_strings):
                for f in range(self.max_fret + 1):
                    attempts, correct = _get_attempts_correct(stats, s, f)
                    if attempts <= 0:
                        bad = 1.0
                    else:
                        acc = correct / attempts
                        bad = 1.0 - acc
                    if bad >= thr:
                        pos.add((s, f))
            return None, None, pos or None

        return None, None, None

    def maybe_level_up(self) -> bool:
        changed = False
        if self.cfg.profile == "FRETS_1_5":
            if self.current_end_fret < self.max_fret:
                self.current_end_fret = min(self.max_fret, self.current_end_fret + max(1, int(self.cfg.ramp_step_frets)))
                changed = True

        elif self.cfg.profile == "STRINGS_3_6":
            if self.current_strings_gui_from > 1:
                self.current_strings_gui_from = max(1, self.current_strings_gui_from - max(1, int(self.cfg.ramp_step_strings)))
                changed = True
            elif self.current_strings_gui_to < self.num_strings:
                self.current_strings_gui_to = min(self.num_strings, self.current_strings_gui_to + max(1, int(self.cfg.ramp_step_strings)))
                changed = True

        elif self.cfg.profile == "WEAK_HEATMAP":
            if self.current_heat_threshold > 0.0:
                self.current_heat_threshold = max(0.0, self.current_heat_threshold - max(0.01, float(self.cfg.ramp_step_threshold)))
                changed = True

        if changed:
            self.last_level_up_time = time.monotonic()
        return changed


def _position_weight(stats: Stats, s: int, f: int) -> float:
    attempts, correct = _get_attempts_correct(stats, s, f)
    if attempts <= 0:
        return 5.0
    acc = correct / attempts
    bad = 1.0 - acc
    return 1.0 + bad * 4.0 + (1.0 / (attempts + 1)) * 2.0


class PracticeSessionFrame(tk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        *,
        stats: Stats,
        stats_path: str,
        minutes: int,
        max_fret: int,
        tuning: list[int],
        tuning_name: str,
        prefer_flats: bool = False,
        rng_seed: int | None = None,
        allowed_strings: Optional[Set[int]] = None,
        allowed_frets: Optional[Set[int]] = None,
        training_plan: Optional[TrainingPlanConfig] = None,
        on_back=None,
        on_finish=None,
    ) -> None:
        super().__init__(master)

        if minutes <= 0:
            raise ValueError("minutes must be > 0")
        if max_fret < 0:
            raise ValueError("max_fret must be >= 0")
        if not tuning:
            raise ValueError("tuning must not be empty")

        self.stats = stats
        self.stats_path = stats_path
        self.minutes = minutes
        self.max_fret = max_fret
        self.tuning = list(tuning)
        self.tuning_name = tuning_name
        self.prefer_flats = prefer_flats
        self.num_strings = len(self.tuning)

        self.on_back = on_back
        self.on_finish = on_finish

        self.allowed_strings = set(allowed_strings) if allowed_strings is not None else None
        self.allowed_frets = set(allowed_frets) if allowed_frets is not None else None

        if self.allowed_strings is not None:
            self.allowed_strings = {s for s in self.allowed_strings if 0 <= s < self.num_strings}
            if not self.allowed_strings:
                self.allowed_strings = None
        if self.allowed_frets is not None:
            self.allowed_frets = {f for f in self.allowed_frets if 0 <= f <= max_fret}
            if not self.allowed_frets:
                self.allowed_frets = None

        self.plan_cfg: TrainingPlanConfig | None = training_plan
        self.plan_state: TrainingPlanState | None = None
        if self.plan_cfg is not None:
            self.plan_state = TrainingPlanState(self.plan_cfg, max_fret=self.max_fret, num_strings=self.num_strings)

        # Rolling window for goal checking
        self._recent: Deque[tuple[float, bool]] = deque()
        self._last_levelup_msg_until = 0.0

        self.rng = random.Random(rng_seed) if rng_seed is not None else random.Random()

        self.total = 0
        self.correct = 0
        self.total_time_sec = 0.0

        self.session_seconds = minutes * 60
        self.end_time = time.monotonic() + self.session_seconds
        self._timer_job: str | None = None

        self.current_position: Position | None = None
        self.current_correct_name: str | None = None
        self.question_start_time = time.monotonic()

        header = tk.Frame(self)
        header.pack(fill="x", pady=(0, 8))

        subtitle = "Adaptive Notes"
        if self.allowed_strings is not None:
            gui_nums = sorted({(self.num_strings - s) for s in self.allowed_strings})  # 1..N
            subtitle += f" | Strings {', '.join(map(str, gui_nums))}"
        if self.allowed_frets is not None and self.allowed_frets:
            subtitle += f" | Frets {min(self.allowed_frets)}–{max(self.allowed_frets)}"

        display = "Flats" if self.prefer_flats else "Sharps"
        tk.Label(
            header,
            text=f"Practice ({minutes} min) | {self.num_strings}-string | {subtitle} | {tuning_name} | {display}",
            font=("Arial", 13),
        ).pack(side="left")

        btns = tk.Frame(header)
        btns.pack(side="right")
        if self.on_back:
            tk.Button(btns, text="Back to menu", command=self._back).pack(side="left", padx=(0, 6))
        tk.Button(btns, text="End session", command=self._end_early).pack(side="left")

        self.time_left_label = tk.Label(self, text="", font=("Arial", 12))
        self.time_left_label.pack()

        self.score_label = tk.Label(self, text="", font=("Arial", 12))
        self.score_label.pack()

        self.plan_label = tk.Label(self, text="", font=("Arial", 11))
        self.plan_label.pack(pady=(2, 0))

        self.fretboard = Fretboard(self, num_strings=self.num_strings, max_fret=self.max_fret, tuning=self.tuning, enable_click_reporting=False)
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

        self._update_ui_labels()
        self._tick_timer()
        self.next_question()

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

    def _window_stats(self) -> tuple[float, int, int]:
        if not self.plan_cfg:
            return 0.0, 0, 0
        now = time.monotonic()
        cutoff = now - int(self.plan_cfg.goal_window_sec)
        while self._recent and self._recent[0][0] < cutoff:
            self._recent.popleft()
        total = len(self._recent)
        correct = sum(1 for _t, ok in self._recent if ok)
        acc = (correct / total) if total > 0 else 0.0
        return acc, correct, total

    def _maybe_level_up(self) -> None:
        if not (self.plan_cfg and self.plan_state):
            return
        acc, _c, n = self._window_stats()
        if n < 10:
            return
        if acc >= float(self.plan_cfg.goal_accuracy):
            if self.plan_state.maybe_level_up():
                self._recent.clear()
                self._last_levelup_msg_until = time.monotonic() + 2.5
                self.feedback.config(text=f"⬆️ Level up! {self.plan_state.describe()}")

    def _update_ui_labels(self) -> None:
        remaining = max(0, int(self.end_time - time.monotonic()))
        self.time_left_label.config(text=f"Time left: {self._format_time(remaining)}")
        self.score_label.config(text=f"Correct: {self.correct}/{self.total}")

        if self.plan_state and self.plan_cfg:
            acc, _c, n = self._window_stats()
            goal = int(float(self.plan_cfg.goal_accuracy) * 100)
            cur = int(acc * 100)
            self.plan_label.config(text=f"{self.plan_state.describe()} | Goal: {cur}%/{goal}% ({n})")
        else:
            self.plan_label.config(text="")

    def _merged_constraints(self) -> tuple[Optional[Set[int]], Optional[Set[int]], Optional[Set[Position]]]:
        plan_strings, plan_frets, plan_positions = (None, None, None)
        if self.plan_state:
            plan_strings, plan_frets, plan_positions = self.plan_state.constraints(self.stats)

        strings = None
        if self.allowed_strings is not None or plan_strings is not None:
            base = set(range(self.num_strings))
            if self.allowed_strings is not None:
                base &= set(self.allowed_strings)
            if plan_strings is not None:
                base &= set(plan_strings)
            strings = base or None

        frets = None
        if self.allowed_frets is not None or plan_frets is not None:
            base = set(range(self.max_fret + 1))
            if self.allowed_frets is not None:
                base &= set(self.allowed_frets)
            if plan_frets is not None:
                base &= set(plan_frets)
            frets = base or None

        positions = plan_positions
        return strings, frets, positions

    def pick_next_position(self) -> Position:
        strings, frets, positions = self._merged_constraints()

        if positions:
            candidates = [(s, f) for (s, f) in positions if 0 <= s < self.num_strings and 0 <= f <= self.max_fret]
            if strings is not None:
                candidates = [(s, f) for (s, f) in candidates if s in strings]
            if frets is not None:
                candidates = [(s, f) for (s, f) in candidates if f in frets]
            if candidates:
                weights = [_position_weight(self.stats, s, f) for (s, f) in candidates]
                return self.rng.choices(candidates, weights=weights, k=1)[0]

        if strings is None and frets is None:
            return choose_adaptive_position(self.stats, self.max_fret, self.rng, num_strings=self.num_strings)

        for _ in range(300):
            s, f = choose_adaptive_position(self.stats, self.max_fret, self.rng, num_strings=self.num_strings)
            if strings is not None and s not in strings:
                continue
            if frets is not None and f not in frets:
                continue
            return (s, f)

        strings2 = strings if strings is not None else set(range(self.num_strings))
        frets2 = frets if frets is not None else set(range(self.max_fret + 1))
        candidates = [(s, f) for s in strings2 for f in frets2]
        return self.rng.choice(candidates) if candidates else (0, 0)

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
        if time.monotonic() > self._last_levelup_msg_until:
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
        self.stats.record_position_attempt(correct=is_correct, note_name=self.current_correct_name, string_index=s, fret=f)

        if self.plan_cfg:
            self._recent.append((time.monotonic(), bool(is_correct)))
            self._maybe_level_up()

        self.feedback.config(text="✅ Correct" if is_correct else f"❌ Wrong. Correct: {self.current_correct_name}")
        self._update_ui_labels()
        self.after(450, self.next_question)

    def _compute_weak_strings(self) -> List[Tuple[str, int, float | None]]:
        items: List[Tuple[str, int, float | None]] = []
        for s in range(self.num_strings):
            attempts_sum = 0
            correct_sum = 0
            for f in range(self.max_fret + 1):
                a, c = _get_attempts_correct(self.stats, s, f)
                attempts_sum += a
                correct_sum += c

            label = f"String {self.num_strings - s}"  # GUI numbering
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
            for s in range(self.num_strings):
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

    def finish(self) -> None:
        self._stop_timer()
        self.fretboard.clear_highlight()
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
            num_strings=self.num_strings,
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
            self.feedback.config(text=f"Finished: {correct}/{answered} ({acc:.1f}%), avg {avg_time:.2f}s")
