import os


def load_quiz(path):
    """Загружает вопросы из файла"""
    with open(path, "r", encoding="KOI8-R") as quiz_file:
        quiz_contents = quiz_file.read()
    return quiz_contents


def collect_dict(quiz_contents):
    """Собирает вопросы и ответы в словарь"""
    blocks = quiz_contents.split("\n\n")

    quiz = {}
    current_question = None

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        if block.startswith("Вопрос"):
            current_question = block.split(":", 1)[1].strip()
        elif block.startswith("Ответ") and current_question:
            answer = block.split(":", 1)[1].strip()
            quiz[current_question] = answer
            current_question = None
    return quiz


def build_collection(directory):
    """Создаёт сборник вопросов из всех .txt-файлов в директории."""
    quiz_collection = {}

    for filename in os.listdir(directory):
        if not filename.endswith(".txt"):
            continue

        path = os.path.join(directory, filename)
        try:
            file_questions = collect_dict(load_quiz(path))
        except (OSError, UnicodeDecodeError) as error:
            print(f"Пропущен {filename}: {error}")
            continue

        quiz_collection.update(file_questions)

    return quiz_collection


def main():

    quiz_collection = build_collection("quiz-questions")

    print(f"Всего вопросов: {len(quiz_collection)}")


if __name__ == "__main__":
    main()
