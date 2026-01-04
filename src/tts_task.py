import numpy as np
import sounddevice as sd
import torch
from PySide6 import QtCore

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
