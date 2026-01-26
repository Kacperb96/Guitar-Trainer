import tkinter as tk
from typing import Callable, Optional, Tuple

from guitar_trainer.core.mapping import note_index_at
from guitar_trainer.core.notes import index_to_name
from guitar_trainer.core.tuning import STANDARD_TUNING


Position = Tuple[int, int]  # (string_index, fret) in CORE convention: 0=low E ... 5=high e


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
    Convert canvas pixel coordinates to (string_index, fret).

    GUI orientation:
      - top line = high e (core string_index = 5)
      - bottom line = low E (core string_index = 0)

    fret: 0..num_frets
    Returns None if click is outside the fretboard area.
    """
    left = margin_x
    right = margin_x + (num_frets + 1) * fret_width  # +1 open-string area
    top = margin_y
    bottom = margin_y + 5 * string_spacing

    if x < left or x > right or y < top or y > bottom:
        return None

    fret = (x - margin_x) // fret_width
    if fret < 0 or fret > num_frets:
        return None

    # gui_row: 0..5 where 0 is the top string line
    gui_row = (y - margin_y) // string_spacing
    if gui_row < 0 or gui_row > 5:
        return None

    # invert: gui_row 0 -> core string 5, gui_row 5 -> core string 0
    string_index = 5 - int(gui_row)

    return int(string_index), int(fret)


def position_to_pixel_center(
    string_index: int,
    fret: int,
    *,
    margin_x: int,
    margin_y: int,
    fret_width: int,
    string_spacing: int,
) -> Tuple[int, int]:
    """
    Return center (x,y) in pixels for a given (string_index, fret) cell.

    GUI orientation:
      - top row represents core string_index=5
      - bottom row represents core string_index=0
    """
    x = margin_x + fret * fret_width + fret_width // 2

    gui_row = 5 - string_index
    y = margin_y + gui_row * string_spacing

    return x, y


class Fretboard(tk.Frame):
    """
    A simple fretboard canvas widget.

    - Draws a 6-string fretboard up to num_frets.
    - GUI orientation: high e on top, low E on bottom.
    - Can optionally report clicks via a callback.
    - Supports highlighting a single position (Mode A) and multiple positions (Mode B).
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        num_frets: int = 12,
        tuning=STANDARD_TUNING,
        margin_x: int = 20,
        margin_y: int = 20,
        fret_width: int = 50,
        string_spacing: int = 30,
        enable_click_reporting: bool = True,
    ) -> None:
        super().__init__(master)

        self.num_frets = num_frets
        self.tuning = tuning
        self.margin_x = margin_x
        self.margin_y = margin_y
        self.fret_width = fret_width
        self.string_spacing = string_spacing

        width = margin_x * 2 + (num_frets + 1) * fret_width
        height = margin_y * 2 + 5 * string_spacing + 20  # space for fret numbers

        self.canvas = tk.Canvas(self, width=width, height=height, bg="white")
        self.canvas.pack(side=tk.TOP)

        self.status = tk.Label(self, text="Click on the fretboard")
        self.status.pack(side=tk.BOTTOM, pady=5)

        self._single_marker_id: int | None = None
        self._cell_markers: dict[Position, int] = {}
        self._click_callback: Callable[[Position], None] | None = None

        self.draw()

        if enable_click_reporting:
            self.canvas.bind("<Button-1>", self.on_click)

    def set_click_callback(self, callback: Callable[[Position], None] | None) -> None:
        self._click_callback = callback

    def draw(self) -> None:
        # Draw frets (vertical lines)
        for f in range(self.num_frets + 2):  # +1 open area, +1 last line
            x = self.margin_x + f * self.fret_width
            self.canvas.create_line(
                x,
                self.margin_y,
                x,
                self.margin_y + 5 * self.string_spacing,
                width=2 if f == 0 else 1,
            )

        # Draw strings (horizontal lines) as GUI rows 0..5 (top..bottom)
        for gui_row in range(6):
            y = self.margin_y + gui_row * self.string_spacing
            self.canvas.create_line(
                self.margin_x,
                y,
                self.margin_x + (self.num_frets + 1) * self.fret_width,
                y,
                width=2,
            )

        # Fret numbers
        for f in [0, 3, 5, 7, 9, 12, 15, 17, 19, 21, 24]:
            if f <= self.num_frets:
                x = self.margin_x + f * self.fret_width + self.fret_width // 2
                self.canvas.create_text(
                    x,
                    self.margin_y + 5 * self.string_spacing + 12,
                    text=str(f),
                    fill="gray",
                )

    # ---------- highlighting ----------

    def highlight_position(self, position: Position) -> None:
        """Mode A: show exactly one dot marker."""
        self.clear_single_highlight()

        string_index, fret = position
        cx, cy = position_to_pixel_center(
            string_index,
            fret,
            margin_x=self.margin_x,
            margin_y=self.margin_y,
            fret_width=self.fret_width,
            string_spacing=self.string_spacing,
        )

        r = max(6, self.string_spacing // 4)
        self._single_marker_id = self.canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r, outline="black", width=2
        )

    def clear_single_highlight(self) -> None:
        if self._single_marker_id is not None:
            self.canvas.delete(self._single_marker_id)
            self._single_marker_id = None

    def set_cell_marker(self, position: Position, *, outline: str = "black") -> None:
        """Mode B: draw/update a marker for a specific cell."""
        self.clear_cell_marker(position)

        string_index, fret = position
        cx, cy = position_to_pixel_center(
            string_index,
            fret,
            margin_x=self.margin_x,
            margin_y=self.margin_y,
            fret_width=self.fret_width,
            string_spacing=self.string_spacing,
        )
        r = max(5, self.string_spacing // 5)
        marker_id = self.canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r, outline=outline, width=2
        )
        self._cell_markers[position] = marker_id

    def clear_cell_marker(self, position: Position) -> None:
        marker_id = self._cell_markers.pop(position, None)
        if marker_id is not None:
            self.canvas.delete(marker_id)

    def clear_all_cell_markers(self) -> None:
        for marker_id in self._cell_markers.values():
            self.canvas.delete(marker_id)
        self._cell_markers.clear()

    # ---------- click handling ----------

    def on_click(self, event: tk.Event) -> None:
        pos = pixel_to_position(
            event.x,
            event.y,
            num_frets=self.num_frets,
            margin_x=self.margin_x,
            margin_y=self.margin_y,
            fret_width=self.fret_width,
            string_spacing=self.string_spacing,
        )

        if pos is None:
            self.status.config(text="Clicked outside the fretboard")
            return

        string_index, fret = pos
        note_idx = note_index_at(string_index, fret, self.tuning)
        note_name = index_to_name(note_idx)
        self.status.config(text=f"Clicked: string={string_index} fret={fret} note={note_name}")

        if self._click_callback is not None:
            self._click_callback(pos)
