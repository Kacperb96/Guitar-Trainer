# Guitar Trainer (Python)

A small Python app to help you learn notes on the guitar fretboard.
It includes:
- CLI training modes
- Tkinter GUI with:
  - Mode A (guess the note from a highlighted position)
  - Mode B (click all positions for a given note)
  - Adaptive Mode (focuses weak/unseen positions)
  - Heatmap (attempts/accuracy per fretboard position)
- Statistics saved to `stats.json`

## Requirements
- Python 3.11+ (Ubuntu often uses `python3`)
- Recommended: a virtual environment (venv)

---

## Setup (recommended way)

### 1) Create and activate venv
From the project root:

python3 -m venv .venv
source .venv/bin/activate

### 2) Install the project (editable)

This makes the src/ package importable and installs the CLI entry point.

python3 -m pip install -U pip
python3 -m pip install -e ".[dev]"

If python is not available on your system, always use python3.

Run
GUI (Start Menu)
guitar-trainer gui

or without the entry-point:

python3 -m guitar_trainer.app gui

CLI (terminal version)
guitar-trainer

or:

python3 -m guitar_trainer.app

Tests
python3 -m pytest

Project structure (simplified)
src/guitar_trainer/
  app.py                 # main entry point (CLI/GUI switch)
  cli.py                 # terminal UI
  core/                  # pure logic (notes, mapping, stats, adaptive)
  gui/                   # Tkinter UI (menu, fretboard, quiz, heatmap)
tests/

Notes

String numbering in GUI:

1 at the top = high e

6 at the bottom = low E

Statistics are stored in stats.json in the project root.