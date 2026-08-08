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
        
        self.queue = {}
        self.next_id = 0

    def _refill(self):
        now = time.monotonic()
        self.tokens = min(self.burst, self.tokens + (now - self.ts) * self.rate / self.per)
        self.ts = now

    def _get_ticket(self):
        with self.lock:
            tid = self.next_id
            self.next_id += 1
            self.queue[tid] = None
            return tid

    def _check(self, tid):
        with self.lock:
            self._refill()
            first = next(iter(self.queue)) if self.queue else None
            
            if first == tid and self.tokens >= 1:
                del self.queue[tid]
                self.tokens -= 1
                return True, 0.0
            
            ahead = 0
            for k in self.queue:
                if k == tid:
                    break
                ahead += 1
                
            deficit = max(0.0, (ahead + 1) - self.tokens)
            delay = deficit * self.per / self.rate
            if delay <= 0:
                delay = 0.01 
            return False, delay

    def _cancel(self, tid):
        with self.lock:
            self.queue.pop(tid, None)

    def acquire(self, blocking=True, timeout=None):
        tid = self._get_ticket()
        start = time.monotonic()
        
        while True:
            got_it, delay = self._check(tid)
            if got_it:
                return True
                
            if not blocking:
                self._cancel(tid)
                return False
                
            elapsed = time.monotonic() - start
            if timeout is not None and elapsed >= timeout:
                self._cancel(tid)
                raise LimitExceeded(timeout)
                
            sleep_time = min(delay, 0.05)
            if timeout is not None:
                sleep_time = min(sleep_time, max(0.0, timeout - elapsed))
                
            try:
                time.sleep(sleep_time)
            except BaseException:
                self._cancel(tid)
                raise

    async def acquire_async(self, timeout=None):
        tid = self._get_ticket()
        start = time.monotonic()
        
        while True:
            got_it, delay = self._check(tid)
            if got_it:
                return True
                
            elapsed = time.monotonic() - start
            if timeout is not None and elapsed >= timeout:
                self._cancel(tid)
                raise LimitExceeded(timeout)
                
            sleep_time = min(delay, 0.05)
            if timeout is not None:
                sleep_time = min(sleep_time, max(0.0, timeout - elapsed))
                
            try:
                await asyncio.sleep(sleep_time)
            except BaseException:
                self._cancel(tid)
                raise

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