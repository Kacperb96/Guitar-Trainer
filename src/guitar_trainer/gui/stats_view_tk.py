import tkinter as tk

from guitar_trainer.core.stats import Stats
from guitar_trainer.gui.fretboard import Fretboard


def _pos_key(s: int, f: int) -> str:
    return f"{s},{f}"


class StatsHeatmapFrame(tk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        *,
        stats: Stats,
        max_fret: int,
        num_strings: int,
        on_back=None,
    ) -> None:
        super().__init__(master)

        self.stats = stats
        self.max_fret = max_fret
        self.num_strings = num_strings
        self.on_back = on_back

        header = tk.Frame(self)
        header.pack(fill="x", pady=(0, 8))
        tk.Label(header, text=f"Heatmap | {num_strings}-string | up to fret {max_fret}", font=("Arial", 13)).pack(side="left")
        if self.on_back:
            tk.Button(header, text="Back", command=self.on_back).pack(side="right")

        # Use dummy tuning just for drawing string count:
        tuning = [0] * num_strings
        self.fretboard = Fretboard(self, num_frets=max_fret, tuning=tuning, enable_click_reporting=False)
        self.fretboard.pack(fill="both", expand=True, padx=10, pady=10)

        self._apply_heatmap()

    def _apply_heatmap(self) -> None:
        # value: 0..1 (1 = "bad" or "needs focus") -> we use 1-accuracy
        values: dict[tuple[int, int], float] = {}
        for s in range(self.num_strings):
            for f in range(self.max_fret + 1):
                data = self.stats.by_position.get(_pos_key(s, f))
                if not data:
                    values[(s, f)] = 1.0  # unseen -> highlight
                    continue
                attempts = int(data.get("attempts", 0))
                correct = int(data.get("correct", 0))
                if attempts <= 0:
                    values[(s, f)] = 1.0
                else:
                    acc = correct / attempts
                    values[(s, f)] = float(1.0 - acc)

        self.fretboard.set_heatmap(values)
