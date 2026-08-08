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

    def _take(self, timeout=None):
        with self.lock:
            self._refill()
            if self.tokens >= 1:
                self.tokens -= 1
                return 0.0

            delay = (1 - self.tokens) * self.per / self.rate
            if timeout is not None and delay > timeout:
                return -1.0

            self.tokens -= 1
            return delay

    def acquire(self, blocking=True, timeout=None):
        if not blocking:
            delay = self._take(0.0)
        else:
            delay = self._take(timeout)
            
        if delay < 0:
            if not blocking:
                return False
            raise LimitExceeded(timeout)
            
        if delay > 0:
            try:
                time.sleep(delay)
            except BaseException:
                with self.lock:
                    self.tokens = min(self.burst, self.tokens + 1)
                raise
        return True

    async def acquire_async(self, timeout=None):
        delay = self._take(timeout)
        if delay < 0:
            raise LimitExceeded(timeout)
            
        if delay > 0:
            try:
                await asyncio.sleep(delay)
            except BaseException:
                with self.lock:
                    self.tokens = min(self.burst, self.tokens + 1)
                raise
        return True

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