from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from guitar_trainer.gui.fretboard_math import compute_layout, position_to_rect
from guitar_trainer.core.notes import index_to_name

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
    STRING_SHADOW = "#9aa2b6"

    DOT = "#b7bdcd"
    DOT_SHADOW = "#232a3a"

    PILL_BG = "#0e1320"
    PILL_BORDER = "#2a3142"
    MUTED = "#9aa2b6"
    MUTED_STRONG = "#cfd4e3"

    HIT = "#22c55e"
    MISS = "#ef4444"
    TARGET = "#f59e0b"

    # Question indicator (this is the “red circle” user expects in Mode A)
    QUESTION = "#ef4444"
    QUESTION_SHADOW = "#35181a"

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
        self._cell_markers: dict[Position, str] = {}
        self._heatmap_values: dict[Position, float] = {}

        # left gutter labels: numbers (1..N) or open-string note names
        self._string_labels_mode: str = "numbers"
        self._toggle_labels_btn = ttk.Button(self.canvas, text="NUM", command=self._toggle_string_labels, width=6)

        self.canvas.bind("<Configure>", lambda _e: self.redraw())
        if self.enable_click_reporting:
            self.canvas.bind("<Button-1>", self._on_click)

    # ---------------------------------------------------------------------
    # Compatibility layer (old API used by quiz_tk.py / practice_tk.py)
    # ---------------------------------------------------------------------
    def highlight_position(self, pos: Position | None) -> None:
        self.set_single_highlight(pos)

    def clear_highlight(self) -> None:
        self.set_single_highlight(None)

    def clear_all_cell_markers(self) -> None:
        self.clear_markers()

    def set_cell_marker(self, pos: Position, color: str | None = None, **kwargs) -> None:
        """
        Backwards-compatible:
        - set_cell_marker(pos, "red")
        - set_cell_marker(pos, outline="red")
        Ignores other kwargs safely.
        """
        if color is None:
            # Old code passes outline="red"
            color = kwargs.get("outline") or kwargs.get("fill") or self.MUTED
        self._cell_markers[pos] = str(color)
        self.redraw()

    def clear_cell_marker(self, pos: Position) -> None:
        if pos in self._cell_markers:
            del self._cell_markers[pos]
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

    def _cell_center(self, x0: float, y0: float, x1: float, y1: float) -> tuple[float, float]:
        return (x0 + x1) / 2.0, (y0 + y1) / 2.0

    def _dot_radius(self, x0: float, y0: float, x1: float, y1: float, *, scale: float) -> float:
        w = abs(x1 - x0)
        h = abs(y1 - y0)
        return max(3.0, min(w, h) * scale)

    def _map_marker_color(self, c: str) -> str:
        c = (c or "").lower()
        if c in {"hit", "good", "ok", "correct"}:
            return self.HIT
        if c in {"miss", "bad", "wrong", "incorrect"}:
            return self.MISS
        if c in {"target", "focus"}:
            return self.TARGET
        return c if c else self.MUTED

    def set_single_highlight(self, pos: Position | None) -> None:
        self._single_highlight = pos
        self.redraw()

    def set_cell_markers(self, markers: dict[Position, str]) -> None:
        self._cell_markers = dict(markers)
        self.redraw()

    def clear_markers(self) -> None:
        self._cell_markers.clear()
        self._single_highlight = None
        self.redraw()

    def set_heatmap(self, values: dict[Position, float]) -> None:
        self._heatmap_values = dict(values)
        self.redraw()

    def clear_heatmap(self) -> None:
        self._heatmap_values.clear()
        self.redraw()

    def _pixel_to_position_effective(self, x: float, y: float) -> Position | None:
        """
        Convert canvas pixel -> (string_index, fret) using the SAME geometry as redraw().
        This fixes click precision when we vertically center / clamp spacing.
        """
        w = max(1, self.canvas.winfo_width())
        h = max(1, self.canvas.winfo_height())
        layout, spacing, top_y, half_band, band_top, band_bot = self._effective_layout(w, h)

        # vertical bounds
        if y < band_top or y > band_bot:
            return None

        # horizontal bounds
        left_x = layout.margin_x
        nut_x1 = layout.margin_x + layout.nut_width
        right_x = nut_x1 + layout.num_frets * layout.fret_width
        if x < left_x or x > right_x:
            return None

        # string (nearest)
        if self.num_strings == 1:
            gui_row = 0
        else:
            gui_row = int(round((y - top_y) / spacing))
            gui_row = max(0, min(self.num_strings - 1, gui_row))

        string_index = (self.num_strings - 1) - gui_row  # back to core index

        # fret
        if x <= nut_x1:
            fret = 0
        else:
            rel = x - nut_x1
            fret = int(rel // layout.fret_width) + 1
            fret = max(1, min(layout.num_frets, fret))

        return (string_index, fret)

    def _on_click(self, e: tk.Event) -> None:
        if not self._click_cb:
            return

        pos = self._pixel_to_position_effective(float(e.x), float(e.y))
        if pos is None:
            return

        self._click_cb(pos)

    def redraw(self) -> None:
        self.canvas.delete("all")

        w = max(1, self.canvas.winfo_width())
        h = max(1, self.canvas.winfo_height())
        layout, spacing, top_y, half_band, band_top, band_bot = self._effective_layout(w, h)

        left_x = layout.margin_x
        nut_x1 = layout.margin_x + layout.nut_width
        right_x = nut_x1 + layout.num_frets * layout.fret_width

        # gutter
        gutter_w = 60
        gutter_x0 = max(0, left_x - gutter_w - 12)
        gutter_x1 = left_x - 12

        self.canvas.create_rectangle(0, 0, w, h, outline="", fill=self.CANVAS_BG)

        # gutter panel
        self.canvas.create_rectangle(gutter_x0, band_top, gutter_x1, band_bot, outline="", fill=self.GUTTER_BG)
        self.canvas.create_line(gutter_x1, band_top, gutter_x1, band_bot, fill=self.BORDER, width=2)

        # Toggle button
        self._toggle_labels_btn.configure(text="NUM" if self._string_labels_mode == "numbers" else "NOTE")
        btn_cx = gutter_x0 + (gutter_w / 2)
        btn_y = max(12, band_top - 18)
        self.canvas.create_window(btn_cx, btn_y, window=self._toggle_labels_btn, anchor="center")

        # open + board
        self.canvas.create_rectangle(left_x, band_top, nut_x1, band_bot, outline="", fill=self.OPEN_BG)
        self.canvas.create_rectangle(nut_x1, band_top, right_x, band_bot, outline="", fill=self.BOARD_BG)
        self.canvas.create_rectangle(left_x, band_top, right_x, band_bot, outline=self.BORDER, width=2)

        # heatmap
        if self._heatmap_values:
            for (s, f), v in self._heatmap_values.items():
                if not (0 <= s < self.num_strings and 0 <= f <= self.num_frets):
                    continue
                v = max(0.0, min(1.0, float(v)))
                if v < 0.15:
                    continue
                if v < 0.35:
                    color = "#2a1a20"
                elif v < 0.60:
                    color = "#3a1b27"
                else:
                    color = "#541c31"

                rect = position_to_rect(layout, s, f)
                if rect is None:
                    continue
                x0, _y0, x1, _y1 = rect

                gui_row = (self.num_strings - 1) - s
                y = top_y + gui_row * spacing if self.num_strings > 1 else top_y
                y0 = y - half_band
                y1 = y + half_band

                self.canvas.create_rectangle(x0, y0, x1, y1, outline="", fill=color)

        # nut + frets
        self.canvas.create_line(nut_x1, band_top, nut_x1, band_bot, fill=self.NUT_LINE, width=4)
        for i in range(1, layout.num_frets + 1):
            x = nut_x1 + i * layout.fret_width
            self.canvas.create_line(x, band_top, x, band_bot, fill=self.FRET_LINE, width=2)

        # fret dots
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

        # strings + labels
        for gui_row in range(self.num_strings):
            y = top_y + gui_row * spacing if self.num_strings > 1 else top_y

            if self.num_strings == 1:
                width_px = 3
            else:
                width_px = 1 + int(4 * (gui_row / (self.num_strings - 1)))

            self.canvas.create_line(left_x, y + 1, right_x, y + 1, fill=self.STRING_SHADOW, width=width_px)
            self.canvas.create_line(left_x, y, right_x, y, fill=self.STRING, width=width_px)

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

        # cell markers (hit/miss/etc)
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

            self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=c, outline="")

        # single highlight (QUESTION indicator) -> filled red circle (as before)
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
                r = self._dot_radius(x0, y0, x1, y1, scale=0.30)

                # shadow
                self.canvas.create_oval(cx - r + 1, cy - r + 1, cx + r + 1, cy + r + 1, fill=self.QUESTION_SHADOW, outline="")
                # fill
                self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=self.QUESTION, outline="")

        # fret numbers
        for f in range(1, layout.num_frets + 1):
            x = nut_x1 + (f - 0.5) * layout.fret_width
            self.canvas.create_text(
                x,
                band_bot + 20,
                text=str(f),
                fill=self.MUTED,
                font=("Segoe UI", 10),
            )
