from __future__ import annotations

# Canonical (sharp) names for indexes 0..11
NOTES_SHARPS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
NOTES_FLATS  = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

# Input aliases (accept both sharps and flats)
_NOTE_NAME_TO_INDEX: dict[str, int] = {
    "C": 0,
    "B#": 0,

    "C#": 1,
    "DB": 1,

    "D": 2,

    "D#": 3,
    "EB": 3,

    "E": 4,
    "FB": 4,

    "F": 5,
    "E#": 5,

    "F#": 6,
    "GB": 6,

    "G": 7,

    "G#": 8,
    "AB": 8,

    "A": 9,

    "A#": 10,
    "BB": 10,

    "B": 11,
    "CB": 11,
}


def normalize_note_index(x: int) -> int:
    return x % 12


def index_to_name(x: int, *, prefer_flats: bool = False) -> str:
    """
    Convert a note index to a display name.
    By default uses sharps: C, C#, D, ...
    If prefer_flats=True uses flats: C, Db, D, ...
    """
    i = normalize_note_index(x)
    return NOTES_FLATS[i] if prefer_flats else NOTES_SHARPS[i]


def parse_note_name(name: str) -> int | None:
    """
    Parse a note name (accept sharps and flats) into note index 0..11.

    Examples:
      "D#" -> 3
      "Eb" -> 3
      "gb" -> 6
      " A# " -> 10
    Returns None if unknown.
    """
    if not isinstance(name, str):
        return None
    s = name.strip().upper()
    if not s:
        return None

    # Normalize unicode accidental symbols if user pasted them
    # ♯ -> #, ♭ -> b
    s = s.replace("♯", "#").replace("♭", "B")

    return _NOTE_NAME_TO_INDEX.get(s)
