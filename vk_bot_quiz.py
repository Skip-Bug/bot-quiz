import random
import time

import requests
import vk_api as vk
from environs import Env
from vk_api.longpoll import VkEventType, VkLongPoll

# TO DO добавить логер


def echo(event, vk_api, text=None):
    vk_api.messages.send(
        user_id=event.user_id,
        message=event.text or text,
        random_id=random.randint(1, 1000),
    )


def run_longpoll(longpoll, vk_api):
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            text = event.text or "Я понимаю только текст 🙂"
            echo(event, vk_api, text)


def main():
    env = Env()
    env.read_env()
    token = env.str("VK_TOKEN")

    vk_session = vk.VkApi(token=token)
    api = vk_session.get_api()

    print("ВК бот запущен")
    while True:
        try:
            longpoll = VkLongPoll(vk_session)
            run_longpoll(longpoll, api)
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
