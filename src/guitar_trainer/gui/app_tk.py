import tkinter as tk

from guitar_trainer.core.stats import load_stats
from guitar_trainer.gui.quiz_tk import NoteQuizFrame, PositionsQuizFrame

STATS_PATH = "stats.json"


def run_gui(mode: str = "A", num_questions: int = 10, max_fret: int = 12) -> None:
    """
    mode: "A" or "B"
    """
    mode = mode.upper().strip()
    if mode not in {"A", "B"}:
        mode = "A"

    root = tk.Tk()
    root.title(f"Guitar Trainer – GUI Mode {mode}")

    stats = load_stats(STATS_PATH)

    if mode == "A":
        frame = NoteQuizFrame(
            root,
            stats=stats,
            stats_path=STATS_PATH,
            num_questions=num_questions,
            max_fret=max_fret,
        )
    else:
        frame = PositionsQuizFrame(
            root,
            stats=stats,
            stats_path=STATS_PATH,
            num_questions=max(1, num_questions // 2),  # Mode B is heavier; default fewer
            max_fret=max_fret,
        )

    frame.pack(padx=12, pady=12)
    root.mainloop()
