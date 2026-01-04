import sys
from pathlib import Path

import numpy as np
import sounddevice as sd
import torch
from PySide6 import QtCore, QtGui, QtQml

# 1) Грузим из torch.hub (первый запуск скачает репозиторий/модели)
loaded = torch.hub.load(
    repo_or_dir="snakers4/silero-models",
    model="silero_tts",
    language="ru",
    speaker="v3_1_ru",
    trust_repo=True,  # чтобы не спрашивал в будущем
)

# 2) torch.hub иногда возвращает tuple: (model, example_text, ...)
#    Приводим к "model"
model = loaded[0] if isinstance(loaded, (tuple, list)) else loaded

# 3) Настройки
SPEAKER = "aidar"  # мужской
SAMPLE_RATE = 48000  # 24000/48000 зависит от модели, 48000 обычно ок


class TtsTask(QtCore.QRunnable):
    def __init__(self, tts_model: torch.nn.Module, text: str, mutex: QtCore.QMutex) -> None:
        super().__init__()
        self.tts_model = tts_model
        self.text = text
        self.mutex = mutex

    def run(self) -> None:
        try:
            audio = self.tts_model.apply_tts(
                text=self.text,
                speaker=SPEAKER,
                sample_rate=SAMPLE_RATE,
            )
            audio = audio.numpy().astype(np.float32)
            sd.play(audio, SAMPLE_RATE)
            sd.wait()
        finally:
            self.mutex.unlock()


class TtsBridge(QtCore.QObject):
    def __init__(self, tts_model: torch.nn.Module) -> None:
        super().__init__()
        self.tts_model = tts_model
        self.pool = QtCore.QThreadPool.globalInstance()
        self.pool.setMaxThreadCount(1)
        self.mutex = QtCore.QMutex()

    @QtCore.Slot(str)
    def say(self, text: str) -> None:
        text = text.strip()
        if not text:
            return
        if not self.mutex.tryLock():
            return
        task = TtsTask(self.tts_model, text, self.mutex)
        self.pool.start(task)


def main() -> int:
    app = QtGui.QGuiApplication(sys.argv)
    engine = QtQml.QQmlApplicationEngine()

    bridge = TtsBridge(model)
    engine.rootContext().setContextProperty("tts", bridge)

    qml_path = Path(__file__).resolve().parent / "Main.qml"
    engine.load(str(qml_path))
    if not engine.rootObjects():
        return 1

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
