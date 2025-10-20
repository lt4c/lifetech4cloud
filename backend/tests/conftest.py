import asyncio
import inspect
from typing import Any

import pytest


def pytest_pyfunc_call(pyfuncitem: pytest.Function) -> bool | None:
    """Run async test functions via asyncio when pytest-asyncio is unavailable."""
    test_obj = pyfuncitem.obj
    if inspect.iscoroutinefunction(test_obj):
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            funcargs = {
                name: pyfuncitem.funcargs[name]
                for name in pyfuncitem._fixtureinfo.argnames or []
            }
            loop.run_until_complete(test_obj(**funcargs))
        finally:
            try:
                loop.run_until_complete(loop.shutdown_asyncgens())
            except Exception:  # pragma: no cover - best effort
                pass
            asyncio.set_event_loop(None)
            loop.close()
        return True
    return None
