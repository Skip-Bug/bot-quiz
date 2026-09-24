# 🎯 bot-quiz

## 📖 Описание

Бот-викторина «Своя игра» для **Telegram** и **ВКонтакте**.
Задаёт вопросы из базы, проверяет ответы с опечатками через нечёткое сравнение,
хранит вопросы и текущее состояние игроков в Redis.

<table>
    <tr>
        <td align="center"><b>Telegram</b></td>
        <td align="center"><b>VKontakte</b></td>
    </tr>
    <tr>
        <td><img style="max-width:50%; height:auto;" alt="Telegram" src="https://github.com/user-attachments/assets/8c84ff7f-eeb3-4719-875a-b02ea4de2276" /></td>
        <td><img style="max-width:50%; height:auto;" alt="VKontakte" src="https://github.com/user-attachments/assets/406ac0ac-5499-4902-b732-9e4fb17bbf3a" /></td>
    </tr>
</table>

[![GitHub Репозиторий](https://img.shields.io/badge/Репозиторий-GitHub-blue?logo=github)](https://github.com/Skip-Bug/bot-quiz)
[![Лицензия MIT](https://img.shields.io/badge/Лицензия-MIT-blue.svg)](LICENSE)
[![VK](https://img.shields.io/badge/VK-группа_Python-blue?logo=vk)](https://vk.ru/club237763822)
[![Telegram](https://img.shields.io/badge/Telegram-@bot-blue?logo=telegram)](https://t.me/load_image_bot)

## 🧰 Требования

- 🐍 **Python 3.8 – 3.10** (более новые версии не тестировались).
  Версию можно узнать командой:

  ```bash
  python --version
  ```

- 🟥 **Redis** ([локально](https://redis-docs.ru/operate/oss_and_stack/install/install-redis/) или [удалённо](https://redislabs.com/)).

  Проверить, что запущен:

  ```bash
  redis-cli ping
  # → PONG
  ```

## ⚙️ Переменные окружения

- 🔑 **Telegram Bot Token**: инструкция по регистрации бота доступна [здесь](https://way23.ru/%D1%80%D0%B5%D0%B3%D0%B8%D1%81%D1%82%D1%80%D0%B0%D1%86%D0%B8%D1%8F-%D0%B1%D0%BE%D1%82%D0%B0-%D0%B2-telegram.html). Пример токена: `958423683:AAEAtJ5Lde5YYfkjergber`.

- 🔑 **VK Bot Token** — инструкция ниже.

### 🪙 Получение токена ВКонтакте

Создайте [группу](https://vk.com/groups?w=groups_create_new) в ВКонтакте.

**Включить сообщения:** Управление сообществом → Сообщения → Сообщения сообщества: **Включены**.
<img style="max-width:100%; height:auto;" alt="Сообщения" src="https://github.com/user-attachments/assets/ce6808e8-a58c-44b7-aa2b-5190bb6fea08" />

**Включить Long Poll:** Управление сообществом → Дополнительно → Работа с API → Long Poll API.
Переключатель в положение «Включено», версию API выберите свежую.
<img style="max-width:100%; height:auto;" alt="Long Poll" src="https://github.com/user-attachments/assets/e0903a0a-c400-46d8-b3df-4f3f9418a6c2" />

**Выбрать типы событий:** Там же, на вкладке «Типы событий», поставьте галочку напротив **«Входящие сообщения»** (`message_new`).

**Включить возможности ботов:** Управление сообществом → Сообщения → Настройки для бота → **«Возможности ботов»: Включены**.
Без этого клавиатура и часть методов будут падать с ошибкой `[912]`.
<img style="max-width:100%; height:auto;" alt="Возможности ботов" src="https://github.com/user-attachments/assets/82d290b2-501f-43b8-9cb0-9b36fe59099d" />

**Создать токен:** На вкладке «Ключи доступа» нажмите **«Создать ключ»** и дайте ему права на сообщения. Этот токен вставьте в переменную `VK_BOT_TOKEN`.
<img style="max-width:100%; height:auto;" alt="Ключи доступа" src="https://github.com/user-attachments/assets/763df98c-45aa-4574-8a4c-c6529af8956a" />

## 🧱 Установка

**📦 Установите зависимости:**

```bash
pip install -r requirements.txt
```

**⚙️ Настройте переменные окружения.**
Создайте файл `.env` в корне проекта:

```env
TG_BOT_TOKEN=ваш_токен_телеграм_бота
VK_BOT_TOKEN=ваш_токен_вконтакте
REDIS_URL=redis://localhost:6379/0
```

## 📚 База вопросов

В папке `quiz-questions/` лежат `.txt`-файлы в кодировке **KOI8-R**.
Формат блока:

```text
Вопрос 1:
Текст вопроса?
Ответ:
Текст ответа.
Комментарий:
Необязательный комментарий для ведущего.
```

Блоки разделяются **пустой строкой**. Парсер:

- склеивает переносы внутри блока,
- вырезает пометки `[чтецу ...]`, `[ведущему ...]`,
- обрезает ответ до первого предложения,
- убирает дубли по «отпечатку» (регистр, пунктуация, `ё/е`).

Если у вас UTF-8 вместо KOI8-R — перекодируйте файлы или поменяйте `encoding` в `questions.load_quiz`.

### 📥 Заливка базы в Redis

После первого запуска (и при изменении `.txt`) базу надо залить в Redis:

```bash
python load_quiz_to_redis.py
# → Залито вопросов: 300000
```

Проверка:

```bash
redis-cli LLEN quiz:questions
# → 300000
```

Без этого шага боты ответят «База пуста».

## 🚀 Запуск

**Telegram-бот:**

```bash
python tg_bot_quiz.py
```

**VK-бот:**

```bash
python vk_bot_quiz.py
```

Оба бота можно запускать одновременно — они независимы и используют разные префиксы ключей в Redis (`tg:` и `vk:`).

## 🎮 Как играть

- **/start** — приветствие и клавиатура.
- **Новый вопрос** — бот задаёт вопрос.
- **Ответ текстом** — бот сравнит с правильным:
  - «Правильно!» — если совпало (или почти).
  - «Близко! Попробуй ещё раз.» — если похоже, но не точно.
  - «Неверно. Правильный ответ: …» — если мимо.
- **Сдаться** — бот покажет правильный ответ.
- **Мой счёт** — пока заглушка.

## ⚙️ Как это работает

- Вопросы хранятся в Redis, ключ `quiz:questions`. Бот достаёт случайный вопрос из Redis, не загружая базу в память.
- Каждый игрок имеет свой текущий вопрос, он хранится в Redis:

  ```
  tg:user:<id>:current_question / current_answer (для Telegram)
  vk:user:<id>:current_question / current_answer (для VK)
  ```

- Проверка ответа — `rapidfuzz.token_sort_ratio`:
  - `≥ 80` → `correct` (верно)
  - `≥ 50` → `close` (близко)
  - иначе → `wrong` (неверно)

## ⚖️ Лицензия

MIT License

## 🎡 Цель проекта

Код написан в образовательных целях на онлайн-курсе для разработчиков [dvmn.org](https://dvmn.org).
