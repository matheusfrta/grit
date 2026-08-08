import asyncio
import functools
import inspect
import queue
import threading


class hedge:
    def __init__(self, delay):
        self.delay = delay

    def __call__(self, fn):
        if inspect.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def awrap(*args, **kwargs):
                t1 = asyncio.create_task(fn(*args, **kwargs))
                
                done, _ = await asyncio.wait([t1], timeout=self.delay)
                if done:
                    return t1.result()
                    
                t2 = asyncio.create_task(fn(*args, **kwargs))
                tasks = [t1, t2]
                
                while tasks:
                    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                    fut = done.pop()
                    tasks.remove(fut)
                    
                    if fut.exception():
                        if not tasks:
                            raise fut.exception()
                    else:
                        for p in tasks:
                            p.cancel()
                        return fut.result()
            return awrap

        @functools.wraps(fn)
        def wrap(*args, **kwargs):
            q = queue.Queue()
            
            def worker():
                try:
                    q.put(("ok", fn(*args, **kwargs)))
                except Exception as e:
                    q.put(("err", e))
            
            active = 1
            threading.Thread(target=worker, daemon=True).start()
            
            err = None
            try:
                kind, val = q.get(timeout=self.delay)
                if kind == "ok":
                    return val
                active -= 1
                err = val
            except queue.Empty:
                pass
                
            active += 1
            threading.Thread(target=worker, daemon=True).start()
            
            while active > 0:
                kind, val = q.get()
                active -= 1
                if kind == "ok":
                    return val
                err = val
                
            raise err
        return wrap