import os
import re
import string

from rapidfuzz import fuzz

_PUNCT = str.maketrans("", "", string.punctuation + "«»—–…°·")


def normalize(text):
    """Приводит текст к сравнимому виду."""
    return text.strip().lower()


def check_answer(user_answer, correct_answer):
    """Сравнивает ответы. Возвращает 'correct', 'close' или 'wrong'."""
    user_text = normalize(user_answer)
    correct_text = normalize(correct_answer)

    score = fuzz.token_sort_ratio(user_text, correct_text)

    if score >= 80:
        return "correct"
    if score >= 50:
        return "close"
    return "wrong"


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


def load_quiz(path):
    """Загружает вопросы из файла"""
    with open(path, "r", encoding="KOI8-R") as quiz_file:
        quiz_contents = quiz_file.read()
    return quiz_contents


def iter_blocks(contents):
    """Генератор непустых блоков из содержимого файла."""
    for block in contents.split("\n\n"):
        block = block.strip()
        if block:
            yield block


def extract_value(block):
    """Возвращает текст блока после первого двоеточия."""
    if ":" not in block:
        raise ValueError(f"Нет двоеточия в блоке: {block[:80]!r}")
    return block.split(":", 1)[1].strip()


def iter_qa(contents):
    """Генератор пар (вопрос, ответ) из содержимого файла."""
    current_question = None

    for block in iter_blocks(contents):
        if block.startswith("Вопрос"):
            current_question = clean_text(extract_value(block))
        elif block.startswith("Ответ") and current_question:
            answer = clean_answer(clean_text(extract_value(block)))
            yield current_question, answer
            current_question = None


def collect_dict(contents, seen):
    """Собирает словарь без дублей."""
    quiz = {}
    for question, answer in iter_qa(contents):
        duplicate_key = fingerprint(question)
        if duplicate_key not in seen:
            seen.add(duplicate_key)
            quiz[question] = answer
    return quiz


def build_collection(directory):
    """Создаёт сборник вопросов из всех .txt-файлов в директории."""
    quiz_collection = {}
    seen = set()

    for filename in sorted(os.listdir(directory)):
        if not filename.endswith(".txt"):
            continue

        path = os.path.join(directory, filename)
        try:
            file_questions = collect_dict(load_quiz(path), seen)
        except (OSError, UnicodeDecodeError) as error:
            print(f"Пропущен {filename}: {error}")
            continue

        quiz_collection.update(file_questions)

    return quiz_collection
