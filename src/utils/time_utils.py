import random
import time


def short_sleep() -> None:
    time.sleep(random.uniform(1.2, 3))


def medium_sleep() -> None:
    time.sleep(random.uniform(3, 5))