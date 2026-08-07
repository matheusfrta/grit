import asyncio
import functools
import inspect
import threading
import time

from .exceptions import LimitExceeded


class limiter:
    def __init__(self, rate, per=1.0, burst=None):
        self.rate = rate
        self.per = per
        self.burst = burst or rate
        self.tokens = float(self.burst)
        self.ts = time.monotonic()
        self.lock = threading.Lock()

    def _refill(self):
        now = time.monotonic()
        self.tokens = min(self.burst, self.tokens + (now - self.ts) * self.rate / self.per)
        self.ts = now

    def _take(self):
        with self.lock:
            self._refill()
            if self.tokens >= 1:
                self.tokens -= 1
                return 0.0
            return (1 - self.tokens) * self.per / self.rate

    def acquire(self, blocking=True, timeout=None):
        waited = 0.0
        while True:
            delay = self._take()
            if delay <= 0:
                return True
            if not blocking:
                return False
            if timeout is not None and waited + delay > timeout:
                raise LimitExceeded(timeout)
            time.sleep(delay)
            waited += delay

    async def acquire_async(self, timeout=None):
        waited = 0.0
        while True:
            delay = self._take()
            if delay <= 0:
                return True
            if timeout is not None and waited + delay > timeout:
                raise LimitExceeded(timeout)
            await asyncio.sleep(delay)
            waited += delay

    def __call__(self, fn):
        if inspect.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def awrap(*args, **kwargs):
                await self.acquire_async()
                return await fn(*args, **kwargs)
            return awrap

        @functools.wraps(fn)
        def wrap(*args, **kwargs):
            self.acquire()
            return fn(*args, **kwargs)
        return wrap