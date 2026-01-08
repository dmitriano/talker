import sqlite3
from datetime import datetime
from pathlib import Path

import torch
from PySide6 import QtCore

from latin_transliterator import LatinTransliterator
from number_normalizer import NumberNormalizer
from tts_save_task import TtsSaveTask
from tts_task import TtsTask


class TtsBridge(QtCore.QObject):
    autosaveChanged = QtCore.Signal()
    categoriesChanged = QtCore.Signal()
    currentCategoryChanged = QtCore.Signal()
    playingChanged = QtCore.Signal()
    preparingChanged = QtCore.Signal()
    savingChanged = QtCore.Signal()
    speakerChanged = QtCore.Signal()
    speedChanged = QtCore.Signal()

    def __init__(self, tts_model: torch.nn.Module) -> None:
        super().__init__()
        self.tts_model = tts_model
        self.pool = QtCore.QThreadPool.globalInstance()
        self.pool.setMaxThreadCount(1)
        self.mutex = QtCore.QMutex()
        self._autosave = False
        self._playing = False
        self._preparing = False
        self._current_task: TtsTask | None = None
        self._saving = False
        self._current_save_task: TtsSaveTask | None = None
        self._db_path = Path(__file__).resolve().parent / "phrases.sqlite3"
        self._latin_transliterator = LatinTransliterator()
        self._number_normalizer = NumberNormalizer()
        self._phrases_model = QtCore.QStringListModel()
        self._categories_model = QtCore.QStringListModel()
        self._speakers_model = QtCore.QStringListModel()
        self._speaker = ""
        self._speed = 1.0
        self._categories: list[dict[str, int | str]] = []
        self._current_category = ""
        self._init_db()
        self._load_categories()
        self._load_phrases()
        self._load_speakers()

    @QtCore.Property(QtCore.QObject, constant=True)
    def phrasesModel(self) -> QtCore.QObject:
        return self._phrases_model

    @QtCore.Property(QtCore.QObject, constant=True)
    def categoriesModel(self) -> QtCore.QObject:
        return self._categories_model

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

    @QtCore.Property(bool, notify=preparingChanged)
    def preparing(self) -> bool:
        return self._preparing

    @QtCore.Property(bool, notify=savingChanged)
    def saving(self) -> bool:
        return self._saving

    @QtCore.Property(str, notify=currentCategoryChanged)
    def currentCategory(self) -> str:
        return self._current_category

    @QtCore.Slot(str)
    def setCurrentCategory(self, name: str) -> None:
        name = name.strip()
        if not name or name == self._current_category:
            return
        if not self._find_category_id(name):
            return
        self._current_category = name
        self.currentCategoryChanged.emit()
        self._load_phrases()

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

    @QtCore.Property(float, notify=speedChanged)
    def speed(self) -> float:
        return self._speed

    @speed.setter
    def speed(self, value: float) -> None:
        if value <= 0 or self._speed == value:
            return
        self._speed = value
        self.speedChanged.emit()

    def _set_playing(self, value: bool) -> None:
        if self._playing == value:
            return
        self._playing = value
        self.playingChanged.emit()

    def _set_preparing(self, value: bool) -> None:
        if self._preparing == value:
            return
        self._preparing = value
        self.preparingChanged.emit()

    def _set_saving(self, value: bool) -> None:
        if self._saving == value:
            return
        self._saving = value
        self.savingChanged.emit()

    def _next_audio_path(self) -> Path:
        base_dir = Path(__file__).resolve().parent / "recordings"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return base_dir / f"tts_{timestamp}.wav"

    def _init_db(self) -> None:
        with sqlite3.connect(self._db_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                )
                """
            )
            connection.execute(
                "INSERT OR IGNORE INTO categories(name) VALUES (?)",
                ("Разговор с Банком",),
            )
            cursor = connection.execute(
                "SELECT id FROM categories WHERE name = ?",
                ("Разговор с Банком",),
            )
            default_category_id = cursor.fetchone()[0]
            connection.execute(
                f"""
                CREATE TABLE IF NOT EXISTS phrases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    say_count INTEGER NOT NULL DEFAULT 0,
                    category_id INTEGER NOT NULL DEFAULT {default_category_id}
                )
                """
            )
            cursor = connection.execute("PRAGMA table_info(phrases)")
            columns = {row[1] for row in cursor.fetchall()}
            if "say_count" not in columns:
                connection.execute(
                    "ALTER TABLE phrases ADD COLUMN say_count INTEGER NOT NULL DEFAULT 0"
                )
            if "category_id" not in columns:
                connection.execute(
                    f"ALTER TABLE phrases ADD COLUMN category_id INTEGER NOT NULL DEFAULT {default_category_id}"
                )
            connection.execute(
                "UPDATE phrases SET category_id = ? WHERE category_id IS NULL",
                (default_category_id,),
            )
            connection.commit()

    def _load_phrases(self) -> None:
        category_id = self._find_category_id(self._current_category)
        if not category_id:
            self._phrases_model.setStringList([])
            return
        with sqlite3.connect(self._db_path) as connection:
            cursor = connection.execute(
                """
                SELECT text
                FROM phrases
                WHERE category_id = ?
                ORDER BY text COLLATE NOCASE ASC
                """,
                (category_id,),
            )
            rows = [row[0] for row in cursor.fetchall()]
        self._phrases_model.setStringList(rows)

    def _load_categories(self) -> None:
        with sqlite3.connect(self._db_path) as connection:
            cursor = connection.execute(
                "SELECT id, name FROM categories ORDER BY name COLLATE NOCASE ASC"
            )
            rows = cursor.fetchall()
        self._categories = [{"id": row[0], "name": row[1]} for row in rows]
        names = [row["name"] for row in self._categories]
        self._categories_model.setStringList(names)
        if not self._current_category:
            default = "Разговор с Банком"
            self._current_category = (
                default if default in names else names[0] if names else ""
            )
        elif self._current_category not in names and names:
            self._current_category = names[0]
        self.categoriesChanged.emit()
        self.currentCategoryChanged.emit()

    def _find_category_id(self, name: str) -> int | None:
        for category in self._categories:
            if category["name"] == name:
                return int(category["id"])
        return None

    def _load_speakers(self) -> None:
        speakers = list(getattr(self.tts_model, "speakers", []))
        speakers = sorted(speakers)
        self._speakers_model.setStringList(speakers)
        if not self._speaker and speakers:
            default_speaker = "aidar" if "aidar" in speakers else speakers[0]
            self._speaker = default_speaker

    def _save_phrase(self, text: str) -> None:
        category_id = self._find_category_id(self._current_category)
        if not category_id:
            return
        with sqlite3.connect(self._db_path) as connection:
            connection.execute(
                """
                INSERT INTO phrases(text, created_at, category_id)
                VALUES(?, CURRENT_TIMESTAMP, ?)
                ON CONFLICT(text)
                DO UPDATE SET created_at = CURRENT_TIMESTAMP, category_id = excluded.category_id
                """,
                (text, category_id),
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

    def _add_category(self, name: str) -> None:
        with sqlite3.connect(self._db_path) as connection:
            connection.execute("INSERT OR IGNORE INTO categories(name) VALUES (?)", (name,))
            connection.commit()
        self._load_categories()

    def _delete_category(self, name: str) -> None:
        if name == "Разговор с Банком":
            return
        category_id = self._find_category_id(name)
        if not category_id:
            return
        with sqlite3.connect(self._db_path) as connection:
            cursor = connection.execute(
                "SELECT id FROM categories WHERE name = ?",
                ("Разговор с Банком",),
            )
            default_category_id = cursor.fetchone()[0]
            connection.execute(
                "UPDATE phrases SET category_id = ? WHERE category_id = ?",
                (default_category_id, category_id),
            )
            connection.execute("DELETE FROM categories WHERE id = ?", (category_id,))
            connection.commit()
        if self._current_category == name:
            self._current_category = "Разговор с Банком"
            self.currentCategoryChanged.emit()
        self._load_categories()
        self._load_phrases()

    def _normalize_text(self, text: str) -> str:
        text = self._latin_transliterator.normalize(text)
        return self._number_normalizer.normalize(text)

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
    def addCategory(self, name: str) -> None:
        name = name.strip()
        if not name:
            return
        self._add_category(name)

    @QtCore.Slot(str)
    def removeCategory(self, name: str) -> None:
        name = name.strip()
        if not name:
            return
        self._delete_category(name)

    @QtCore.Slot(str)
    def say(self, text: str) -> None:
        text = text.strip()
        if not text:
            return
        spoken_text = self._normalize_text(text)
        if self._autosave:
            self._save_phrase(text)
        self._increment_phrase_count(text)
        if not self.mutex.tryLock():
            return
        self._set_preparing(True)
        self._set_playing(False)
        task = TtsTask(
            self.tts_model, spoken_text, self._speaker, self._speed, self.mutex
        )
        task.ready.connect(self._on_task_ready)
        task.finished.connect(self._on_task_finished)
        self._current_task = task
        self.pool.start(task)

    @QtCore.Slot(str)
    def saveAudio(self, text: str) -> None:
        text = text.strip()
        if not text:
            return
        spoken_text = self._normalize_text(text)
        if self._autosave:
            self._save_phrase(text)
        self._increment_phrase_count(text)
        if not self.mutex.tryLock():
            return
        output_path = self._next_audio_path()
        self._set_saving(True)
        task = TtsSaveTask(
            self.tts_model,
            spoken_text,
            self._speaker,
            self._speed,
            output_path,
            self.mutex,
        )
        task.finished.connect(self._on_save_finished)
        task.failed.connect(self._on_save_failed)
        self._current_save_task = task
        self.pool.start(task)

    @QtCore.Slot()
    def _on_task_finished(self) -> None:
        self._set_playing(False)
        self._set_preparing(False)
        self._current_task = None

    @QtCore.Slot()
    def _on_task_ready(self) -> None:
        self._set_preparing(False)
        self._set_playing(True)

    @QtCore.Slot(str)
    def _on_save_finished(self, _: str) -> None:
        self._set_saving(False)
        self._current_save_task = None

    @QtCore.Slot(str)
    def _on_save_failed(self, _: str) -> None:
        self._set_saving(False)
        self._current_save_task = None
