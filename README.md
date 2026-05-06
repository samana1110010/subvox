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

| Command               | Status      | Action                       |
| --------------------- | ----------- | ---------------------------- |
| `up`                  | Implemented | Move/page up                 |
| `down`                | Implemented | Move/page down               |
| `left`                | Implemented | Move cursor left             |
| `right`               | Implemented | Move cursor right            |
| `select`              | Implemented | Click/select                 |
| `social` / `whatsapp` | Implemented | Start WhatsApp workflow      |
| `stream` / `youtube`  | Implemented | Open YouTube                 |
| `music` / `spotify`   | Implemented | Open/play Spotify            |
| `focus <app>`         | Implemented | Focus a window/app           |
| `help` / `commands`   | Implemented | Show command list            |
| `exit` / `quit` / `q` | Implemented | Stop controller              |
| `update`              | Planned     | System/update workflow       |
| `scroll`              | Planned     | Toggle scroll mode           |
| `silence`             | Planned     | Ignore idle signal           |
| `reject`              | Planned     | Ignore noise/artifact signal |

---

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

## EMG Simulation Phase

Before moving to hardware, we are simulating the EMG signal flow using **LTspice** and building the signal-processing pipeline in **Python**.

We also plan to use public silent-speech EMG data only for the simulation phase.

Dataset:
[https://zenodo.org/records/4064409](https://zenodo.org/records/4064409)

Reference repo:
[https://github.com/dgaddy/silent_speech](https://github.com/dgaddy/silent_speech)

The final model will require our own collected 10-command EMG data.

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
