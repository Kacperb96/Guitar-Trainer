import tkinter as tk
from typing import Optional, Tuple

from guitar_trainer.core.mapping import note_index_at
from guitar_trainer.core.notes import index_to_name
from guitar_trainer.core.tuning import STANDARD_TUNING


def pixel_to_position(
    x: int,
    y: int,
    *,
    num_frets: int,
    margin_x: int,
    margin_y: int,
    fret_width: int,
    string_spacing: int,
) -> Optional[Tuple[int, int]]:
    """
    Convert canvas pixel coordinates to (string_index, fret).

    string_index: 0..5 (0 = top string)
    fret: 0..num_frets
    Returns None if click is outside the fretboard area.
    """
    # Compute fret area bounds
    left = margin_x
    right = margin_x + (num_frets + 1) * fret_width  # +1 for open-string area
    top = margin_y
    bottom = margin_y + 5 * string_spacing

    if x < left or x > right or y < top or y > bottom:
        return None

    # Fret calculation
    fret = (x - margin_x) // fret_width
    if fret < 0 or fret > num_frets:
        return None

    # String calculation (string 0 at top)
    string_index = (y - margin_y) // string_spacing
    if string_index < 0 or string_index > 5:
        return None

    return int(string_index), int(fret)


class Fretboard(tk.Frame):
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
    ) -> None:
        super().__init__(master)

        self.num_frets = num_frets
        self.tuning = tuning
        self.margin_x = margin_x
        self.margin_y = margin_y
        self.fret_width = fret_width
        self.string_spacing = string_spacing

        width = margin_x * 2 + (num_frets + 1) * fret_width
        height = margin_y * 2 + 5 * string_spacing

        self.canvas = tk.Canvas(self, width=width, height=height, bg="white")
        self.canvas.pack(side=tk.TOP)

        self.status = tk.Label(self, text="Click on the fretboard")
        self.status.pack(side=tk.BOTTOM, pady=5)

        self.draw()
        self.canvas.bind("<Button-1>", self.on_click)

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

        # Draw strings (horizontal lines)
        for s in range(6):
            y = self.margin_y + s * self.string_spacing
            self.canvas.create_line(
                self.margin_x,
                y,
                self.margin_x + (self.num_frets + 1) * self.fret_width,
                y,
                width=2,
            )

        # Fret numbers
        for f in [0, 3, 5, 7, 9, 12]:
            if f <= self.num_frets:
                x = self.margin_x + f * self.fret_width + self.fret_width // 2
                self.canvas.create_text(
                    x,
                    self.margin_y + 5 * self.string_spacing + 12,
                    text=str(f),
                    fill="gray",
                )

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

        self.status.config(
            text=f"Clicked: string={string_index} fret={fret} note={note_name}"
        )
