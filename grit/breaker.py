import functools
import inspect
import threading
import time

from .exceptions import BreakerOpen

CLOSED = "closed"
OPEN = "open"
HALF = "half_open"


class breaker:
    def __init__(self, fails=5, reset_after=30.0, on=Exception, name=None, success_threshold=1):
        self.fails = fails
        self.reset_after = reset_after
        self.on = on
        self.name = name
        self.success_threshold = success_threshold
        self.state = CLOSED
        self.count = 0
        self.half_ok = 0
        self.opened_at = 0.0
        self.lock = threading.Lock()
        self.listeners = []

    def on_change(self, fn):
        self.listeners.append(fn)
        return fn

    def _emit(self):
        for fn in self.listeners:
            fn(self.name, self.state)

    def _before(self):
        with self.lock:
            if self.state != OPEN:
                return
            left = self.reset_after - (time.monotonic() - self.opened_at)
            if left > 0:
                raise BreakerOpen(self.name, left)
            self.state = HALF
            self.half_ok = 0
            self._emit()

    def _success(self):
        with self.lock:
            if self.state == HALF:
                self.half_ok += 1
                if self.half_ok >= self.success_threshold:
                    self.state = CLOSED
                    self.count = 0
                    self._emit()
            else:
                self.count = 0

    def _failure(self):
        with self.lock:
            if self.state == HALF:
                self.state = OPEN
                self.opened_at = time.monotonic()
                self._emit()
                return
            self.count += 1
            if self.count >= self.fails:
                self.state = OPEN
                self.opened_at = time.monotonic()
                self._emit()

    def __call__(self, fn):
        if inspect.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def awrap(*args, **kwargs):
                self._before()
                try:
                    out = await fn(*args, **kwargs)
                except self.on:
                    self._failure()
                    raise
                self._success()
                return out
            return awrap

        @functools.wraps(fn)
        def wrap(*args, **kwargs):
            self._before()
            try:
                out = fn(*args, **kwargs)
            except self.on:
                self._failure()
                raise
            self._success()
            return out
        return wrap

    def __enter__(self):
        self._before()
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc is None:
            self._success()
        elif isinstance(exc, self.on):
            self._failure()
        return False