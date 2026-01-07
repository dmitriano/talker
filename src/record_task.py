import threading
import time
import wave
from pathlib import Path

import numpy as np
import sounddevice as sd
from PySide6 import QtCore

DEFAULT_SAMPLE_RATE = 48000
DEFAULT_CHANNELS = 1


class RecordingTask(QtCore.QObject, QtCore.QRunnable):
    finished = QtCore.Signal(str)
    failed = QtCore.Signal(str)

    def __init__(
        self,
        output_path: Path,
        mutex: QtCore.QMutex,
        stop_event: threading.Event,
        sample_rate: int = DEFAULT_SAMPLE_RATE,
        channels: int = DEFAULT_CHANNELS,
    ) -> None:
        QtCore.QObject.__init__(self)
        QtCore.QRunnable.__init__(self)
        self.output_path = output_path
        self.mutex = mutex
        self.stop_event = stop_event
        self.sample_rate = sample_rate
        self.channels = channels
        self._chunks: list[np.ndarray] = []
        self._lock = threading.Lock()

    def run(self) -> None:
        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="float32",
                callback=self._on_audio,
            ):
                while not self.stop_event.is_set():
                    time.sleep(0.1)
            self._write_wav()
            self.finished.emit(str(self.output_path))
        except Exception as exc:
            self.failed.emit(str(exc))
        finally:
            self.mutex.unlock()

    def _on_audio(self, indata: np.ndarray, frames: int, time_info, status) -> None:
        if status:
            return
        with self._lock:
            self._chunks.append(indata.copy())

    def _write_wav(self) -> None:
        with self._lock:
            if not self._chunks:
                samples = np.zeros((0, self.channels), dtype=np.float32)
            else:
                samples = np.concatenate(self._chunks, axis=0)
        samples = np.clip(samples, -1.0, 1.0)
        pcm = (samples * 32767).astype(np.int16)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(self.output_path), "wb") as wave_file:
            wave_file.setnchannels(self.channels)
            wave_file.setsampwidth(2)
            wave_file.setframerate(self.sample_rate)
            wave_file.writeframes(pcm.tobytes())
