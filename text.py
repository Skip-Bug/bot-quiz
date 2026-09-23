import re
import string

_PUNCT = str.maketrans("", "", string.punctuation + "«»—–…°·")


def normalize(text):
    """Приводит текст к сравнимому виду."""
    return text.strip().lower()


def clean_text(text):
    """Чистим вредные переносы и комментарии для ведущего."""
    if "[" in text:
        no_comments = re.sub(
            r"\[(?:чтецу|ведущему)[^\]]*\]\s*",
            "",
            text,
            flags=re.IGNORECASE,
        )
    else:
        no_comments = text

    no_breaks = re.sub(r"(?<![.!?:])\n", " ", no_comments)
    return no_breaks


def clean_answer(text):
    """Обрезка ответа до первого предложения."""
    text = text.strip()
    parts = re.split(r"(?<=[.!?])\s+", text, maxsplit=1)
    if len(parts) == 1:
        return text
    if len(parts[0]) <= 4:
        return text
    return parts[0].strip()


def fingerprint(text):
    """Грубый отпечаток текста: без регистра, пунктуации, ё/е, лишних пробелов."""
    no_case = text.lower().replace("ё", "е")
    no_punct = no_case.translate(_PUNCT)
    return " ".join(no_punct.split())
