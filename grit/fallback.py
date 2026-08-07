import functools
import inspect


class fallback:
    def __init__(self, value=None, fn=None, on=Exception):
        self.value = value
        self.fn = fn
        self.on = on

    def _rescue(self, e):
        if self.fn:
            return self.fn(e)
        return self.value

    def __call__(self, fn):
        if inspect.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def awrap(*args, **kwargs):
                try:
                    return await fn(*args, **kwargs)
                except self.on as e:
                    out = self._rescue(e)
                    if inspect.isawaitable(out):
                        out = await out
                    return out
            return awrap

        @functools.wraps(fn)
        def wrap(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except self.on as e:
                return self._rescue(e)
        return wrap