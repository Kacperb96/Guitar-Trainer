import tkinter as tk

from guitar_trainer.core.stats import Stats
from guitar_trainer.gui.fretboard import Fretboard


def _clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


def _mix_color(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> str:
    t = _clamp(t, 0.0, 1.0)
    r = int(a[0] + (b[0] - a[0]) * t)
    g = int(a[1] + (b[1] - a[1]) * t)
    bl = int(a[2] + (b[2] - a[2]) * t)
    return f"#{r:02x}{g:02x}{bl:02x}"


class StatsHeatmapFrame(tk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        *,
        stats: Stats,
        max_fret: int,
        on_back=None,
    ) -> None:
        super().__init__(master)

        self.stats = stats
        self.max_fret = max_fret
        self.on_back = on_back

        # ---------- header ----------
        header = tk.Frame(self)
        header.pack(fill="x", pady=(0, 8))

        tk.Label(header, text="Heatmap (Mode A positions)", font=("Arial", 13)).pack(side="left")
        if self.on_back:
            tk.Button(header, text="Back to menu", command=self.on_back).pack(side="right")

        # ---------- controls ----------
        controls = tk.Frame(self)
        controls.pack(fill="x", padx=10, pady=(0, 8))

        tk.Label(controls, text="Metric:").pack(side="left")
        self.metric_var = tk.StringVar(value="Attempts")
        tk.OptionMenu(
            controls,
            self.metric_var,
            "Attempts",
            "Accuracy",
            command=lambda _v: self.render(),
        ).pack(side="left", padx=8)

        self.info = tk.Label(controls, text="", fg="gray")
        self.info.pack(side="left", padx=10)

        # ---------- fretboard ----------
        self.fretboard = Fretboard(self, num_frets=max_fret, enable_click_reporting=False)
        self.fretboard.pack(fill="both", expand=True, padx=12, pady=12)

        self.render()

    def render(self) -> None:
        self.fretboard.clear_heatmap()

        points = []
        max_attempts = 0

        for s in range(6):
            for f in range(self.max_fret + 1):
                key = f"{s},{f}"
                data = self.stats.by_position.get(key)
                attempts = int(data.get("attempts", 0)) if data else 0
                correct = int(data.get("correct", 0)) if data else 0
                max_attempts = max(max_attempts, attempts)
                points.append((s, f, attempts, correct))

        metric = self.metric_var.get()

        white = (255, 255, 255)
        red = (255, 140, 140)
        green = (140, 220, 140)

        painted = 0
        for s, f, attempts, correct in points:
            if metric == "Attempts":
                if attempts == 0 or max_attempts == 0:
                    continue
                t = attempts / max_attempts
                fill = _mix_color(white, red, t)
            else:
                if attempts == 0:
                    continue
                acc = correct / attempts
                fill = _mix_color(red, green, acc)

            self.fretboard.set_heatmap_cell((s, f), fill=fill)
            painted += 1

        if metric == "Attempts":
            self.info.config(
                text=f"Painted: {painted} | max attempts: {max_attempts}"
            )
        else:
            self.info.config(
                text=f"Painted: {painted} | cells with attempts > 0"
            )
