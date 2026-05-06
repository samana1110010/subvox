Copy this shorter version into GitHub’s `README.md`:

````markdown
# SubVox

**SubVox** is a low-cost EMG-based assistive control project that aims to use silent/subvocal command signals to control desktop automation workflows.

The project is currently in the **software automation + EMG simulation phase**. Hardware integration will be added after the simulation and signal-processing pipeline is stable.

---

## Purpose

SubVox is being built as a hands-free interaction system for users who may have difficulty using conventional input methods.

Instead of recognizing full silent speech, the project focuses on a small set of trained commands such as navigation, social, streaming, music, silence, and reject.

---

## Workflow

```text
EMG signal
    ↓
signal processing
    ↓
command classification
    ↓
automation controller
    ↓
desktop/app action
````

Current prototype:

```text
terminal command
    ↓
main.py
    ↓
automation module
    ↓
app/browser action
```

Future version:

```text
EMG classifier output
    ↓
main.py
    ↓
automation module
    ↓
desktop/app action
```

---

## Current Features

* WhatsApp Web automation
* Unread DM scanning
* Recent chat context extraction
* Local LLM-based reply generation
* YouTube opening workflow
* Spotify opening/playback workflow
* Basic navigation commands

---

## Command Set

These are the 10 main commands planned for SubVox:

| Command | Action |
|---|---|
| `left` | Navigate/move left |
| `right` | Navigate/move right |
| `up` | Navigate/move up |
| `down` | Navigate/move down |
| `select` | Confirm/click/select |
| `scroll` | Toggle scroll mode |
| `music` | Open/play Spotify |
| `stream` | Open YouTube/streaming workflow |
| `social` | Start WhatsApp/social workflow |
| `update` | Trigger system/update workflow |

Additional safety classes planned later:

| Class | Action |
|---|---|
| `silence` | Ignore idle/no-command state |
| `reject` | Ignore invalid/noisy signal |

## WhatsApp Workflow

```text
Open WhatsApp Web
    ↓
Scan unread direct messages
    ↓
Open unread chat
    ↓
Extract recent chat context
    ↓
Generate reply using local LLM
    ↓
Send response
```

---

## Project Structure

```text
subvox/
├── agent/
├── config/
├── tools/
│   ├── social.py
│   ├── stream_tools.py
│   ├── media_tools.py
│   └── nav_tools.py
├── main.py
├── setup.py
├── requirements.txt
└── README.md
```

---

## Tech Stack

* Python
* Playwright
* Ollama
* Qwen / TinyLlama
* Browser automation
* LTspice
* Public EMG datasets for simulation

---

## Setup

```bash
git clone https://github.com/samana1110010/subvox.git
cd subvox
pip install -r requirements.txt
playwright install chromium
python setup.py
python main.py
```

---

## Requirements

```text
playwright
ollama
requests
pyautogui
pygetwindow
```

---

## LLM Setup

The WhatsApp workflow uses Ollama.

Linux:

```bash
ollama pull qwen2.5:7b
```

Windows:

```bash
ollama pull tinyllama
```

---

## Planned Hardware Flow

```text
Electrodes
    ↓
BioAmp
    ↓
ADC / microcontroller
    ↓
Python
    ↓
command classifier
    ↓
automation controller
```

---

## Research Direction

SubVox focuses on:

1. Low-cost EMG-based control
2. Personalized calibration
3. Human-in-the-loop automation

---

## Current Limitations

* Command input is currently terminal-based.
* Navigation and window focus handling need improvement.
* WhatsApp Web selectors may change.
* EMG hardware is not connected yet.
* EMG classification is still in the simulation phase.

---

## Future Work

* Complete EMG simulation
* Build the signal-processing pipeline
* Start hardware testing step by step
* Collect personalized EMG command data
* Train a 10-command classifier
* Connect EMG classifier output to the automation controller

---

## Disclaimer

This project is experimental and intended for learning, research, and prototyping.

```
```
