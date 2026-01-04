import sqlite3
from pathlib import Path

import torch
from PySide6 import QtCore

from tts_task import TtsTask


class TtsBridge(QtCore.QObject):
    autosaveChanged = QtCore.Signal()

    def __init__(self, tts_model: torch.nn.Module) -> None:
        super().__init__()
        self.tts_model = tts_model
        self.pool = QtCore.QThreadPool.globalInstance()
        self.pool.setMaxThreadCount(1)
        self.mutex = QtCore.QMutex()
        self._autosave = False
        self._db_path = Path(__file__).resolve().parent / "phrases.sqlite3"
        self._phrases_model = QtCore.QStringListModel()
        self._init_db()
        self._load_phrases()

    @QtCore.Property(QtCore.QObject, constant=True)
    def phrasesModel(self) -> QtCore.QObject:
        return self._phrases_model

    @QtCore.Property(bool, notify=autosaveChanged)
    def autosave(self) -> bool:
        return self._autosave

    @autosave.setter
    def autosave(self, value: bool) -> None:
        if self._autosave == value:
            return
        self._autosave = value
        self.autosaveChanged.emit()

    def _init_db(self) -> None:
        with sqlite3.connect(self._db_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS phrases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.commit()

    def _load_phrases(self) -> None:
        with sqlite3.connect(self._db_path) as connection:
            cursor = connection.execute(
                "SELECT text FROM phrases ORDER BY created_at DESC, id DESC"
            )
            rows = [row[0] for row in cursor.fetchall()]
        self._phrases_model.setStringList(rows)

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
        if not self.mutex.tryLock():
            return
        task = TtsTask(self.tts_model, text, self.mutex)
        self.pool.start(task)
