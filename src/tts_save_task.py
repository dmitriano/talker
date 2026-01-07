import inspect
import wave
from pathlib import Path

import numpy as np
import torch
from PySide6 import QtCore

SAMPLE_RATE = 48000  # 24000/48000 зависит от модели, 48000 обычно ок


class TtsSaveTask(QtCore.QObject, QtCore.QRunnable):
    finished = QtCore.Signal(str)
    failed = QtCore.Signal(str)

    def __init__(
        self,
        tts_model: torch.nn.Module,
        text: str,
        speaker: str,
        speed: float,
        output_path: Path,
        mutex: QtCore.QMutex,
    ) -> None:
        QtCore.QObject.__init__(self)
        QtCore.QRunnable.__init__(self)
        self.tts_model = tts_model
        self.text = text
        self.speaker = speaker
        self.speed = speed
        self.output_path = output_path
        self.mutex = mutex

    def run(self) -> None:
        try:
            audio, sample_rate = self._synthesize()
            self._write_wav(audio, sample_rate)
            self.finished.emit(str(self.output_path))
        except Exception as exc:
            self.failed.emit(str(exc))
        finally:
            self.mutex.unlock()

    def _synthesize(self) -> tuple[np.ndarray, int]:
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
        if audio.size:
            tail_silence = np.zeros(int(SAMPLE_RATE * 0.05), dtype=np.float32)
            audio = np.concatenate([audio, tail_silence])
        sample_rate = SAMPLE_RATE
        if "speed" not in kwargs and self.speed != 1.0:
            sample_rate = int(SAMPLE_RATE * self.speed)
        return audio, sample_rate

    def _write_wav(self, audio: np.ndarray, sample_rate: int) -> None:
        audio = np.clip(audio, -1.0, 1.0)
        pcm = (audio * 32767).astype(np.int16)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(self.output_path), "wb") as wave_file:
            wave_file.setnchannels(1)
            wave_file.setsampwidth(2)
            wave_file.setframerate(sample_rate)
            wave_file.writeframes(pcm.tobytes())
