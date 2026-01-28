from __future__ import annotations

from typing import Optional, Tuple


def pos_key(string_index: int, fret: int) -> str:
    """Return a stable string key for a fretboard position.

    The canonical format is: "<string_index>,<fret>" using core string indexing.
    """
    return f"{int(string_index)},{int(fret)}"


def parse_pos_key(key: str) -> Optional[Tuple[int, int]]:
    """Parse a position key created by pos_key().

    Returns (string_index, fret) or None if parsing fails.
    """
    try:
        s, f = str(key).split(",", 1)
        return int(s), int(f)
    except Exception:
        return None
