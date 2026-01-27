from typing import Optional, Tuple

Position = Tuple[int, int]  # (string_index, fret)


def compute_geometry(
    canvas_w: int,
    canvas_h: int,
    num_frets: int,
) -> tuple[int, int, int, int]:
    """
    Compute fretboard geometry from available canvas size.

    Returns:
        margin_x, margin_y, fret_width, string_spacing
    """
    if canvas_w <= 0 or canvas_h <= 0:
        raise ValueError("Canvas size must be positive")

    footer_h = 26

    margin_x = max(26, min(70, int(canvas_w * 0.06)))
    margin_y = max(18, min(60, int(canvas_h * 0.06)))

    usable_w = max(200, canvas_w - 2 * margin_x)
    usable_h = max(160, canvas_h - 2 * margin_y - footer_h)

    fret_width = max(22, min(90, int(usable_w / (num_frets + 1))))
    string_spacing = max(22, min(70, int(usable_h / 5)))

    return margin_x, margin_y, fret_width, string_spacing


def pixel_to_position(
    x: int,
    y: int,
    *,
    num_frets: int,
    margin_x: int,
    margin_y: int,
    fret_width: int,
    string_spacing: int,
) -> Optional[Position]:
    """
    Convert pixel coordinates to (string_index, fret).

    GUI orientation:
    - top = string 1 (high e)
    - bottom = string 6 (low E)

    Core orientation:
    - string_index 0 = low E
    - string_index 5 = high e
    """
    left = margin_x
    right = margin_x + (num_frets + 1) * fret_width
    top = margin_y
    bottom = margin_y + 5 * string_spacing

    if x < left or x > right or y < top or y > bottom:
        return None

    fret = (x - left) // fret_width
    if fret < 0 or fret > num_frets:
        return None

    gui_row = (y - top) // string_spacing
    if gui_row < 0 or gui_row > 5:
        return None

    string_index = 5 - int(gui_row)
    return int(string_index), int(fret)
