from __future__ import annotations

# Note index: C=0, C#=1, ..., B=11
# Strings order (core): 0=low E ... 5=high e

STANDARD_TUNING = [4, 9, 2, 7, 11, 4]  # E A D G B E

TUNING_PRESETS: dict[str, list[int]] = {
    "E Standard": [4, 9, 2, 7, 11, 4],          # E A D G B E
    "Eb Standard (D#)": [3, 8, 1, 6, 10, 3],     # Eb Ab Db Gb Bb Eb
    "D Standard": [2, 7, 0, 5, 9, 2],            # D G C F A D
    "Drop D": [2, 9, 2, 7, 11, 4],               # D A D G B E
    "Drop C#": [1, 8, 1, 6, 10, 3],              # C# G# C# F# A# D#
    "Drop C": [0, 7, 0, 5, 9, 2],                # C G C F A D
}

DEFAULT_TUNING_NAME = "E Standard"


def get_tuning_by_name(name: str) -> list[int]:
    """
    Returns a COPY of the tuning list for safety.
    Falls back to E Standard if unknown.
    """
    tuning = TUNING_PRESETS.get(name, TUNING_PRESETS[DEFAULT_TUNING_NAME])
    return list(tuning)
