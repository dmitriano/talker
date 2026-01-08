# Talker Agent Notes

## Project summary
- PySide6 + QML desktop app for Russian text-to-speech using Silero via torch.hub.
- UI entry point is `Main.qml` loaded by `say.py`, which registers `TtsBridge` as `tts`.
- Phrase storage uses `phrases.sqlite3` in `src/` with `categories` and `phrases` tables.

## Running
- From `src/`: `python say.py` (first run downloads the model via torch.hub).
- Required deps: torch, PySide6, sounddevice, numpy.

## Architecture
- `say.py`: bootstraps model, sets QML context.
- `tts_bridge.py`: Qt bridge, signals/properties, SQLite CRUD, QThreadPool orchestration.
- `tts_task.py`: plays audio via sounddevice.
- `tts_save_task.py`: saves WAV files to `recordings/`.

## Concurrency + audio
- `TtsBridge` uses `QThreadPool` with max 1 thread and a `QMutex`.
- `TtsTask` and `TtsSaveTask` must always `unlock()` in `finally` to avoid deadlocks.
- Sample rate constant is duplicated in `tts_task.py` and `tts_save_task.py`; keep them in sync.

## Data + UX rules
- The default category literal is hardcoded in `tts_bridge.py` and used in DB seed and delete guard; keep those usages aligned.
- `save` and `saveAudio` both increment `say_count`; keep that behavior unless changing UX explicitly.
- UI strings are mostly Russian; preserve existing tone if editing text.

## Editing tips
- Expose new QML bindings via `QtCore.Property` + signal or `QtCore.Slot` in `TtsBridge`.
- After changing DB schema, update `_init_db` migration logic so existing files keep working.
