# Talker

Desktop TTS app built with PySide6 + QML. It uses Silero via `torch.hub` and
stores phrases in a local SQLite database.

## Requirements

- Python 3.10+ (3.9+ likely works, but 3.10+ is recommended)
- Python packages: `torch`, `PySide6`, `sounddevice`, `numpy`

## Install

From `src/`:

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install torch PySide6 sounddevice numpy
```

Note: the first run downloads the Silero model via `torch.hub`.

## Run

From `src/`:

```bash
python say.py
```

## Data

- `phrases.sqlite3` stores categories and phrases.
- `recordings/` stores generated WAV files.
