import sys

from environs import Env
from telegram import Update
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
)

sys.stdout.reconfigure(encoding="utf-8")


def start(update: Update, context: CallbackContext):
    user = update.effective_user
    update.message.reply_text(
        text=f"Привет, {user.first_name} ! Я бот, пожалуйста, поговорите со мной!",
    )


def echo(update: Update, context: CallbackContext) -> None:
    """Отвечает как эхо."""
    update.message.reply_text(update.message.text)


def main() -> None:
    """Запускает бота."""
    env = Env()
    env.read_env()
    token = env.str("TG_BOT_TOKEN")

    updater = Updater(token)
    dispatcher = updater.dispatcher

    start_handler = CommandHandler("start", start)

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
