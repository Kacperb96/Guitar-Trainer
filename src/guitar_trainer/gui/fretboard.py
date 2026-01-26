import tkinter as tk
from typing import Callable, Optional, Tuple

from guitar_trainer.core.mapping import note_index_at
from guitar_trainer.core.notes import index_to_name
from guitar_trainer.core.tuning import STANDARD_TUNING


Position = Tuple[int, int]  # (string_index, fret) core: 0=low E ... 5=high e


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
    left = margin_x
    right = margin_x + (num_frets + 1) * fret_width
    top = margin_y
    bottom = margin_y + 5 * string_spacing

    if x < left or x > right or y < top or y > bottom:
        return None

    fret = (x - margin_x) // fret_width
    if fret < 0 or fret > num_frets:
        return None

    gui_row = (y - margin_y) // string_spacing
    if gui_row < 0 or gui_row > 5:
        return None

    # GUI: top = high e => core string 5
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
    x = margin_x + fret * fret_width + fret_width // 2
    gui_row = 5 - string_index
    y = margin_y + gui_row * string_spacing
    return x, y


class Fretboard(tk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        *,
        num_frets: int = 12,
        tuning=STANDARD_TUNING,
        margin_x: int = 30,
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
        height = margin_y * 2 + 5 * string_spacing + 20

        self.canvas = tk.Canvas(self, width=width, height=height, bg="white")
        self.canvas.pack(side=tk.TOP)

        self.status = tk.Label(self, text="Click on the fretboard")
        self.status.pack(side=tk.BOTTOM, pady=5)

        self._single_marker_id: int | None = None
        self._cell_markers: dict[Position, int] = {}
        self._heatmap_ids: list[int] = []
        self._click_callback: Callable[[Position], None] | None = None

        self.draw()

        if enable_click_reporting:
            self.canvas.bind("<Button-1>", self.on_click)

    def set_click_callback(self, callback: Callable[[Position], None] | None) -> None:
        self._click_callback = callback

    def _board_bounds(self) -> tuple[int, int, int, int]:
        left = self.margin_x
        right = self.margin_x + (self.num_frets + 1) * self.fret_width
        top = self.margin_y
        bottom = self.margin_y + 5 * self.string_spacing
        return left, right, top, bottom

    def clear_heatmap(self) -> None:
        for _id in self._heatmap_ids:
            self.canvas.delete(_id)
        self._heatmap_ids.clear()

    def set_heatmap_cell(self, position: Position, *, fill: str) -> None:
        """
        Draw a colored rectangle for a given cell (string,fret).
        This is drawn behind strings/frets.
        """
        left, right, top, bottom = self._board_bounds()
        string_index, fret = position
        gui_row = 5 - string_index

        x0 = left + fret * self.fret_width
        x1 = x0 + self.fret_width

        # band around the string line
        y_center = top + gui_row * self.string_spacing
        half = self.string_spacing // 2
        y0 = max(top, y_center - half)
        y1 = min(bottom, y_center + half)

        rid = self.canvas.create_rectangle(x0, y0, x1, y1, outline="", fill=fill, tags=("heatmap",))
        self._heatmap_ids.append(rid)
        self.canvas.tag_lower(rid)  # send behind everything

    def draw(self) -> None:
        board_left, board_right, board_top, board_bottom = self._board_bounds()

        # open-string area
        open_left = board_left
        open_right = board_left + self.fret_width
        self.canvas.create_rectangle(
            open_left, board_top, open_right, board_bottom,
            outline="", fill="#f2f2f2",
        )

        # frets
        for f in range(self.num_frets + 2):
            x = board_left + f * self.fret_width
            self.canvas.create_line(
                x, board_top, x, board_bottom,
                width=2 if f == 0 else 1,
            )

        # nut line
        nut_x = board_left + self.fret_width
        self.canvas.create_line(nut_x, board_top, nut_x, board_bottom, width=4)

        # strings (GUI rows)
        for gui_row in range(6):
            y = self.margin_y + gui_row * self.string_spacing
            self.canvas.create_line(board_left, y, board_right, y, width=2)

        # string numbers on the left (1 at top = high e)
        label_x = board_left - 10
        for gui_row in range(6):
            y = self.margin_y + gui_row * self.string_spacing
            self.canvas.create_text(label_x, y, text=str(gui_row + 1), fill="gray", anchor="e")

        # fret numbers
        for f in [0, 3, 5, 7, 9, 12, 15, 17, 19, 21, 24]:
            if f <= self.num_frets:
                x = board_left + f * self.fret_width + self.fret_width // 2
                self.canvas.create_text(x, board_bottom + 12, text=str(f), fill="gray")

    # ---------- markers ----------

    def highlight_position(self, position: Position) -> None:
        self.clear_single_highlight()
        string_index, fret = position
        cx, cy = position_to_pixel_center(
            string_index, fret,
            margin_x=self.margin_x, margin_y=self.margin_y,
            fret_width=self.fret_width, string_spacing=self.string_spacing,
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
        self.clear_cell_marker(position)
        string_index, fret = position
        cx, cy = position_to_pixel_center(
            string_index, fret,
            margin_x=self.margin_x, margin_y=self.margin_y,
            fret_width=self.fret_width, string_spacing=self.string_spacing,
        )
        r = max(5, self.string_spacing // 5)
        mid = self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline=outline, width=2)
        self._cell_markers[position] = mid

    def clear_cell_marker(self, position: Position) -> None:
        mid = self._cell_markers.pop(position, None)
        if mid is not None:
            self.canvas.delete(mid)

    def clear_all_cell_markers(self) -> None:
        for mid in self._cell_markers.values():
            self.canvas.delete(mid)
        self._cell_markers.clear()

    # ---------- click handling ----------

    def on_click(self, event: tk.Event) -> None:
        pos = pixel_to_position(
            event.x, event.y,
            num_frets=self.num_frets,
            margin_x=self.margin_x, margin_y=self.margin_y,
            fret_width=self.fret_width, string_spacing=self.string_spacing,
        )
        if pos is None:
            self.status.config(text="Clicked outside the fretboard")
            return

        s, f = pos
        note_idx = note_index_at(s, f, self.tuning)
        self.status.config(text=f"Clicked: string={s} fret={f} note={index_to_name(note_idx)}")

        if self._click_callback is not None:
            self._click_callback(pos)
