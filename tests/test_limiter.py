import asyncio
import time

import pytest

from grit import limiter
from grit.exceptions import LimitExceeded


def test_burst_then_throttle():
    lim = limiter(rate=2, per=1.0)
    start = time.monotonic()
    for _ in range(3):
        lim.acquire()
    assert time.monotonic() - start >= 0.4


def test_non_blocking():
    lim = limiter(rate=1, per=10.0)
    assert lim.acquire(blocking=False)
    assert not lim.acquire(blocking=False)


def test_acquire_timeout():
    lim = limiter(rate=1, per=10.0)
    lim.acquire()
    with pytest.raises(LimitExceeded):
        lim.acquire(timeout=0.05)


def test_decorator():
    lim = limiter(rate=100, per=1.0)

    @lim
    def ping():
        return "pong"

    assert ping() == "pong"


def test_async():
    lim = limiter(rate=100, per=1.0)

    @lim
    async def ping():
        return "pong"

    assert asyncio.run(ping()) == "pong"