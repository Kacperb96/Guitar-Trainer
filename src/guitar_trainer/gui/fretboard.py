from __future__ import annotations

import tkinter as tk
from typing import Callable, Optional

from guitar_trainer.gui.fretboard_math import compute_layout, position_to_rect

Position = tuple[int, int]  # (string_index, fret)


class Fretboard(tk.Frame):
    """
    Draws a fretboard for N strings (len(tuning)) and num_frets.

    GUI string numbers:
      1 at TOP (highest string), N at bottom (lowest).

    Core string_index:
      0 = lowest string ... N-1 = highest string.

    Fixes included:
    - caps vertical stretch (max_string_spacing) so it doesn't become huge
    - hit-testing (click -> position) uses EXACT SAME geometry as drawing
    - Mode B markers are circles (default RED), not rectangles
    - highlight is a RED circle
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        num_frets: int,
        tuning: list[int],
        enable_click_reporting: bool = False,
        max_string_spacing: int = 48,
    ) -> None:
        super().__init__(master)

        self.num_frets = int(num_frets)
        self.tuning = list(tuning)
        self.num_strings = len(self.tuning)
        if self.num_strings <= 0:
            raise ValueError("tuning must contain at least 1 string")

        self.enable_click_reporting = enable_click_reporting
        self.max_string_spacing = int(max_string_spacing)

        self._click_cb: Optional[Callable[[Position], None]] = None

        # Sensible default height
        self.canvas = tk.Canvas(self, highlightthickness=0, height=320)
        self.canvas.pack(fill="both", expand=True)

        self._single_highlight: Position | None = None
        self._cell_markers: dict[Position, str] = {}  # position -> color
        self._heatmap_values: dict[Position, float] = {}

        self.canvas.bind("<Configure>", lambda _e: self.redraw())
        if self.enable_click_reporting:
            self.canvas.bind("<Button-1>", self._on_click)

    # ---------- callbacks ----------

    def set_click_callback(self, cb: Callable[[Position], None]) -> None:
        self._click_cb = cb

    def _effective_layout(self, w: int, h: int):
        """
        Returns:
          layout (from compute_layout for X geometry),
          spacing (capped),
          top_y (centered),
          half_band (half spacing),
          first_string_y, last_string_y,
          band_top, band_bot
        """
        layout = compute_layout(w, h, num_frets=self.num_frets, num_strings=self.num_strings)

        if self.num_strings > 1:
            spacing = min(layout.string_spacing, float(self.max_string_spacing))
        else:
            spacing = 0.0

        if self.num_strings == 1:
            board_h = 0.0
        else:
            board_h = (self.num_strings - 1) * spacing

        desired_top = (h - board_h) / 2.0
        top_y = max(layout.margin_y, desired_top)

        if self.num_strings == 1:
            first_string_y = top_y
            last_string_y = top_y
            half_band = 18.0
        else:
            first_string_y = top_y
            last_string_y = top_y + (self.num_strings - 1) * spacing
            half_band = 0.5 * spacing

        band_top = first_string_y - half_band
        band_bot = last_string_y + half_band
        return layout, spacing, top_y, half_band, first_string_y, last_string_y, band_top, band_bot

    def _on_click(self, event) -> None:
        if not self._click_cb:
            return

        w = max(1, self.canvas.winfo_width())
        h = max(1, self.canvas.winfo_height())
        layout, spacing, top_y, half_band, first_y, last_y, band_top, band_bot = self._effective_layout(w, h)

        # bounds vertical
        if event.y < band_top or event.y > band_bot:
            return

        # determine GUI row (0 = top)
        if self.num_strings == 1:
            gui_row = 0
        else:
            gui_row = int(round((event.y - top_y) / spacing))
            gui_row = max(0, min(self.num_strings - 1, gui_row))

        # convert to core string_index
        string_index = (self.num_strings - 1) - gui_row

        # bounds horizontal
        left_x = layout.margin_x
        nut_x1 = layout.margin_x + layout.nut_width
        right_x = nut_x1 + layout.num_frets * layout.fret_width
        if event.x < left_x or event.x > right_x:
            return

        # fret
        if event.x <= nut_x1:
            fret = 0
        else:
            rel = event.x - nut_x1
            fret = int(rel // layout.fret_width) + 1
            fret = max(1, min(layout.num_frets, fret))

        self._click_cb((string_index, fret))

    # ---------- heatmap ----------

    def set_heatmap(self, values: dict[Position, float]) -> None:
        self._heatmap_values = dict(values)
        self.redraw()

    def clear_heatmap(self) -> None:
        self._heatmap_values.clear()
        self.redraw()

    # ---------- markers / highlight ----------

    def highlight_position(self, position: Position) -> None:
        self._single_highlight = position
        self.redraw()

    def clear_single_highlight(self) -> None:
        self._single_highlight = None
        self.redraw()

    def set_cell_marker(self, position: Position, *, outline: str = "red") -> None:
        """
        Mode B selection marker. Default is RED as requested.
        You can pass outline="green"/"orange" etc for feedback.
        """
        self._cell_markers[position] = outline
        self.redraw()

    def clear_cell_marker(self, position: Position) -> None:
        if position in self._cell_markers:
            del self._cell_markers[position]
            self.redraw()

    def clear_all_cell_markers(self) -> None:
        self._cell_markers.clear()
        self.redraw()

    # ---------- drawing helpers ----------

    def _cell_center(self, x0: float, y0: float, x1: float, y1: float) -> tuple[float, float]:
        return (0.5 * (x0 + x1), 0.5 * (y0 + y1))

    def _dot_radius(self, x0: float, y0: float, x1: float, y1: float, *, scale: float) -> float:
        r = min((x1 - x0), (y1 - y0)) * scale
        return max(6.0, min(16.0, r))

    # ---------- redraw ----------

    def redraw(self) -> None:
        self.canvas.delete("all")

        w = max(1, self.canvas.winfo_width())
        h = max(1, self.canvas.winfo_height())
        layout, spacing, top_y, half_band, first_y, last_y, band_top, band_bot = self._effective_layout(w, h)

        left_x = layout.margin_x
        nut_x1 = layout.margin_x + layout.nut_width
        right_x = nut_x1 + layout.num_frets * layout.fret_width

        # background
        self.canvas.create_rectangle(left_x, band_top, nut_x1, band_bot, outline="", fill="#f0f0f0")
        self.canvas.create_rectangle(nut_x1, band_top, right_x, band_bot, outline="", fill="#ffffff")
        self.canvas.create_rectangle(left_x, band_top, right_x, band_bot, outline="black", width=2)

        # heatmap layer (under strings & dots)
        if self._heatmap_values:
            for (s, f), v in self._heatmap_values.items():
                if not (0 <= s < self.num_strings and 0 <= f <= self.num_frets):
                    continue
                v = max(0.0, min(1.0, float(v)))
                intensity = int(255 * (1.0 - v))
                color = f"#{intensity:02x}{intensity:02x}{intensity:02x}"

                rect = position_to_rect(layout, s, f)
                if rect is None:
                    continue
                x0, _y0, x1, _y1 = rect

                gui_row = (self.num_strings - 1) - s
                y = top_y + gui_row * spacing if self.num_strings > 1 else top_y
                y0 = y - half_band
                y1 = y + half_band

                self.canvas.create_rectangle(x0, y0, x1, y1, outline="", fill=color)

        # frets
        self.canvas.create_line(nut_x1, band_top, nut_x1, band_bot, width=4)
        for i in range(1, layout.num_frets + 1):
            x = nut_x1 + i * layout.fret_width
            self.canvas.create_line(x, band_top, x, band_bot, width=2)

        # fret dots
        dot_frets = {3, 5, 7, 9, 12, 15, 17, 19, 21, 24}
        mid_y = (first_y + last_y) / 2.0
        for f in dot_frets:
            if f > layout.num_frets:
                continue
            cx = nut_x1 + (f - 0.5) * layout.fret_width
            if f in {12, 24}:
                cy1 = first_y + (last_y - first_y) * 0.35
                cy2 = first_y + (last_y - first_y) * 0.65
                self.canvas.create_oval(cx - 6, cy1 - 6, cx + 6, cy1 + 6, fill="gray", outline="")
                self.canvas.create_oval(cx - 6, cy2 - 6, cx + 6, cy2 + 6, fill="gray", outline="")
            else:
                self.canvas.create_oval(cx - 6, mid_y - 6, cx + 6, mid_y + 6, fill="gray", outline="")

        # strings + numbers
        for gui_row in range(self.num_strings):
            y = top_y + gui_row * spacing if self.num_strings > 1 else top_y
            if self.num_strings == 1:
                width_px = 3
            else:
                width_px = 1 + int(4 * (gui_row / (self.num_strings - 1)))
            self.canvas.create_line(left_x, y, right_x, y, width=width_px)
            self.canvas.create_text(left_x - 12, y, text=str(gui_row + 1), anchor="e", font=("Arial", 10, "bold"))

        # Mode B markers as COLORED DOTS
        for (s, f), color in self._cell_markers.items():
            rect = position_to_rect(layout, s, f)
            if rect is None:
                continue
            x0, _y0, x1, _y1 = rect
            gui_row = (self.num_strings - 1) - s
            y = top_y + gui_row * spacing if self.num_strings > 1 else top_y
            y0 = y - half_band
            y1 = y + half_band
            cx, cy = self._cell_center(x0, y0, x1, y1)
            r = self._dot_radius(x0, y0, x1, y1, scale=0.22)
            self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=color, outline=color)

        # highlight as RED DOT (slightly larger)
        if self._single_highlight is not None:
            s, f = self._single_highlight
            rect = position_to_rect(layout, s, f)
            if rect is not None:
                x0, _y0, x1, _y1 = rect
                gui_row = (self.num_strings - 1) - s
                y = top_y + gui_row * spacing if self.num_strings > 1 else top_y
                y0 = y - half_band
                y1 = y + half_band
                cx, cy = self._cell_center(x0, y0, x1, y1)
                r = self._dot_radius(x0, y0, x1, y1, scale=0.28)
                self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill="red", outline="red")
