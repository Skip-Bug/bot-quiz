import random
import sys
from functools import wraps

from environs import Env
from telegram import ChatAction, ReplyKeyboardMarkup, Update
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
)

from utils import build_collection

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


def start(update: Update, context: CallbackContext):
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


@send_typing_action
def button_handler(update: Update, context: CallbackContext):
    """Реагирует на нажатия кнопок."""
    text = update.message.text

    if text == "Новый вопрос":
        new_question(update, context)
    elif text == "Сдаться":
        update.message.reply_text("ТУ ДУ — сдаться")
    elif text == "Мой счёт":
        update.message.reply_text("ТУ ДУ — мой счёт")


def new_question(update: Update, context: CallbackContext) -> None:
    """Отправляет случайный вопрос из коллекции."""
    quiz_collection = context.bot_data["quiz"]
    question, answer = random.choice(list(quiz_collection.items()))

    update.message.reply_text(question)


def echo(update: Update, context: CallbackContext):
    """Отвечает как эхо."""
    update.effective_message.reply_text(update.effective_message.text)


def main() -> None:
    """Запускает бота."""
    env = Env()
    env.read_env()
    token = env.str("TG_BOT_TOKEN")

    updater = Updater(token)
    dispatcher = updater.dispatcher

    quiz_collection = build_collection("quiz-questions")
    updater.dispatcher.bot_data["quiz"] = quiz_collection

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(
        MessageHandler(
            Filters.regex("^(Новый вопрос|Сдаться|Мой счёт)$"),
            button_handler,
        )
    )
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
