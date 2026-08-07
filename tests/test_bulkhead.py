import asyncio
import threading

import pytest

from grit import bulkhead
from grit.exceptions import BulkheadFull


def test_rejects_when_full():
    bh = bulkhead(1)
    entered = threading.Event()
    release = threading.Event()

    @bh
    def slow():
        entered.set()
        release.wait(2)

    t = threading.Thread(target=slow)
    t.start()
    assert entered.wait(1)

    with pytest.raises(BulkheadFull):
        slow()

    release.set()
    t.join()


def test_releases_slot():
    bh = bulkhead(1)

    @bh
    def quick():
        return 1

    assert quick() == 1
    assert quick() == 1


def test_async():
    bh = bulkhead(2)

    @bh
    async def job():
        await asyncio.sleep(0.01)
        return "done"

    async def main():
        return await asyncio.gather(job(), job(), job())

    assert asyncio.run(main()) == ["done"] * 3