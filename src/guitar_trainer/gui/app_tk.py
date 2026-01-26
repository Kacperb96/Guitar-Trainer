import tkinter as tk

from guitar_trainer.core.stats import load_stats
from guitar_trainer.gui.menu_tk import MenuFrame
from guitar_trainer.gui.quiz_tk import NoteQuizFrame, PositionsQuizFrame

STATS_PATH = "stats.json"


def run_gui() -> None:
    root = tk.Tk()
    root.title("Guitar Trainer – GUI")

    def show_menu() -> None:
        for child in root.winfo_children():
            child.destroy()

        menu = MenuFrame(root, stats_path=STATS_PATH, on_start=start_quiz)
        menu.pack(padx=12, pady=12)

    def start_quiz(mode: str, num_questions: int, max_fret: int) -> None:
        for child in root.winfo_children():
            child.destroy()

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

    show_menu()
    root.mainloop()
