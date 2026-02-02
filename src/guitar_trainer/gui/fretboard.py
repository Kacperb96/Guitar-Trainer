from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from guitar_trainer.core.notes import index_to_name
from guitar_trainer.gui.fretboard_math import compute_layout, position_to_rect

Position = tuple[int, int]  # (string_index, fret)


class Fretboard(tk.Frame):
    CANVAS_BG = "#0f1115"
    GUTTER_BG = "#121726"
    BOARD_BG = "#1a1f2b"
    OPEN_BG = "#141a26"
    BORDER = "#2a3142"

    FRET_LINE = "#3a4358"
    NUT_LINE = "#6c7794"
    STRING = "#d7dbe6"
    STRING_SHADOW = "#8a93aa"

    HIGHLIGHT_BAND = "#0b5d6b"  # teal band for selected string

    DOT = "#7b8398"
    DOT_SHADOW = "#2b3142"

    TEXT = "#e7e9ee"
    MUTED = "#a9afbf"
    MUTED_STRONG = "#d0d6e6"
    PILL_BG = "#1c2333"
    PILL_BORDER = "#2f3850"

    MARKER_RED = "#ff4d6d"
    MARKER_GREEN = "#2ecc71"
    MARKER_ORANGE = "#f39c12"

    HEAT_LOW = "#2563eb"   # blue
    HEAT_MID = "#f59e0b"   # amber
    HEAT_HIGH = "#ef4444"  # red

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

        self.canvas = tk.Canvas(
            self,
            highlightthickness=0,
            height=320,
            bg=self.CANVAS_BG,
        )
        self.canvas.pack(fill="both", expand=True)

        self._single_highlight: Position | None = None
        self._highlighted_string: int | None = None
        self._cell_markers: dict[Position, str] = {}
        self._heatmap_values: dict[Position, float] = {}

        self._heatmap_mode: bool = False
        self._string_labels_mode: str = "numbers"  # "numbers" | "notes"
        self._show_fret_numbers: bool = True

        self._toggle_labels_btn = ttk.Button(
            self.canvas, text="NUM",
            command=self._toggle_string_labels, width=6
        )

        self.canvas.bind("<Configure>", lambda _e: self.redraw())
        if self.enable_click_reporting:
            self.canvas.bind("<Button-1>", self._on_click)

    # ---------------------------------------------------------------------
    # Public toggles
    # ---------------------------------------------------------------------
    def set_show_fret_numbers(self, show: bool) -> None:
        self._show_fret_numbers = bool(show)
        self.redraw()

    def get_show_fret_numbers(self) -> bool:
        return bool(self._show_fret_numbers)

    def toggle_fret_numbers(self) -> bool:
        self._show_fret_numbers = not self._show_fret_numbers
        self.redraw()
        return self._show_fret_numbers

    # ---------------------------------------------------------------------
    # Compatibility layer
    # ---------------------------------------------------------------------
    def highlight_position(self, position: Position | None) -> None:
        self._single_highlight = position
        self.redraw()

    def clear_highlight(self) -> None:
        self._single_highlight = None
        self.redraw()

    def clear_single_highlight(self) -> None:
        self._single_highlight = None
        self.redraw()

    def set_single_highlight(self, position: Position | None) -> None:
        self._single_highlight = position
        self.redraw()

    def set_highlighted_string(self, string_index: int | None) -> None:
        """Highlight a whole string (0 = lowest pitch string)."""
        if string_index is None:
            self._highlighted_string = None
        else:
            i = int(string_index)
            self._highlighted_string = i if 0 <= i < self.num_strings else None
        self.redraw()

    def clear_highlighted_string(self) -> None:
        self._highlighted_string = None
        self.redraw()

    def set_cell_marker(self, position: Position, *args, **kwargs) -> None:
        color = None
        if args:
            color = args[0]
        if color is None:
            color = kwargs.get("outline") or kwargs.get("fill") or "red"
        self._cell_markers[position] = str(color)
        self.redraw()

    def clear_cell_marker(self, position: Position) -> None:
        if position in self._cell_markers:
            del self._cell_markers[position]
            self.redraw()

    def clear_all_cell_markers(self) -> None:
        self._cell_markers.clear()
        self.redraw()

    # ---------------------------------------------------------------------

    def set_click_callback(self, cb: Callable[[Position], None]) -> None:
        self._click_cb = cb

    def _toggle_string_labels(self) -> None:
        self._string_labels_mode = "notes" if self._string_labels_mode == "numbers" else "numbers"
        self.redraw()

    def _effective_layout(self, w: int, h: int):
        layout = compute_layout(w, h, num_frets=self.num_frets, num_strings=self.num_strings)

        if self.num_strings > 1:
            spacing = min(layout.string_spacing, float(self.max_string_spacing))
        else:
            spacing = 0.0

        board_h = 0.0 if self.num_strings == 1 else (self.num_strings - 1) * spacing
        desired_top = (h - board_h) / 2.0
        top_y = max(layout.margin_y, desired_top)

        half_band = 18.0 if self.num_strings == 1 else 0.5 * spacing
        band_top = top_y - half_band
        band_bot = top_y + (self.num_strings - 1) * spacing + half_band if self.num_strings > 1 else top_y + half_band
        return layout, spacing, top_y, half_band, band_top, band_bot

    def _on_click(self, event) -> None:
        if not self._click_cb:
            return

        w = max(1, self.canvas.winfo_width())
        h = max(1, self.canvas.winfo_height())
        layout, spacing, top_y, _half_band, band_top, band_bot = self._effective_layout(w, h)

        if event.y < band_top or event.y > band_bot:
            return

        if self.num_strings == 1:
            gui_row = 0
        else:
            gui_row = int(round((event.y - top_y) / spacing))
            gui_row = max(0, min(self.num_strings - 1, gui_row))

        string_index = (self.num_strings - 1) - gui_row

        left_x = layout.margin_x
        nut_x1 = layout.margin_x + layout.nut_width
        right_x = nut_x1 + layout.num_frets * layout.fret_width
        if event.x < left_x or event.x > right_x:
            return

        if event.x <= nut_x1:
            fret = 0
        else:
            rel = event.x - nut_x1
            fret = int(rel // layout.fret_width) + 1
            fret = max(1, min(layout.num_frets, fret))

        self._click_cb((string_index, fret))

    # Heatmap API
    def set_heatmap(self, values: dict[Position, float]) -> None:
        self._heatmap_values = dict(values or {})
        self._heatmap_mode = True
        self.redraw()

    def clear_heatmap(self) -> None:
        self._heatmap_values.clear()
        self._heatmap_mode = False
        self.redraw()

    def _heat_color(self, value: float) -> str:
        if value <= 0.33:
            return self.HEAT_LOW
        if value <= 0.66:
            return self.HEAT_MID
        return self.HEAT_HIGH

    def _heat_outline(self, value: float) -> str:
        return self._heat_color(value)

    # Drawing helpers
    def _cell_center(self, x0: float, y0: float, x1: float, y1: float) -> tuple[float, float]:
        return (x0 + x1) / 2.0, (y0 + y1) / 2.0

    def _dot_radius(self, x0: float, y0: float, x1: float, y1: float, *, scale: float) -> float:
        w = abs(x1 - x0)
        h = abs(y1 - y0)
        base = min(w, h)
        return max(4.0, base * float(scale))

    def _map_marker_color(self, color: str) -> str:
        c = str(color or "").strip().lower()
        if c in {"green", "#2ecc71"}:
            return self.MARKER_GREEN
        if c in {"orange", "#f39c12"}:
            return self.MARKER_ORANGE
        return self.MARKER_RED

    def redraw(self) -> None:
        self.canvas.delete("all")

        w = max(1, self.canvas.winfo_width())
        h = max(1, self.canvas.winfo_height())
        layout, spacing, top_y, half_band, band_top, band_bot = self._effective_layout(w, h)

        left_x = layout.margin_x
        nut_x1 = layout.margin_x + layout.nut_width
        right_x = nut_x1 + layout.num_frets * layout.fret_width

        gutter_w = 14 if self._heatmap_mode else 60
        gutter_x0 = max(0, left_x - gutter_w - 12)
        gutter_x1 = left_x - 12

        self.canvas.create_rectangle(0, 0, w, h, outline="", fill=self.CANVAS_BG)

        self.canvas.create_rectangle(gutter_x0, band_top, gutter_x1, band_bot, outline="", fill=self.GUTTER_BG)
        self.canvas.create_line(gutter_x1, band_top, gutter_x1, band_bot, fill=self.BORDER, width=2)

        if not self._heatmap_mode:
            self._toggle_labels_btn.configure(text="NUM" if self._string_labels_mode == "numbers" else "NOTES")
            btn_cx = gutter_x0 + (gutter_w / 2)
            btn_y = max(12, band_top - 18)
            self.canvas.create_window(btn_cx, btn_y, window=self._toggle_labels_btn, anchor="center")

        self.canvas.create_rectangle(left_x, band_top, nut_x1, band_bot, outline="", fill=self.OPEN_BG)
        self.canvas.create_rectangle(nut_x1, band_top, right_x, band_bot, outline="", fill=self.BOARD_BG)
        self.canvas.create_rectangle(left_x, band_top, right_x, band_bot, outline=self.BORDER, width=2)

        # Highlight an entire string (if requested)
        if self._highlighted_string is not None and not self._heatmap_mode:
            s = self._highlighted_string
            gui_row = (self.num_strings - 1) - s
            y = top_y + gui_row * spacing if self.num_strings > 1 else top_y
            y0 = y - half_band
            y1 = y + half_band
            self.canvas.create_rectangle(
                left_x,
                y0,
                right_x,
                y1,
                outline="",
                fill=self.HIGHLIGHT_BAND,
            )

        if self._heatmap_values:
            for (s, f), v in self._heatmap_values.items():
                if not (0 <= s < self.num_strings and 0 <= f <= self.num_frets):
                    continue
                v = max(0.0, min(1.0, float(v)))
                if v <= 0.02:
                    continue

                rect = position_to_rect(layout, s, f)
                if rect is None:
                    continue
                x0, _y0, x1, _y1 = rect

                gui_row = (self.num_strings - 1) - s
                y = top_y + gui_row * spacing if self.num_strings > 1 else top_y
                y0 = y - half_band
                y1 = y + half_band

                self.canvas.create_rectangle(
                    x0, y0, x1, y1,
                    outline=self._heat_outline(v),
                    width=1,
                    fill=self._heat_color(v),
                )

        self.canvas.create_line(nut_x1, band_top, nut_x1, band_bot, fill=self.NUT_LINE, width=4)
        for i in range(1, layout.num_frets + 1):
            x = nut_x1 + i * layout.fret_width
            self.canvas.create_line(x, band_top, x, band_bot, fill=self.FRET_LINE, width=2)

        dot_frets = {3, 5, 7, 9, 12, 15, 17, 19, 21, 24}
        mid_y = (band_top + band_bot) / 2.0
        for f in dot_frets:
            if f > layout.num_frets:
                continue
            cx = nut_x1 + (f - 0.5) * layout.fret_width

            def dot(cy: float, r: float = 6.5):
                self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=self.DOT_SHADOW, outline="")
                self.canvas.create_oval(cx - (r - 1), cy - (r - 1), cx + (r - 1), cy + (r - 1), fill=self.DOT, outline="")

            if f in {12, 24}:
                cy1 = band_top + (band_bot - band_top) * 0.40
                cy2 = band_top + (band_bot - band_top) * 0.60
                dot(cy1)
                dot(cy2)
            else:
                dot(mid_y)

        for gui_row in range(self.num_strings):
            y = top_y + gui_row * spacing if self.num_strings > 1 else top_y

            if self.num_strings == 1:
                width_px = 3
            else:
                width_px = 1 + int(4 * (gui_row / (self.num_strings - 1)))

            self.canvas.create_line(left_x, y + 1, right_x, y + 1, fill=self.STRING_SHADOW, width=width_px)
            self.canvas.create_line(left_x, y, right_x, y, fill=self.STRING, width=width_px)

            if self._heatmap_mode:
                continue

            if self._string_labels_mode == "numbers":
                label = str(gui_row + 1)
            else:
                tuning_idx = (self.num_strings - 1) - gui_row
                label = index_to_name(self.tuning[tuning_idx])

            pill_w = 30 + max(0, len(label) - 2) * 10
            pill_h = 22
            cx = gutter_x0 + (gutter_w / 2)
            x0 = cx - pill_w / 2
            x1 = cx + pill_w / 2
            y0 = y - pill_h / 2
            y1 = y + pill_h / 2

            self.canvas.create_rectangle(x0, y0, x1, y1, fill=self.PILL_BG, outline=self.PILL_BORDER, width=1)
            self.canvas.create_text(
                cx,
                y,
                text=label,
                anchor="center",
                fill=self.MUTED_STRONG,
                font=("Segoe UI", 11, "bold"),
            )

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
            r = self._dot_radius(x0, y0, x1, y1, scale=0.20)
            c = self._map_marker_color(color)

            self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill="#000000", outline="")
            self.canvas.create_oval(cx - (r - 1), cy - (r - 1), cx + (r - 1), cy + (r - 1), fill=c, outline=c)

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

                self.canvas.create_oval(cx - (r + 5), cy - (r + 5), cx + (r + 5), cy + (r + 5),
                                        fill="#2a0b14", outline="")
                self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=self.MARKER_RED,
                                        outline=self.MARKER_RED)

        # Fret numbers (toggleable)
        if self._show_fret_numbers:
            for f in range(1, layout.num_frets + 1):
                x = nut_x1 + (f - 0.5) * layout.fret_width
                self.canvas.create_text(x, band_bot + 20, text=str(f), fill=self.MUTED, font=("Segoe UI", 10))
