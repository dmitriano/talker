import inspect

import numpy as np
import sounddevice as sd
import torch
from PySide6 import QtCore
SAMPLE_RATE = 48000  # 24000/48000 зависит от модели, 48000 обычно ок


class TtsTask(QtCore.QObject, QtCore.QRunnable):
    finished = QtCore.Signal()

    def __init__(
        self,
        tts_model: torch.nn.Module,
        text: str,
        speaker: str,
        speed: float,
        mutex: QtCore.QMutex,
    ) -> None:
        QtCore.QObject.__init__(self)
        QtCore.QRunnable.__init__(self)
        self.tts_model = tts_model
        self.text = text
        self.speaker = speaker
        self.speed = speed
        self.mutex = mutex

    def run(self) -> None:
        try:
            apply_tts = self.tts_model.apply_tts
            kwargs = {
                "text": self.text,
                "speaker": self.speaker,
                "sample_rate": SAMPLE_RATE,
            }
            if "speed" in inspect.signature(apply_tts).parameters:
                kwargs["speed"] = self.speed
            audio = apply_tts(**kwargs)
            audio = audio.numpy().astype(np.float32)
            sample_rate = SAMPLE_RATE
            if "speed" not in kwargs and self.speed != 1.0:
                sample_rate = int(SAMPLE_RATE * self.speed)
            sd.play(audio, sample_rate)
            sd.wait()
        finally:
            self.mutex.unlock()
            self.finished.emit()
