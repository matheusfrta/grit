import asyncio

import pytest

from grit import constant, retry
from grit.exceptions import RetryExhausted


def test_succeeds_after_flops():
    calls = {"n": 0}

    @retry(tries=3, wait=constant(0))
    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise ValueError("nope")
        return "ok"

    assert flaky() == "ok"
    assert calls["n"] == 3


def test_gives_up():
    @retry(tries=2, wait=constant(0))
    def bad():
        raise ValueError("always")

    with pytest.raises(RetryExhausted) as info:
        bad()
    assert info.value.attempts == 2
    assert isinstance(info.value.last, ValueError)


def test_giveup_predicate():
    calls = {"n": 0}

    @retry(tries=5, wait=constant(0), giveup=lambda e: isinstance(e, KeyError))
    def bad():
        calls["n"] += 1
        raise KeyError("stop")

    with pytest.raises(RetryExhausted):
        bad()
    assert calls["n"] == 1


def test_only_catches_listed():
    @retry(tries=3, wait=constant(0), on=ValueError)
    def bad():
        raise TypeError("other")

    with pytest.raises(TypeError):
        bad()


def test_on_retry_hook():
    seen = []

    @retry(tries=2, wait=constant(0), on_retry=lambda n, e: seen.append(n))
    def bad():
        raise ValueError()

    with pytest.raises(RetryExhausted):
        bad()
    assert seen == [1]


def test_async():
    calls = {"n": 0}

    @retry(tries=3, wait=constant(0))
    async def flaky():
        calls["n"] += 1
        if calls["n"] < 2:
            raise ValueError()
        return 7

    assert asyncio.run(flaky()) == 7