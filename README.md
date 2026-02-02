# 🎸 Guitar Trainer

**Guitar Trainer** is an interactive application for learning note names on the guitar fretboard (and other stringed instruments).
It combines quiz-based learning, adaptive training, and a visual **heatmap** that shows exactly where you struggle.

The goal is not just to test knowledge, but to **build true fretboard awareness**.

---

## 🚀 Getting Started

### Virtual environment
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Start GUI
```bash
guitar-trainer gui
```

### Start CLI (terminal mode)
```bash
guitar-trainer
```

---

## 🧠 Core Idea

The program:
- asks questions about notes on the fretboard,
- records every answer,
- analyzes mistakes per **string, fret, and note**,
- visualizes weak spots using a heatmap,
- adapts future questions to your weaknesses.

You don’t just practice — you get **feedback-driven training**.

---

## 🎛️ Menu Settings

### Number of strings
Choose the number of strings for your instrument:
- Guitar: `6`
- Bass: `4`
- Extended range guitars: `7–12`

### Tuning
- Built-in presets (E Standard, Drop D, etc.)
- **Custom tuning** – enter notes from lowest to highest string  

Example:
```
E A D G B E
```

### Display
- **Sharps** → `F#, C#`
- **Flats** → `Gb, Db`

This affects **notation only**, not the logic.

### Max fret
Defines the fretboard range:
- `12` – one octave
- `24` – full modern fretboard

---

## 🎮 Practice Modes

---

### 🅰️ Mode A — Guess the Note

Classic note recognition.

- A single position on the fretboard is highlighted.
- Your task: **type the note name**.

Example:
> String 3, fret 5 → `C`

✔️ Correct → score increases  
❌ Wrong → correct note is shown

**Statistics collected:**
- accuracy per note
- accuracy per string and fret

---

### 🅱️ Mode B — Find All Positions

Whole-fretboard thinking.

- The program selects a **note** (e.g. `F`)
- Click **all positions** where that note appears (up to max fret)

After submitting:
- 🟢 green → correct
- 🔴 red → incorrect
- 🟠 orange → missing positions

Perfect for:
- breaking box-based thinking
- understanding note repetition across strings

---

### 🅲 Mode C — Note on Highlighted String ⭐

This mode mirrors a real-world guitar exercise.

- One **string is highlighted**
- One **note** is selected (e.g. `F`)
- Your task: **click the correct fret on that string**

If you make a mistake:
- 🔴 red → your choice
- 🟠 orange → correct fret(s)

At the bottom you can configure:
- number of frets,
- which strings are active,
- flats vs sharps display.

Great for:
- learning individual strings,
- navigation across the neck,
- improvisation preparation.

---

### 🔁 Adaptive Mode (Smart Mode A)

An intelligent version of Mode A.

The program:
- analyzes your past answers,
- **asks more questions where you make mistakes**,
- reduces repetition of already mastered areas.

This makes practice:
- faster,
- more focused,
- less repetitive.

---

### ⏱️ Practice Session (Timed)

Time-based training (e.g. 10 minutes).

- continuous questions,
- real-time statistics,
- optional training plans (accuracy or heatmap-driven).

At the end, you get a **practice summary**.

---

## 📊 Statistics

Statistics are stored **per profile**, based on:
- number of strings,
- tuning,
- practice mode.

This means:
- different guitars = separate progress,
- alternate tunings don’t mix results.

Recorded data includes:
- total attempts,
- correct answers,
- accuracy percentage,
- per-note stats,
- per-position (string + fret) stats.

---

## 🔥 Heatmap (Key Feature)

The heatmap shows **where you struggle on the fretboard**.

Color meaning:
- 🔵 **Blue** – little data or strong performance
- 🟡 **Yellow** – average accuracy
- 🔴 **Red** – frequent mistakes

How to use it:
1. Practice for a while
2. Click **Heatmap…**
3. Identify:
   - weak strings,
   - weak frets,
   - problem areas of the neck

This turns vague intuition into **precise diagnosis**.

---

## 🖥️ CLI Mode

Terminal-based alternative:
```bash
guitar-trainer
```

Modes:
- A – guess the note
- B – find all positions
- S – show stats
- R – reset stats

CLI and GUI **share the same logic and statistics**.

---

## 🧩 Who Is This For?

✔️ Guitarists who know chords but not the fretboard  
✔️ Players stuck in scale boxes  
✔️ Anyone learning a new tuning or instrument  
✔️ Musicians who want conscious note awareness  

---

## 📌 Future Ideas

- interval training,
- scale visualization,
- MIDI input,
- stats export,
- web version.

---

## ❤️ Author

Built with real guitar practice in mind — not just a theory quiz.

Issues, suggestions, and pull requests are welcome 🙂
