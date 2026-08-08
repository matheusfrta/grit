import asyncio
import functools
import inspect
import threading


class singleflight:
    def __init__(self, key=None):
        self.key = key
        self.lock = threading.Lock()
        self.calls = {}
        self.acalls = {}

    def _get_key(self, args, kwargs):
        if self.key:
            return self.key(*args, **kwargs)
        return str(args) + str(kwargs)

    def __call__(self, fn):
        if inspect.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def awrap(*args, **kwargs):
                k = self._get_key(args, kwargs)
                with self.lock:
                    if k in self.acalls:
                        fut = self.acalls[k]
                        is_new = False
                    else:
                        fut = asyncio.Future()
                        self.acalls[k] = fut
                        is_new = True

                if not is_new:
                    return await fut

                try:
                    res = await fn(*args, **kwargs)
                    fut.set_result(res)
                    return res
                except Exception as e:
                    fut.set_exception(e)
                    raise
                finally:
                    with self.lock:
                        self.acalls.pop(k, None)
            return awrap

        @functools.wraps(fn)
        def wrap(*args, **kwargs):
            k = self._get_key(args, kwargs)
            with self.lock:
                if k in self.calls:
                    state = self.calls[k]
                    is_new = False
                else:
                    state = {"event": threading.Event()}
                    self.calls[k] = state
                    is_new = True

            if not is_new:
                state["event"].wait()
                if "err" in state:
                    raise state["err"]
                return state["res"]

            try:
                res = fn(*args, **kwargs)
                state["res"] = res
                return res
            except Exception as e:
                state["err"] = e
                raise
            finally:
                state["event"].set()
                with self.lock:
                    self.calls.pop(k, None)
        return wrap