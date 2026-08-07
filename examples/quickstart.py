import random
import time

from grit import breaker, constant, fallback, policy, retry, timeout

db = breaker(fails=3, reset_after=10, name="postgres")


@db.on_change
def alert(name, state):
    print(f"[{name}] -> {state}")


@policy(
    fallback(value={"users": [], "cached": True}),
    timeout(2),
    retry(tries=3, wait=constant(0.2), on=ConnectionError),
    db,
)
def list_users():
    if random.random() < 0.7:
        raise ConnectionError("db is down")
    return {"users": ["ana", "bob"], "cached": False}


if __name__ == "__main__":
    for _ in range(5):
        print(list_users())
        time.sleep(0.3)