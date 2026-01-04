import torch
import sounddevice as sd
import numpy as np

# 1) Грузим из torch.hub (первый запуск скачает репозиторий/модели)
loaded = torch.hub.load(
    repo_or_dir="snakers4/silero-models",
    model="silero_tts",
    language="ru",
    speaker="v3_1_ru",
    trust_repo=True,   # чтобы не спрашивал в будущем
)

# 2) torch.hub иногда возвращает tuple: (model, example_text, ...)
#    Приводим к "model"
model = loaded[0] if isinstance(loaded, (tuple, list)) else loaded

# 3) Настройки
SPEAKER = "aidar"      # мужской
SAMPLE_RATE = 48000    # 24000/48000 зависит от модели, 48000 обычно ок

print("Silero TTS ready.")
print("Введите текст (exit — выход):")

while True:
    text = input("> ").strip()
    if text.lower() in ("exit", "quit"):
        break
    if not text:
        continue

    # 4) Генерация аудио
    audio = model.apply_tts(
        text=text,
        speaker=SPEAKER,
        sample_rate=SAMPLE_RATE
    )

    # 5) Проигрывание
    audio = audio.numpy().astype(np.float32)
    sd.play(audio, SAMPLE_RATE)
    sd.wait()
