import re


class NumberNormalizer:
    _DIGIT_WORDS = (
        "ноль",
        "один",
        "два",
        "три",
        "четыре",
        "пять",
        "шесть",
        "семь",
        "восемь",
        "девять",
    )
    _ONES = (
        "",
        "один",
        "два",
        "три",
        "четыре",
        "пять",
        "шесть",
        "семь",
        "восемь",
        "девять",
    )
    _ONES_FEM = (
        "",
        "одна",
        "две",
        "три",
        "четыре",
        "пять",
        "шесть",
        "семь",
        "восемь",
        "девять",
    )
    _TEENS = (
        "десять",
        "одиннадцать",
        "двенадцать",
        "тринадцать",
        "четырнадцать",
        "пятнадцать",
        "шестнадцать",
        "семнадцать",
        "восемнадцать",
        "девятнадцать",
    )
    _TENS = (
        "",
        "",
        "двадцать",
        "тридцать",
        "сорок",
        "пятьдесят",
        "шестьдесят",
        "семьдесят",
        "восемьдесят",
        "девяносто",
    )
    _HUNDREDS = (
        "",
        "сто",
        "двести",
        "триста",
        "четыреста",
        "пятьсот",
        "шестьсот",
        "семьсот",
        "восемьсот",
        "девятьсот",
    )
    _GROUPS = [
        (None, False),
        (("тысяча", "тысячи", "тысяч"), True),
        (("миллион", "миллиона", "миллионов"), False),
        (("миллиард", "миллиарда", "миллиардов"), False),
        (("триллион", "триллиона", "триллионов"), False),
    ]

    def __init__(self) -> None:
        self._digit_re = re.compile(r"\d+")

    def normalize(self, text: str) -> str:
        return self._digit_re.sub(self._replace, text)

    def _replace(self, match: re.Match[str]) -> str:
        return self._number_to_words(match.group(0))

    def _plural_form(self, value: int, forms: tuple[str, str, str]) -> str:
        value %= 100
        if 11 <= value <= 19:
            return forms[2]
        value %= 10
        if value == 1:
            return forms[0]
        if 2 <= value <= 4:
            return forms[1]
        return forms[2]

    def _triplet_to_words(self, value: int, feminine: bool) -> list[str]:
        words: list[str] = []
        hundreds = value // 100
        tens = (value // 10) % 10
        ones = value % 10
        if hundreds:
            words.append(self._HUNDREDS[hundreds])
        if tens == 1:
            words.append(self._TEENS[ones])
            return words
        if tens:
            words.append(self._TENS[tens])
        if ones:
            ones_words = self._ONES_FEM if feminine else self._ONES
            words.append(ones_words[ones])
        return words

    def _spell_digits(self, number: str) -> str:
        return " ".join(self._DIGIT_WORDS[int(ch)] for ch in number)

    def _number_to_words(self, number: str) -> str:
        if len(number) > 1 and number.startswith("0"):
            return self._spell_digits(number)
        try:
            value = int(number)
        except ValueError:
            return number
        if value == 0:
            return self._DIGIT_WORDS[0]
        groups: list[int] = []
        while value > 0:
            groups.append(value % 1000)
            value //= 1000
        if len(groups) > len(self._GROUPS):
            return self._spell_digits(number)
        words: list[str] = []
        for idx in range(len(groups) - 1, -1, -1):
            group_value = groups[idx]
            if group_value == 0:
                continue
            group_name, feminine = self._GROUPS[idx]
            words.extend(self._triplet_to_words(group_value, feminine))
            if group_name:
                words.append(self._plural_form(group_value, group_name))
        return " ".join(words)
