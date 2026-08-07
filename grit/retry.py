import asyncio
import functools
import inspect
import time

from .backoff import expo
from .exceptions import RetryExhausted


class retry:
    def __init__(self, tries=3, on=Exception, wait=None, giveup=None, on_retry=None):
        self.tries = tries
        self.on = on
        self.wait = wait or expo(base=0.5)
        self.giveup = giveup
        self.on_retry = on_retry

    def _dead(self, e, attempt):
        return attempt >= self.tries or (self.giveup and self.giveup(e))

    def __call__(self, fn):
        if inspect.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def awrap(*args, **kwargs):
                attempt = 0
                while True:
                    try:
                        return await fn(*args, **kwargs)
                    except self.on as e:
                        attempt += 1
                        if self._dead(e, attempt):
                            raise RetryExhausted(attempt, e) from e
                        if self.on_retry:
                            self.on_retry(attempt, e)
                        await asyncio.sleep(self.wait(attempt))
            return awrap

        @functools.wraps(fn)
        def wrap(*args, **kwargs):
            attempt = 0
            while True:
                try:
                    return fn(*args, **kwargs)
                except self.on as e:
                    attempt += 1
                    if self._dead(e, attempt):
                        raise RetryExhausted(attempt, e) from e
                    if self.on_retry:
                        self.on_retry(attempt, e)
                    time.sleep(self.wait(attempt))
        return wrap