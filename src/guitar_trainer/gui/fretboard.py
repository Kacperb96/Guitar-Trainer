import tkinter as tk
from typing import Callable, Optional, Tuple

from guitar_trainer.core.mapping import note_index_at
from guitar_trainer.core.notes import index_to_name
from guitar_trainer.core.tuning import STANDARD_TUNING
from guitar_trainer.gui.fretboard_math import compute_geometry, pixel_to_position

Position = Tuple[int, int]  # (string_index, fret)


class Fretboard(tk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        *,
        num_frets: int = 12,
        tuning=STANDARD_TUNING,
        enable_click_reporting: bool = True,
    ) -> None:
        super().__init__(master)

        self.num_frets = num_frets
        self.tuning = tuning

        self.margin_x = 30
        self.margin_y = 20
        self.fret_width = 50
        self.string_spacing = 30

        self._last_size: tuple[int, int] | None = None

        # redraw state
        self._single_highlight: Position | None = None
        self._cell_markers: dict[Position, str] = {}
        self._heatmap: dict[Position, str] = {}

        self.canvas = tk.Canvas(self, bg="white", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.status = tk.Label(self, text="Click on the fretboard")
        self.status.pack(pady=5)

        self._click_callback: Callable[[Position], None] | None = None

        self.canvas.bind("<Configure>", self._on_resize)
        if enable_click_reporting:
            self.canvas.bind("<Button-1>", self._on_click)

    # ---------- public API ----------

    def set_click_callback(self, callback: Callable[[Position], None]) -> None:
        self._click_callback = callback

    def highlight_position(self, pos: Position) -> None:
        self._single_highlight = pos
        self.redraw()

    def clear_single_highlight(self) -> None:
        self._single_highlight = None
        self.redraw()

    def set_cell_marker(self, pos: Position, *, outline: str = "black") -> None:
        self._cell_markers[pos] = outline
        self.redraw()

    def clear_cell_marker(self, pos: Position) -> None:
        self._cell_markers.pop(pos, None)
        self.redraw()

    def clear_all_cell_markers(self) -> None:
        self._cell_markers.clear()
        self.redraw()

    def set_heatmap_cell(self, pos: Position, *, fill: str) -> None:
        self._heatmap[pos] = fill
        self.redraw()

    def clear_heatmap(self) -> None:
        self._heatmap.clear()
        self.redraw()

    # ---------- geometry & drawing ----------

    def _on_resize(self, event: tk.Event) -> None:
        size = (event.width, event.height)
        if size == self._last_size:
            return

        self._last_size = size
        self.margin_x, self.margin_y, self.fret_width, self.string_spacing = (
            compute_geometry(event.width, event.height, self.num_frets)
        )
        self.redraw()

    def redraw(self) -> None:
        self.canvas.delete("all")
        self._draw_base()
        self._draw_heatmap()
        self._draw_markers()

    def _board_bounds(self) -> tuple[int, int, int, int]:
        left = self.margin_x
        right = left + (self.num_frets + 1) * self.fret_width
        top = self.margin_y
        bottom = top + 5 * self.string_spacing
        return left, right, top, bottom

    def _draw_fret_dots(self) -> None:
        """
        Draw classic fretboard position markers:
        single dots: 3,5,7,9,15,17,19,21
        double dots: 12,24
        """
        left, _right, top, bottom = self._board_bounds()

        # Typical marker frets
        single = {3, 5, 7, 9, 15, 17, 19, 21}
        double = {12, 24}

        # radius scales with geometry
        r = max(4, min(self.fret_width, self.string_spacing) // 6)

        # y positions (between string lines):
        # single dot centered between the middle strings
        y_single = top + int(2.5 * self.string_spacing)

        # double dots a bit above/below center (between gaps)
        y_double_a = top + int(1.5 * self.string_spacing)
        y_double_b = top + int(3.5 * self.string_spacing)

        for fret in range(0, self.num_frets + 1):
            if fret in single or fret in double:
                # dot is usually in the middle of the fret "cell"
                x = left + fret * self.fret_width + self.fret_width // 2

                if fret in double:
                    for y in (y_double_a, y_double_b):
                        self.canvas.create_oval(
                            x - r, y - r, x + r, y + r,
                            fill="gray", outline=""
                        )
                else:
                    self.canvas.create_oval(
                        x - r, y_single - r, x + r, y_single + r,
                        fill="gray", outline=""
                    )

    def _draw_base(self) -> None:
        left, right, top, bottom = self._board_bounds()

        # open-string area (fret 0) – highlighted
        self.canvas.create_rectangle(
            left,
            top,
            left + self.fret_width,
            bottom,
            fill="#f2f2f2",
            outline="",
        )

        # frets (vertical lines)
        for f in range(self.num_frets + 2):
            x = left + f * self.fret_width
            self.canvas.create_line(x, top, x, bottom, width=2 if f == 0 else 1)

        # nut line (between open area and fret 1) – thicker
        nut_x = left + self.fret_width
        self.canvas.create_line(nut_x, top, nut_x, bottom, width=4)

        # position marker dots (draw BEFORE strings so strings look "on top")
        self._draw_fret_dots()

        # strings + string numbers (1 at top)
        for gui_row in range(6):
            y = top + gui_row * self.string_spacing
            self.canvas.create_line(left, y, right, y, width=2)
            self.canvas.create_text(left - 10, y, text=str(gui_row + 1), anchor="e", fill="gray")

        # fret numbers along the bottom
        footer_y = bottom + 12
        for f in [0, 3, 5, 7, 9, 12, 15, 17, 19, 21, 24]:
            if f <= self.num_frets:
                x = left + f * self.fret_width + self.fret_width // 2
                self.canvas.create_text(x, footer_y, text=str(f), fill="gray")

    def _position_center(self, s: int, f: int) -> tuple[int, int]:
        left, _, top, _ = self._board_bounds()
        x = left + f * self.fret_width + self.fret_width // 2
        y = top + (5 - s) * self.string_spacing
        return x, y

    def _draw_heatmap(self) -> None:
        # heatmap rectangles behind strings/frets: draw them first-ish, but after base is ok;
        # they will still sit "under" markers because markers are drawn last.
        left, _, top, bottom = self._board_bounds()

        for (s, f), fill in self._heatmap.items():
            if f < 0 or f > self.num_frets:
                continue
            if s < 0 or s > 5:
                continue

            gui_row = 5 - s
            x0 = left + f * self.fret_width
            x1 = x0 + self.fret_width
            y_center = top + gui_row * self.string_spacing
            half = self.string_spacing // 2

            self.canvas.create_rectangle(
                x0,
                max(top, y_center - half),
                x1,
                min(bottom, y_center + half),
                fill=fill,
                outline="",
            )

    def _draw_markers(self) -> None:
        # many markers (Mode B)
        for (s, f), outline in self._cell_markers.items():
            if f < 0 or f > self.num_frets:
                continue
            if s < 0 or s > 5:
                continue

            cx, cy = self._position_center(s, f)
            r = max(5, self.string_spacing // 5)
            self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline=outline, width=2)

        # single highlight (Mode A)
        if self._single_highlight:
            s, f = self._single_highlight
            if 0 <= s <= 5 and 0 <= f <= self.num_frets:
                cx, cy = self._position_center(s, f)
                r = max(6, self.string_spacing // 4)
                self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline="black", width=2)

    # ---------- input ----------

    def _on_click(self, event: tk.Event) -> None:
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
            return

        s, f = pos
        note = index_to_name(note_index_at(s, f, self.tuning))
        self.status.config(text=f"String={s} Fret={f} Note={note}")

        if self._click_callback:
            self._click_callback(pos)
