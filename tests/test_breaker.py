import asyncio
import time

import pytest

from grit import breaker
from grit.exceptions import BreakerOpen


def test_opens_after_failures():
    b = breaker(fails=2, reset_after=60)

    @b
    def bad():
        raise ValueError()

    for _ in range(2):
        with pytest.raises(ValueError):
            bad()
    assert b.state == "open"
    with pytest.raises(BreakerOpen):
        bad()


def test_half_open_recovers():
    b = breaker(fails=1, reset_after=0.05)

    @b
    def bad():
        raise ValueError()

    with pytest.raises(ValueError):
        bad()
    time.sleep(0.06)

    @b
    def good():
        return "fine"

    assert good() == "fine"
    assert b.state == "closed"


def test_context_manager():
    b = breaker(fails=1, reset_after=60)
    with pytest.raises(ValueError):
        with b:
            raise ValueError()
    assert b.state == "open"


def test_listener_fires():
    b = breaker(fails=1, reset_after=60, name="db")
    seen = []

    @b.on_change
    def track(name, state):
        seen.append((name, state))

    @b
    def bad():
        raise ValueError()

    with pytest.raises(ValueError):
        bad()
    assert seen == [("db", "open")]


def test_async():
    b = breaker(fails=1, reset_after=60)

    @b
    async def bad():
        raise ValueError()

    with pytest.raises(ValueError):
        asyncio.run(bad())
    assert b.state == "open"