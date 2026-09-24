import time

import redis
import requests
import vk_api as vk
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkEventType, VkLongPoll
from vk_api.utils import get_random_id

from quiz_processing import get_random_question
from settings import REDIS_URL, VK_BOT_TOKEN
from utils import build_user_key, check_answer, clear_current_question

# TO DO добавить логер

PLATFORM = "vk"


def build_keyboard() -> str:
    """Собирает клавиатуру и возвращает её как строку для API."""
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("Новый вопрос", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button("Сдаться", color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button("Мой счёт", color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()


def send_message(vk_api, user_id, text, keyboard=None) -> None:
    """Отправляет сообщение, опционально с клавиатурой."""
    vk_api.messages.send(
        user_id=user_id,
        message=text,
        random_id=get_random_id(),
        keyboard=keyboard,
    )


def handle_new_question(vk_api, redis_connect, user_id) -> None:
    """Запускает новый вопрос."""
    current_question = redis_connect.get(
        build_user_key(PLATFORM, user_id, "current_question")
    )
    if current_question is not None:
        send_message(
            vk_api,
            user_id,
            f"Сначала ответь на текущий вопрос:\n\n{current_question}\n\n"
            f"Или нажми «Сдаться».",
        )
        return

    question, answer = get_random_question(redis_connect)
    redis_connect.set(build_user_key(PLATFORM, user_id, "current_question"), question)
    redis_connect.set(build_user_key(PLATFORM, user_id, "current_answer"), answer)
    send_message(vk_api, user_id, question)


def handle_solution_attempt(vk_api, redis_connect, user_id, text) -> None:
    """Проверяет ответ и озвучивает результат."""
    current_answer = redis_connect.get(
        build_user_key(PLATFORM, user_id, "current_answer")
    )
    if current_answer is None:
        send_message(vk_api, user_id, "Сначала нажми «Новый вопрос».")
        return

    result = check_answer(text, current_answer)
    if result == "correct":
        send_message(vk_api, user_id, f"Правильно! Ответ: {current_answer}")
        clear_current_question(PLATFORM, user_id, redis_connect)
    elif result == "close":
        send_message(vk_api, user_id, "Близко! Попробуй ещё раз.")
    else:
        send_message(
            vk_api,
            user_id,
            f"Неверно. Правильный ответ: {current_answer}",
        )
        clear_current_question(PLATFORM, user_id, redis_connect)


def handle_give_up(vk_api, redis_connect, user_id) -> None:
    """Показывает правильный ответ когда игрок сдался."""
    answer = redis_connect.get(build_user_key(PLATFORM, user_id, "current_answer"))
    if answer is None:
        send_message(vk_api, user_id, "Сначала нажми «Новый вопрос».")
        return
    send_message(vk_api, user_id, f"Правильный ответ: {answer}")
    clear_current_question(PLATFORM, user_id, redis_connect)


def handle_score(vk_api, user_id) -> None:
    """Показывает счёт (пока заглушка)."""
    send_message(vk_api, user_id, "ТУ ДУ — мой счёт")


def run_longpoll(longpoll, vk_api, redis_connect) -> None:
    """Входит в режим игры"""
    for event in longpoll.listen():
        if event.type != VkEventType.MESSAGE_NEW or not event.to_me:
            continue
        text = event.text.strip()
        user_id = event.user_id

        if not text:
            send_message(vk_api, user_id, "Я понимаю только текст 🙂")
            continue

        if text.lower() in ("начать", "start", "/start"):
            send_message(
                vk_api,
                user_id,
                "Привет! Я бот для игры Викторина!",
                keyboard=build_keyboard(),
            )
        elif text == "Новый вопрос":
            handle_new_question(vk_api, redis_connect, user_id)
        elif text == "Сдаться":
            handle_give_up(vk_api, redis_connect, user_id)
        elif text == "Мой счёт":
            handle_score(vk_api, user_id)
        else:
            handle_solution_attempt(vk_api, redis_connect, user_id, text)


def main():
    token = VK_BOT_TOKEN
    vk_session = vk.VkApi(token=token)
    vk_api = vk_session.get_api()

    redis_connect = redis.from_url(REDIS_URL, decode_responses=True)

    print("ВК бот запущен")
    while True:
        try:
            longpoll = VkLongPoll(vk_session)
            run_longpoll(longpoll, vk_api, redis_connect)
        except (vk.ApiHttpError, requests.exceptions.ConnectionError) as e:
            print(f"Сетевая ошибка: {e}. Переподключение через 5 секунд...")
            time.sleep(5)
        except KeyboardInterrupt:
            print("ВК бот остановлен пользователем")
            break
        except Exception as e:
            print(f"Ошибка ВК бота: {e}")
            break


if __name__ == "__main__":
    main()
