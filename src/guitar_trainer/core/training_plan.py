from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

Profile = Literal["FRETS_1_5", "WEAK_HEATMAP", "STRINGS_3_6"]


@dataclass(frozen=True)
class TrainingPlanConfig:
    profile: Profile

    # Goal / progression
    goal_accuracy: float = 0.80          # 0..1
    goal_window_sec: int = 120           # seconds

    # FRETS_1_5
    start_fret: int = 1
    end_fret: int = 5
    ramp_step_frets: int = 2

    # WEAK_HEATMAP
    heat_threshold: float = 0.60         # 0..1 where 1=unseen/worst
    ramp_step_threshold: float = 0.10

    # STRINGS_3_6 (GUI numbering: 1=top/thinnest)
    strings_gui_from: int = 3
    strings_gui_to: int = 6
    ramp_step_strings: int = 1

    def __post_init__(self) -> None:
        if self.profile not in ("FRETS_1_5", "WEAK_HEATMAP", "STRINGS_3_6"):
            raise ValueError("TrainingPlanConfig.profile is invalid.")

        if not (0.0 <= float(self.goal_accuracy) <= 1.0):
            raise ValueError("TrainingPlanConfig.goal_accuracy must be between 0 and 1.")
        if int(self.goal_window_sec) < 10 or int(self.goal_window_sec) > 1800:
            raise ValueError("TrainingPlanConfig.goal_window_sec must be between 10 and 1800.")

        if int(self.start_fret) < 0 or int(self.end_fret) < 0:
            raise ValueError("Fret values must be >= 0.")
        if int(self.ramp_step_frets) < 1:
            raise ValueError("ramp_step_frets must be >= 1.")

        if not (0.0 <= float(self.heat_threshold) <= 1.0):
            raise ValueError("heat_threshold must be between 0 and 1.")
        if not (0.01 <= float(self.ramp_step_threshold) <= 1.0):
            raise ValueError("ramp_step_threshold must be between 0.01 and 1.0.")

        if int(self.strings_gui_from) < 1 or int(self.strings_gui_to) < 1:
            raise ValueError("strings_gui_* must be >= 1.")
        if int(self.ramp_step_strings) < 1:
            raise ValueError("ramp_step_strings must be >= 1.")


def plan_from_menu(
    *,
    plan_name: str,
    goal_accuracy: float,
    goal_window_sec: int,
    heat_threshold: float,
    num_strings: int,
) -> Optional[TrainingPlanConfig]:
    name = (plan_name or "").strip()
    if not name or name == "None":
        return None

    if name == "Frets 1–5":
        return TrainingPlanConfig(
            profile="FRETS_1_5",
            goal_accuracy=goal_accuracy,
            goal_window_sec=goal_window_sec,
            start_fret=1,
            end_fret=5,
            ramp_step_frets=2,
        )

    if name == "Strings 3–6":
        return TrainingPlanConfig(
            profile="STRINGS_3_6",
            goal_accuracy=goal_accuracy,
            goal_window_sec=goal_window_sec,
            strings_gui_from=3,
            strings_gui_to=max(3, int(num_strings)),
            ramp_step_strings=1,
        )

    # Default: weak heatmap
    return TrainingPlanConfig(
        profile="WEAK_HEATMAP",
        goal_accuracy=goal_accuracy,
        goal_window_sec=goal_window_sec,
        heat_threshold=heat_threshold,
        ramp_step_threshold=0.10,
    )
