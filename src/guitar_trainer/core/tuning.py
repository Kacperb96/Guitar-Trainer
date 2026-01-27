from __future__ import annotations

from guitar_trainer.core.notes import parse_note_name

# Note index: C=0, C#=1, ..., B=11
# Tuning list is in CORE order: 0 = lowest string ... last = highest string

TUNING_PRESETS_6: dict[str, list[int]] = {
    "E Standard": [4, 9, 2, 7, 11, 4],            # E A D G B E
    "Eb Standard (D#)": [3, 8, 1, 6, 10, 3],       # Eb Ab Db Gb Bb Eb
    "D Standard": [2, 7, 0, 5, 9, 2],              # D G C F A D
    "Drop D": [2, 9, 2, 7, 11, 4],                 # D A D G B E
    "Drop C#": [1, 8, 1, 6, 10, 3],                # C# G# C# F# A# D#
    "Drop C": [0, 7, 0, 5, 9, 2],                  # C G C F A D
}

TUNING_PRESETS_7: dict[str, list[int]] = {
    "B Standard": [11, 4, 9, 2, 7, 11, 4],         # B E A D G B E
    "Bb Standard (A#)": [10, 3, 8, 1, 6, 10, 3],   # Bb Eb Ab Db Gb Bb Eb
    "A Standard": [9, 2, 7, 0, 5, 9, 2],           # A D G C F A D
    "Drop A": [9, 4, 9, 2, 7, 11, 4],              # A E A D G B E
}

DEFAULT_NUM_STRINGS = 6
DEFAULT_TUNING_NAME_6 = "E Standard"
DEFAULT_TUNING_NAME_7 = "B Standard"

CUSTOM_TUNING_NAME = "Custom..."


def get_tuning_presets(num_strings: int) -> dict[str, list[int]]:
    if num_strings == 7:
        return TUNING_PRESETS_7
    return TUNING_PRESETS_6


def get_default_tuning_name(num_strings: int) -> str:
    return DEFAULT_TUNING_NAME_7 if num_strings == 7 else DEFAULT_TUNING_NAME_6


def get_tuning_by_name(num_strings: int, name: str) -> list[int]:
    presets = get_tuning_presets(num_strings)
    default_name = get_default_tuning_name(num_strings)
    tuning = presets.get(name, presets[default_name])
    return list(tuning)  # copy


def parse_custom_tuning_text(text: str, *, num_strings: int) -> list[int]:
    """
    Parse user input like:
      "E A D G B E"
      "E,A,D,G,B,E"
      "B E A D G B E" (7-string)
      "Eb Ab Db Gb Bb Eb"
    Returns list[int] of length num_strings (CORE order: lowest -> highest).
    """
    if num_strings <= 0:
        raise ValueError("num_strings must be >= 1")

    cleaned = text.strip()
    if not cleaned:
        raise ValueError("Custom tuning is empty.")

    # allow commas or spaces
    cleaned = cleaned.replace(",", " ")
    parts = [p.strip() for p in cleaned.split() if p.strip()]
    if len(parts) != num_strings:
        raise ValueError(f"Custom tuning must contain exactly {num_strings} notes (got {len(parts)}).")

    out: list[int] = []
    for token in parts:
        idx = parse_note_name(token)
        if idx is None:
            raise ValueError(f"Invalid note name in tuning: '{token}'")
        out.append(idx)

    return out


# Backward-compatible constants (6-string)
STANDARD_TUNING = list(TUNING_PRESETS_6[DEFAULT_TUNING_NAME_6])
TUNING_PRESETS = TUNING_PRESETS_6
DEFAULT_TUNING_NAME = DEFAULT_TUNING_NAME_6
