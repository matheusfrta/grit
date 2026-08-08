import asyncio
import time
import pytest
from grit import hedge


def test_sync_hedge_fast():
    calls = {"n": 0}
    
    @hedge(delay=0.1)
    def fast():
        calls["n"] += 1
        return "ok"
        
    assert fast() == "ok"
    time.sleep(0.2)
    assert calls["n"] == 1


def test_sync_hedge_slow():
    calls = {"n": 0}
    
    @hedge(delay=0.05)
    def slow():
        calls["n"] += 1
        if calls["n"] == 1:
            time.sleep(0.2)
        return calls["n"]
        
    assert slow() == 2


def test_async_hedge_fast():
    calls = {"n": 0}
    
    @hedge(delay=0.1)
    async def fast():
        calls["n"] += 1
        return "ok"
        
    assert asyncio.run(fast()) == "ok"


def test_async_hedge_slow():
    calls = {"n": 0}
    
    @hedge(delay=0.05)
    async def slow():
        calls["n"] += 1
        if calls["n"] == 1:
            await asyncio.sleep(0.2)
        return calls["n"]
        
    assert asyncio.run(slow()) == 2