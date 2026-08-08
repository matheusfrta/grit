import random
import threading


def constant(base=1.0):
    return lambda attempt: base


def linear(base=1.0):
    return lambda attempt: base * attempt


def expo(base=1.0, factor=2.0, cap=60.0):
    def wait(attempt):
        return min(cap, base * factor ** (attempt - 1))
    return wait


def fibo(base=1.0, cap=60.0):
    def wait(attempt):
        a, b = 1, 1
        for _ in range(max(0, attempt - 1)):
            a, b = b, a + b
        return min(cap, base * a)
    return wait


def jitter(fn, spread=1.0):
    def wait(attempt):
        return fn(attempt) + random.uniform(0, spread)
    return wait


def decorr(base=1.0, cap=60.0):
    state = {"prev": base}
    lock = threading.Lock()

    def wait(attempt):
        with lock:
            state["prev"] = min(cap, random.uniform(base, state["prev"] * 3))
            return state["prev"]
    return wait