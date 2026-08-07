import pytest

from grit import breaker, constant, policy, retry, timeout
from grit.exceptions import RetryExhausted


def test_layers_compose():
    calls = {"n": 0}

    @policy(timeout(1), retry(tries=3, wait=constant(0)))
    def flaky():
        calls["n"] += 1
        if calls["n"] < 2:
            raise ValueError()
        return "ok"

    assert flaky() == "ok"
    assert calls["n"] == 2


def test_order_matters():
    b = breaker(fails=2, reset_after=60)

    @policy(retry(tries=2, wait=constant(0)), b)
    def bad():
        raise ValueError()

    with pytest.raises(RetryExhausted):
        bad()
    assert b.count == 2
    assert b.state == "open"


def test_empty_policy_rejected():
    with pytest.raises(ValueError):
        policy()