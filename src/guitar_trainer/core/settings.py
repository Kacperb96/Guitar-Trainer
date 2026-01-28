from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from guitar_trainer.core.tuning import (
    DEFAULT_NUM_STRINGS,
    CUSTOM_TUNING_NAME,
    parse_custom_tuning_text,
)
from guitar_trainer.core.training_plan import TrainingPlanConfig, plan_from_menu

QUESTIONS_MIN = 1
QUESTIONS_MAX = 200

PRACTICE_MIN_MINUTES = 1
PRACTICE_MAX_MINUTES = 120

MAX_FRET_MIN = 0
MAX_FRET_MAX = 24

GOAL_ACC_MIN = 0.0
GOAL_ACC_MAX = 1.0

GOAL_WINDOW_MIN_SEC = 10
GOAL_WINDOW_MAX_SEC = 1800

HEAT_THRESHOLD_MIN = 0.0
HEAT_THRESHOLD_MAX = 1.0


def parse_int_field(value: str, *, min_value: int, max_value: int, field_name: str) -> int:
    try:
        v = int(str(value).strip())
    except Exception:
        raise ValueError(f"{field_name} must be an integer.")
    if v < min_value or v > max_value:
        raise ValueError(f"{field_name} must be between {min_value} and {max_value}.")
    return v


def parse_float_field(value: str, *, min_value: float, max_value: float, field_name: str) -> float:
    try:
        v = float(str(value).strip())
    except Exception:
        raise ValueError(f"{field_name} must be a number.")
    if v < min_value or v > max_value:
        raise ValueError(f"{field_name} must be between {min_value} and {max_value}.")
    return v


@dataclass(frozen=True)
class AppSettings:
    mode: str
    num_questions: int
    max_fret: int
    tuning_name: str
    practice_minutes: int
    prefer_flats: bool
    num_strings: int
    custom_tuning: Optional[list[int]] = None
    plan_config: Optional[TrainingPlanConfig] = None

    @staticmethod
    def validate_num_strings(raw: str) -> int:
        try:
            n = int(str(raw).strip())
        except Exception:
            return DEFAULT_NUM_STRINGS
        if n < 4 or n > 12:
            return DEFAULT_NUM_STRINGS
        return n


def build_settings_from_menu(
    *,
    mode_raw: str,
    questions_raw: str,
    practice_minutes_raw: str,
    max_fret_raw: str,
    num_strings_raw: str,
    tuning_name_raw: str,
    display_raw: str,
    custom_tuning_raw: str,
    plan_name_raw: str,
    plan_goal_acc_raw: str,
    plan_goal_window_raw: str,
    plan_heat_thr_raw: str,
) -> AppSettings:
    mode = str(mode_raw or "").strip().upper() or "A"
    if mode not in ("A", "B", "ADAPT", "PRACTICE"):
        raise ValueError("Mode must be one of: A, B, ADAPT, PRACTICE.")

    num_questions = parse_int_field(
        questions_raw, min_value=QUESTIONS_MIN, max_value=QUESTIONS_MAX, field_name="Questions"
    )
    practice_minutes = parse_int_field(
        practice_minutes_raw,
        min_value=PRACTICE_MIN_MINUTES,
        max_value=PRACTICE_MAX_MINUTES,
        field_name="Practice minutes",
    )
    max_fret = parse_int_field(
        max_fret_raw, min_value=MAX_FRET_MIN, max_value=MAX_FRET_MAX, field_name="Max fret"
    )

    num_strings = AppSettings.validate_num_strings(num_strings_raw)

    tuning_name = str(tuning_name_raw or "").strip() or CUSTOM_TUNING_NAME
    prefer_flats = str(display_raw or "").strip().lower() == "flats"

    custom_tuning: Optional[list[int]] = None
    if tuning_name == CUSTOM_TUNING_NAME:
        custom_tuning = parse_custom_tuning_text(custom_tuning_raw, num_strings=num_strings)

    plan_config: Optional[TrainingPlanConfig] = None
    plan_name = str(plan_name_raw or "").strip()
    if mode == "PRACTICE" and plan_name and plan_name != "None":
        goal_acc = parse_float_field(
            plan_goal_acc_raw, min_value=GOAL_ACC_MIN, max_value=GOAL_ACC_MAX, field_name="Goal accuracy"
        )
        goal_win = parse_int_field(
            plan_goal_window_raw,
            min_value=GOAL_WINDOW_MIN_SEC,
            max_value=GOAL_WINDOW_MAX_SEC,
            field_name="Goal window (sec)",
        )
        heat_thr = parse_float_field(
            plan_heat_thr_raw,
            min_value=HEAT_THRESHOLD_MIN,
            max_value=HEAT_THRESHOLD_MAX,
            field_name="Heatmap threshold",
        )

        plan_config = plan_from_menu(
            plan_name=plan_name,
            goal_accuracy=goal_acc,
            goal_window_sec=goal_win,
            heat_threshold=heat_thr,
            num_strings=num_strings,
        )

    return AppSettings(
        mode=mode,
        num_questions=num_questions,
        max_fret=max_fret,
        tuning_name=tuning_name,
        practice_minutes=practice_minutes,
        prefer_flats=prefer_flats,
        num_strings=num_strings,
        custom_tuning=custom_tuning,
        plan_config=plan_config,
    )
