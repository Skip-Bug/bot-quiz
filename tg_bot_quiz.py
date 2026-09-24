import sys
from enum import Enum, auto
from functools import wraps
from typing import Callable

import redis
from telegram import ChatAction, ReplyKeyboardMarkup, Update
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    ConversationHandler,
    Filters,
    MessageHandler,
    Updater,
)

from quiz_processing import get_random_question
from settings import REDIS_URL, TG_BOT_TOKEN
from utils import build_user_key, check_answer, clear_current_question

sys.stdout.reconfigure(encoding="utf-8")

PLATFORM = "tg"


# TO DO добавить логер
class State(Enum):
    CHOOSING = auto()
    ANSWERING = auto()


def send_typing_action(func) -> Callable:
    """Показывает «печатает...», пока работает хендлер."""

    @wraps(func)
    def wrapper(update, context, *args, **kwargs):
        context.bot.send_chat_action(
            chat_id=update.effective_message.chat_id,
            action=ChatAction.TYPING,
        )
        return func(update, context, *args, **kwargs)

    return wrapper


def start(update: Update, context: CallbackContext) -> State:
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
    return State.CHOOSING


@send_typing_action
def handle_new_question_request(
    update: Update,
    context: CallbackContext,
) -> State:
    """Отправляет случайный вопрос и переходит в ANSWERING."""
    user_id = update.effective_user.id
    redis_connect = context.bot_data["redis"]
    current_question = redis_connect.get(
        build_user_key(PLATFORM, user_id, "current_question")
    )
    if current_question is not None:
        update.message.reply_text(
            f"Сначала ответь на текущий вопрос:\n\n{current_question}\n\n"
            f"Или нажми «Сдаться»."
        )
        return State.ANSWERING

    question, answer = get_random_question(redis_connect)
    redis_connect.set(build_user_key(PLATFORM, user_id, "current_question"), question)
    redis_connect.set(build_user_key(PLATFORM, user_id, "current_answer"), answer)

    update.message.reply_text(question)
    return State.ANSWERING


@send_typing_action
def handle_solution_attempt(update: Update, context: CallbackContext) -> State:
    """Проверяет ответ и озвучивает результат."""
    user_id = update.effective_user.id
    redis_connect = context.bot_data["redis"]

    current_answer = redis_connect.get(
        build_user_key(PLATFORM, user_id, "current_answer")
    )
    if current_answer is None:
        update.message.reply_text("Сначала нажми «Новый вопрос».")
        return State.CHOOSING

    result = check_answer(update.message.text, current_answer)

    if result == "correct":
        update.message.reply_text(f"Правильно! Ответ: {current_answer}")
        clear_current_question(PLATFORM, user_id, redis_connect)
        return State.CHOOSING

    if result == "close":
        update.message.reply_text("Близко! Попробуй ещё раз.")
        return State.ANSWERING

    update.message.reply_text(f"Неверно. Правильный ответ: {current_answer}")
    clear_current_question(PLATFORM, user_id, redis_connect)
    return State.CHOOSING


@send_typing_action
def handle_give_up(update: Update, context: CallbackContext) -> State:
    """Показывает правильный ответ когда игрок сдался."""
    user_id = update.effective_user.id
    redis_connect = context.bot_data["redis"]

    answer = redis_connect.get(build_user_key(PLATFORM, user_id, "current_answer"))
    if answer is None:
        update.message.reply_text("Сначала нажми «Новый вопрос».")
        return State.CHOOSING

    update.message.reply_text(f"Правильный ответ: {answer}")
    clear_current_question(PLATFORM, user_id, redis_connect)
    return State.CHOOSING


@send_typing_action
def handle_score(update: Update, context: CallbackContext) -> None:
    """Показывает счёт (пока заглушка)."""
    update.message.reply_text("ТУ ДУ — мой счёт")


def build_conv_handler() -> ConversationHandler:
    """Собирает ConversationHandler с двумя состояниями."""
    return ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(
                Filters.regex("^Новый вопрос$"),
                handle_new_question_request,
            ),
        ],
        states={
            State.CHOOSING: [
                MessageHandler(
                    Filters.regex("^Новый вопрос$"),
                    handle_new_question_request,
                ),
                MessageHandler(Filters.regex("^Сдаться$"), handle_give_up),
                MessageHandler(Filters.regex("^Мой счёт$"), handle_score),
            ],
            State.ANSWERING: [
                MessageHandler(
                    Filters.regex("^Новый вопрос$"),
                    handle_new_question_request,
                ),
                MessageHandler(Filters.regex("^Сдаться$"), handle_give_up),
                MessageHandler(Filters.regex("^Мой счёт$"), handle_score),
                MessageHandler(
                    Filters.text
                    & ~Filters.command
                    & ~Filters.regex("^(Новый вопрос|Сдаться|Мой счёт)$"),
                    handle_solution_attempt,
                ),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )


def main() -> None:
    """Запускает бота."""
    tg_token = TG_BOT_TOKEN
    redis_connect = redis.from_url(REDIS_URL, decode_responses=True)

    updater = Updater(tg_token)

    dispatcher = updater.dispatcher
    dispatcher.bot_data["redis"] = redis_connect
    dispatcher.add_handler(build_conv_handler())

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
