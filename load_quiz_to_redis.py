"""Скрипт заливки вопросов в Redis"""
import json
import time

import redis

from quiz_processing import build_collection
from settings import REDIS_URL

BATCH_SIZE = 1000


def main():
    start = time.monotonic()

    redis_connect = redis.from_url(REDIS_URL, decode_responses=True)

    collection, errors = build_collection("quiz-questions")

    for filename, message in errors.items():
        print(f"Пропущен {filename}: {message}")

    redis_connect.delete("quiz:questions")
    pipeline = redis_connect.pipeline()
    count = 0

    for question, answer in collection.items():
        payload = json.dumps({"q": question, "a": answer}, ensure_ascii=False)
        pipeline.rpush("quiz:questions", payload)
        count += 1
        if count % BATCH_SIZE == 0:
            pipeline.execute()
            pipeline = redis_connect.pipeline()
            print(f"Залито: {count}")

    pipeline.execute()

    total = redis_connect.llen("quiz:questions")
    elapsed = time.monotonic() - start
    print(f"Готово за {elapsed:.1f} сек. В Redis: {total}")


if __name__ == "__main__":
    main()
