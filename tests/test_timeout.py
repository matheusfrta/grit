import asyncio
import time

import pytest

from grit import timeout
from grit.exceptions import TimeoutExceeded


def test_sync_ok():
    @timeout(1)
    def fast():
        return 3

    assert fast() == 3


def test_sync_timeout():
    @timeout(0.1)
    def slow():
        time.sleep(2)

    with pytest.raises(TimeoutExceeded):
        slow()


def test_async_ok():
    @timeout(1)
    async def fast():
        return 3

    assert asyncio.run(fast()) == 3


def test_async_timeout():
    @timeout(0.1)
    async def slow():
        await asyncio.sleep(2)

    with pytest.raises(TimeoutExceeded):
        asyncio.run(slow())