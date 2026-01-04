import sqlite3
from pathlib import Path

import torch
from PySide6 import QtCore

from tts_task import TtsTask


class TtsBridge(QtCore.QObject):
    autosaveChanged = QtCore.Signal()
    playingChanged = QtCore.Signal()
    speakerChanged = QtCore.Signal()

    def __init__(self, tts_model: torch.nn.Module) -> None:
        super().__init__()
        self.tts_model = tts_model
        self.pool = QtCore.QThreadPool.globalInstance()
        self.pool.setMaxThreadCount(1)
        self.mutex = QtCore.QMutex()
        self._autosave = False
        self._playing = False
        self._current_task: TtsTask | None = None
        self._db_path = Path(__file__).resolve().parent / "phrases.sqlite3"
        self._phrases_model = QtCore.QStringListModel()
        self._speakers_model = QtCore.QStringListModel()
        self._speaker = ""
        self._init_db()
        self._load_phrases()
        self._load_speakers()

    @QtCore.Property(QtCore.QObject, constant=True)
    def phrasesModel(self) -> QtCore.QObject:
        return self._phrases_model

    @QtCore.Property(QtCore.QObject, constant=True)
    def speakersModel(self) -> QtCore.QObject:
        return self._speakers_model

    @QtCore.Property(bool, notify=autosaveChanged)
    def autosave(self) -> bool:
        return self._autosave

    @autosave.setter
    def autosave(self, value: bool) -> None:
        if self._autosave == value:
            return
        self._autosave = value
        self.autosaveChanged.emit()

    @QtCore.Property(bool, notify=playingChanged)
    def playing(self) -> bool:
        return self._playing

    @QtCore.Property(str, notify=speakerChanged)
    def speaker(self) -> str:
        return self._speaker

    @speaker.setter
    def speaker(self, value: str) -> None:
        value = value.strip()
        if not value or self._speaker == value:
            return
        self._speaker = value
        self.speakerChanged.emit()

    def _set_playing(self, value: bool) -> None:
        if self._playing == value:
            return
        self._playing = value
        self.playingChanged.emit()

    def _init_db(self) -> None:
        with sqlite3.connect(self._db_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS phrases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    say_count INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            cursor = connection.execute("PRAGMA table_info(phrases)")
            columns = {row[1] for row in cursor.fetchall()}
            if "say_count" not in columns:
                connection.execute(
                    "ALTER TABLE phrases ADD COLUMN say_count INTEGER NOT NULL DEFAULT 0"
                )
            connection.commit()

    def _load_phrases(self) -> None:
        with sqlite3.connect(self._db_path) as connection:
            cursor = connection.execute(
                "SELECT text FROM phrases ORDER BY text COLLATE NOCASE ASC"
            )
            rows = [row[0] for row in cursor.fetchall()]
        self._phrases_model.setStringList(rows)

    def _load_speakers(self) -> None:
        speakers = list(getattr(self.tts_model, "speakers", []))
        speakers = sorted(speakers)
        self._speakers_model.setStringList(speakers)
        if not self._speaker and speakers:
            default_speaker = "aidar" if "aidar" in speakers else speakers[0]
            self._speaker = default_speaker

    def _save_phrase(self, text: str) -> None:
        with sqlite3.connect(self._db_path) as connection:
            connection.execute(
                """
                INSERT INTO phrases(text, created_at)
                VALUES(?, CURRENT_TIMESTAMP)
                ON CONFLICT(text) DO UPDATE SET created_at = CURRENT_TIMESTAMP
                """,
                (text,),
            )
            connection.commit()
        self._load_phrases()

    def _increment_phrase_count(self, text: str) -> None:
        with sqlite3.connect(self._db_path) as connection:
            connection.execute(
                "UPDATE phrases SET say_count = say_count + 1 WHERE text = ?",
                (text,),
            )
            connection.commit()

    def _delete_phrase(self, text: str) -> None:
        with sqlite3.connect(self._db_path) as connection:
            connection.execute("DELETE FROM phrases WHERE text = ?", (text,))
            connection.commit()
        self._load_phrases()

    @QtCore.Slot(str)
    def save(self, text: str) -> None:
        text = text.strip()
        if not text:
            return
        self._save_phrase(text)

    @QtCore.Slot(str)
    def removePhrase(self, text: str) -> None:
        text = text.strip()
        if not text:
            return
        self._delete_phrase(text)

    @QtCore.Slot(str)
    def say(self, text: str) -> None:
        text = text.strip()
        if not text:
            return
        if self._autosave:
            self._save_phrase(text)
        self._increment_phrase_count(text)
        if not self.mutex.tryLock():
            return
        self._set_playing(True)
        task = TtsTask(self.tts_model, text, self._speaker, self.mutex)
        task.finished.connect(self._on_task_finished)
        self._current_task = task
        self.pool.start(task)

    @QtCore.Slot()
    def _on_task_finished(self) -> None:
        self._set_playing(False)
        self._current_task = None
