import json
import os
import random

from text import clean_answer, clean_text, fingerprint


def get_random_question(redis_connect):
    """Возвращает question, answer."""
    total = redis_connect.llen("quiz:questions")

    index = random.randint(0, total - 1)
    payload = redis_connect.lindex("quiz:questions", index)
    quiz = json.loads(payload)
    return quiz["q"], quiz["a"]


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
