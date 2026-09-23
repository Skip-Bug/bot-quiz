from rapidfuzz import fuzz

from text import normalize


def user_key(platform, user_id, name):
    return f"{platform}:user:{user_id}:{name}"


def clear_current_question(platform, user_id, redis_connect):
    redis_connect.delete(
        user_key(platform, user_id, "current_question"),
        user_key(platform, user_id, "current_answer"),
    )


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
