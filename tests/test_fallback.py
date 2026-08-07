import asyncio

from grit import fallback


def test_returns_value():
    @fallback(value="default")
    def bad():
        raise ValueError()

    assert bad() == "default"


def test_fn_receives_error():
    @fallback(fn=lambda e: f"caught {type(e).__name__}")
    def bad():
        raise KeyError()

    assert bad() == "caught KeyError"


def test_passthrough_on_success():
    @fallback(value="default")
    def good():
        return "real"

    assert good() == "real"


def test_async():
    @fallback(value=-1)
    async def bad():
        raise ValueError()

    assert asyncio.run(bad()) == -1


def test_async_fn_handler():
    async def rescue(e):
        return "saved"

    @fallback(fn=rescue)
    async def bad():
        raise ValueError()

    assert asyncio.run(bad()) == "saved"