from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FretboardLayout:
    width: int
    height: int
    num_frets: int
    num_strings: int
    margin_x: int
    margin_y: int
    nut_width: int
    fret_width: float
    string_spacing: float


def compute_layout(
    width: int,
    height: int,
    *,
    num_frets: int,
    num_strings: int,
    margin_x: int = 20,
    margin_y: int = 20,
    nut_width: int = 40,
) -> FretboardLayout:
    width = max(1, int(width))
    height = max(1, int(height))
    num_frets = max(1, int(num_frets))
    num_strings = max(1, int(num_strings))

    usable_w = max(1, width - 2 * margin_x - nut_width)
    fret_width = usable_w / num_frets

    if num_strings == 1:
        string_spacing = 0.0
    else:
        usable_h = max(1, height - 2 * margin_y)
        string_spacing = usable_h / (num_strings - 1)

    return FretboardLayout(
        width=width,
        height=height,
        num_frets=num_frets,
        num_strings=num_strings,
        margin_x=margin_x,
        margin_y=margin_y,
        nut_width=nut_width,
        fret_width=fret_width,
        string_spacing=string_spacing,
    )


# --- Backward-compatible alias for older tests/code ---
def compute_geometry(
    width: int,
    height: int,
    *,
    num_frets: int,
    num_strings: int = 6,
    margin_x: int = 20,
    margin_y: int = 20,
    nut_width: int = 40,
) -> FretboardLayout:
    """
    Compatibility wrapper: old code/tests used compute_geometry().
    """
    return compute_layout(
        width,
        height,
        num_frets=num_frets,
        num_strings=num_strings,
        margin_x=margin_x,
        margin_y=margin_y,
        nut_width=nut_width,
    )


def position_to_rect(layout: FretboardLayout, string_index: int, fret: int) -> tuple[float, float, float, float] | None:
    if string_index < 0 or string_index >= layout.num_strings:
        return None
    if fret < 0 or fret > layout.num_frets:
        return None

    gui_row = (layout.num_strings - 1) - string_index
    y = layout.margin_y + gui_row * layout.string_spacing

    if fret == 0:
        x0 = layout.margin_x
        x1 = layout.margin_x + layout.nut_width
    else:
        x0 = layout.margin_x + layout.nut_width + (fret - 1) * layout.fret_width
        x1 = x0 + layout.fret_width

    if layout.num_strings == 1:
        y0, y1 = y - 10, y + 10
    else:
        y0 = y - layout.string_spacing / 2
        y1 = y + layout.string_spacing / 2

    return (x0, y0, x1, y1)


def pixel_to_position(
    x: float,
    y: float,
    *,
    width: int,
    height: int,
    num_frets: int,
    num_strings: int = 6,
    margin_x: int = 20,
    margin_y: int = 20,
    nut_width: int = 40,
) -> tuple[int, int] | None:
    layout = compute_layout(
        width,
        height,
        num_frets=num_frets,
        num_strings=num_strings,
        margin_x=margin_x,
        margin_y=margin_y,
        nut_width=nut_width,
    )

    # vertical bounds check
    if layout.num_strings == 1:
        top_y = layout.margin_y
        bot_y = layout.margin_y
        half = 10
    else:
        top_y = layout.margin_y
        bot_y = layout.margin_y + (layout.num_strings - 1) * layout.string_spacing
        half = 0.5 * layout.string_spacing

    if y < top_y - half or y > bot_y + half:
        return None

    # nearest string in GUI coords
    if layout.num_strings == 1:
        gui_row = 0
    else:
        gui_row = int(round((y - layout.margin_y) / layout.string_spacing))
        gui_row = max(0, min(layout.num_strings - 1, gui_row))

    string_index = (layout.num_strings - 1) - gui_row

    # horizontal bounds
    nut_x0 = layout.margin_x
    nut_x1 = layout.margin_x + layout.nut_width
    max_x = nut_x1 + layout.num_frets * layout.fret_width
    if x < nut_x0 or x > max_x:
        return None

    if x <= nut_x1:
        fret = 0
    else:
        rel = x - nut_x1
        fret = int(rel // layout.fret_width) + 1
        fret = max(1, min(layout.num_frets, fret))

    return (string_index, fret)
