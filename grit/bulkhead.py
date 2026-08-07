import asyncio
import functools
import inspect
import threading

from .exceptions import BulkheadFull


class bulkhead:
    def __init__(self, size, timeout=None):
        self.size = size
        self.timeout = timeout
        self.sem = threading.Semaphore(size)
        self._asem = None

    async def _take_async(self):
        if self._asem is None:
            self._asem = asyncio.Semaphore(self.size)
        sem = self._asem
        if self.timeout is None:
            if sem._value <= 0:
                return False
            await sem.acquire()
            return True
        try:
            await asyncio.wait_for(sem.acquire(), self.timeout)
            return True
        except asyncio.TimeoutError:
            return False

    def __call__(self, fn):
        if inspect.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def awrap(*args, **kwargs):
                if not await self._take_async():
                    raise BulkheadFull(self.size)
                try:
                    return await fn(*args, **kwargs)
                finally:
                    self._asem.release()
            return awrap

        @functools.wraps(fn)
        def wrap(*args, **kwargs):
            if self.timeout is None:
                ok = self.sem.acquire(blocking=False)
            else:
                ok = self.sem.acquire(timeout=self.timeout)
            if not ok:
                raise BulkheadFull(self.size)
            try:
                return fn(*args, **kwargs)
            finally:
                self.sem.release()
        return wrap