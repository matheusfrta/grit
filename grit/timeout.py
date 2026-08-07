import asyncio
import functools
import inspect
import signal
import threading

from .exceptions import TimeoutExceeded


class timeout:
    def __init__(self, seconds):
        self.seconds = seconds

    def __call__(self, fn):
        if inspect.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def awrap(*args, **kwargs):
                try:
                    return await asyncio.wait_for(fn(*args, **kwargs), self.seconds)
                except asyncio.TimeoutError as e:
                    raise TimeoutExceeded(self.seconds) from e
            return awrap

        @functools.wraps(fn)
        def wrap(*args, **kwargs):
            if threading.current_thread() is threading.main_thread() and hasattr(signal, "SIGALRM"):
                return self._signal(fn, args, kwargs)
            return self._thread(fn, args, kwargs)
        return wrap

    def _signal(self, fn, args, kwargs):
        def handler(signum, frame):
            raise TimeoutExceeded(self.seconds)

        old = signal.signal(signal.SIGALRM, handler)
        signal.setitimer(signal.ITIMER_REAL, self.seconds)
        try:
            return fn(*args, **kwargs)
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, old)

    def _thread(self, fn, args, kwargs):
        box = {}

        def run():
            try:
                box["out"] = fn(*args, **kwargs)
            except Exception as e:
                box["err"] = e

        t = threading.Thread(target=run, daemon=True)
        t.start()
        t.join(self.seconds)
        if t.is_alive():
            raise TimeoutExceeded(self.seconds)
        if "err" in box:
            raise box["err"]
        return box.get("out")