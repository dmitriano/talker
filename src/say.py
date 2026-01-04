import sys
from pathlib import Path
import torch
from PySide6 import QtGui, QtQml

from tts_bridge import TtsBridge

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
