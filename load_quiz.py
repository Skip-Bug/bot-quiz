"""Скрипт заливки вопросов в Redis"""

import json

import redis

from questions import build_collection
from settings import REDIS_URL


def main():
    redis_connect = redis.from_url(REDIS_URL, decode_responses=True)

    redis_connect.delete("quiz:questions")
    for question, answer in build_collection("quiz-questions").items():
        payload = json.dumps({"q": question, "a": answer}, ensure_ascii=False)
        redis_connect.rpush("quiz:questions", payload)

    total = redis_connect.llen("quiz:questions")
    print(f"Залито вопросов: {total}")


if __name__ == "__main__":
    main()
