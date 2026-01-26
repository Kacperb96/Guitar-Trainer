import tkinter as tk

from guitar_trainer.core.stats import load_stats
from guitar_trainer.gui.menu_tk import MenuFrame
from guitar_trainer.gui.quiz_tk import NoteQuizFrame, PositionsQuizFrame
from guitar_trainer.gui.stats_view_tk import StatsHeatmapFrame

STATS_PATH = "stats.json"


def run_gui() -> None:
    root = tk.Tk()
    root.title("Guitar Trainer – GUI")

    def clear_root() -> None:
        for child in root.winfo_children():
            child.destroy()

    def show_menu() -> None:
        clear_root()
        menu = MenuFrame(
            root,
            stats_path=STATS_PATH,
            on_start=start_quiz,
            on_heatmap=show_heatmap,
        )
        menu.pack(padx=12, pady=12)

    def start_quiz(mode: str, num_questions: int, max_fret: int) -> None:
        clear_root()
        stats = load_stats(STATS_PATH)

        if mode == "A":
            frame = NoteQuizFrame(
                root,
                stats=stats,
                stats_path=STATS_PATH,
                num_questions=num_questions,
                max_fret=max_fret,
                on_back=show_menu,
            )
        else:
            frame = PositionsQuizFrame(
                root,
                stats=stats,
                stats_path=STATS_PATH,
                num_questions=num_questions,
                max_fret=max_fret,
                on_back=show_menu,
            )

        frame.pack(padx=12, pady=12)

    def show_heatmap(max_fret: int) -> None:
        clear_root()
        stats = load_stats(STATS_PATH)
        frame = StatsHeatmapFrame(
            root,
            stats=stats,
            max_fret=max_fret,
            on_back=show_menu,
        )
        frame.pack(padx=12, pady=12)

    show_menu()
    root.mainloop()
