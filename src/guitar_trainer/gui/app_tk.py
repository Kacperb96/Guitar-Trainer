import tkinter as tk

from guitar_trainer.gui.fretboard import Fretboard


def run_gui(num_frets: int = 12) -> None:
    root = tk.Tk()
    root.title("Guitar Trainer - Fretboard")

    fb = Fretboard(root, num_frets=num_frets)
    fb.pack(padx=10, pady=10)

    root.mainloop()
