from .tuning import STANDARD_TUNING
from .notes import normalize_note_index

def note_index_at(string_index: int, fret: int, tuning: list[int] = STANDARD_TUNING) -> int:
    """
    Return pitch-class index (0..11) at given string and fret.
    string_index: 0..5 (0 = low E, 5 = high E)
    fret: >= 0 (0 = open string)
    """
    if string_index < 0 or string_index >= len(tuning):
        raise ValueError("string_index must be between 0 and 5")
    if fret < 0:
        raise ValueError("fret must be >= 0")

    return normalize_note_index(tuning[string_index] + fret)


def positions_for_note(note_index: int, max_fret: int, tuning: list[int] = STANDARD_TUNING) -> list[tuple[int, int]]:
    """
    Return all (string_index, fret) positions where given pitch-class occurs,
    searching frets 0..max_fret inclusive.
    Ordering: string 0..5, then fret ascending within each string.
    """
    if max_fret < 0:
        raise ValueError("max_fret must be >= 0")

    target = normalize_note_index(note_index)
    positions: list[tuple[int, int]] = []

    for string_index in range(len(tuning)):
        open_note = tuning[string_index]
        for fret in range(max_fret + 1):
            if normalize_note_index(open_note + fret) == target:
                positions.append((string_index, fret))

    return positions