import random
import sys
from functools import wraps

import redis
from environs import Env
from telegram import ChatAction, ReplyKeyboardMarkup, Update
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
)

from utils import build_collection, check

sys.stdout.reconfigure(encoding="utf-8")


def send_typing_action(func):
    """Показывает «печатает...», пока работает хендлер."""

    @wraps(func)
    def wrapper(update, context, *args, **kwargs):
        context.bot.send_chat_action(
            chat_id=update.effective_message.chat_id,
            action=ChatAction.TYPING,
        )
        return func(update, context, *args, **kwargs)

    return wrapper


def start(update: Update, context: CallbackContext) -> None:
    """Отвечает на /start и показывает клавиатуру."""
    user = update.effective_user

    custom_keyboard = [
        ["Новый вопрос", "Сдаться"],
        ["Мой счёт"],
    ]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)

    update.message.reply_text(
        text=f"Привет, {user.first_name}! Я бот для игры Викторина!",
        reply_markup=reply_markup,
    )


def new_question(update: Update, context: CallbackContext) -> None:
    """Отправляет случайный вопрос из коллекции."""
    quiz_collection = context.bot_data["quiz"]
    question, answer = random.choice(list(quiz_collection.items()))

    user_id = update.effective_user.id
    redis_connect = context.bot_data["redis"]
    redis_connect.set(f"user:{user_id}:current_question", question)
    redis_connect.set(f"user:{user_id}:current_answer", answer)

    update.message.reply_text(question)


def clear_current_question(user_id: int, redis_connect) -> None:
    """Удаляет текущий вопрос пользователя из Redis."""
    redis_connect.delete(
        f"user:{user_id}:current_question",
        f"user:{user_id}:current_answer",
    )


@send_typing_action
def check_answer(update: Update, context: CallbackContext) -> None:
    """Проверяет ответ пользователя."""
    user_id = update.effective_user.id
    redis_connect = context.bot_data["redis"]

    current_answer = redis_connect.get(f"user:{user_id}:current_answer")

    if current_answer is None:
        update.message.reply_text("Сначала нажми «Новый вопрос».")
        return

    result = check(update.message.text, current_answer)

    if result == "correct":
        update.message.reply_text(f"Правильно! Ответ: {current_answer}")
        clear_current_question(user_id, redis_connect)
    elif result == "close":
        update.message.reply_text("Близко! Попробуй ещё раз.")
    else:
        update.message.reply_text(f"Неверно. Правильный ответ: {current_answer}")
        clear_current_question(user_id, redis_connect)


@send_typing_action
def button_handler(update: Update, context: CallbackContext) -> None:
    """Реагирует на нажатия кнопок."""
    text = update.message.text

    if text == "Новый вопрос":
        new_question(update, context)
    elif text == "Сдаться":
        redis_connect = context.bot_data["redis"]
        user_id = update.effective_user.id
        answer = redis_connect.get(f"user:{user_id}:current_answer")

        if answer is None:
            update.message.reply_text("Сначала нажми «Новый вопрос».")
        else:
            update.message.reply_text(f"Правильный ответ: {answer}")
            clear_current_question(user_id, redis_connect)
    elif text == "Мой счёт":
        update.message.reply_text("ТУ ДУ — мой счёт")


def main() -> None:
    """Запускает бота."""
    env = Env()
    env.read_env()
    token = env.str("TG_BOT_TOKEN")
    redis_connect = redis.Redis(host="localhost", port=6379, decode_responses=True)

    updater = Updater(token)

    dispatcher = updater.dispatcher
    dispatcher.bot_data["redis"] = redis_connect
    quiz_collection = build_collection("quiz-questions")
    updater.dispatcher.bot_data["quiz"] = quiz_collection

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(
        MessageHandler(
            Filters.regex("^(Новый вопрос|Сдаться|Мой счёт)$"),
            button_handler,
        )
    )

    dispatcher.add_handler(
        MessageHandler(Filters.text & ~Filters.command, check_answer)
    )

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
