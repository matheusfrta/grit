import asyncio
import threading
import time

from grit import singleflight


def test_sync_coalesces():
    calls = {"n": 0}
    
    @singleflight()
    def fetch(item):
        calls["n"] += 1
        time.sleep(0.1)
        return f"data:{item}"
        
    def worker(item, out, i):
        out[i] = fetch(item)
        
    out = {}
    threads = [threading.Thread(target=worker, args=(1, out, i)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
        
    assert calls["n"] == 1
    assert list(out.values()) == ["data:1"] * 5


def test_async_coalesces():
    calls = {"n": 0}
    
    @singleflight(key=lambda item: item)
    async def fetch(item):
        calls["n"] += 1
        await asyncio.sleep(0.1)
        return f"data:{item}"
        
    async def main():
        return await asyncio.gather(*[fetch(2) for _ in range(5)])
        
    res = asyncio.run(main())
    assert calls["n"] == 1
    assert res == ["data:2"] * 5