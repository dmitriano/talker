import re


class LatinTransliterator:
    _MULTI_MAP = {
        "shch": "щ",
        "sch": "щ",
        "yo": "ё",
        "zh": "ж",
        "kh": "х",
        "ts": "ц",
        "ch": "ч",
        "sh": "ш",
        "yu": "ю",
        "ya": "я",
        "ye": "е",
        "je": "е",
    }
    _MULTI_KEYS = (
        "shch",
        "sch",
        "yo",
        "zh",
        "kh",
        "ts",
        "ch",
        "sh",
        "yu",
        "ya",
        "ye",
        "je",
    )
    _SINGLE_MAP = {
        "a": "а",
        "b": "б",
        "c": "ц",
        "d": "д",
        "e": "е",
        "f": "ф",
        "g": "г",
        "h": "х",
        "i": "и",
        "j": "й",
        "k": "к",
        "l": "л",
        "m": "м",
        "n": "н",
        "o": "о",
        "p": "п",
        "q": "к",
        "r": "р",
        "s": "с",
        "t": "т",
        "u": "у",
        "v": "в",
        "w": "в",
        "x": "кс",
        "y": "ы",
        "z": "з",
    }

    def __init__(self) -> None:
        self._latin_re = re.compile(r"[A-Za-z]+")

    def normalize(self, text: str) -> str:
        return self._latin_re.sub(self._replace, text)

    def _replace(self, match: re.Match[str]) -> str:
        return self._transliterate(match.group(0))

    def _transliterate(self, text: str) -> str:
        lowered = text.lower()
        result: list[str] = []
        idx = 0
        while idx < len(lowered):
            for key in self._MULTI_KEYS:
                if lowered.startswith(key, idx):
                    result.append(self._MULTI_MAP[key])
                    idx += len(key)
                    break
            else:
                ch = lowered[idx]
                result.append(self._SINGLE_MAP.get(ch, ch))
                idx += 1
        return "".join(result)
