import asyncio
import logging
from functools import wraps
from time import time
from typing import Optional

from qbot.core import registry

_JOBS = {}
logger = logging.getLogger(__name__)


def job(timer: Optional[float] = None):
    """
    Bieda-cron.
    """

    def decorator(function):
        @wraps(function)
        async def wrapper():
            try:
                result = await function()
            except Exception:
                logger.exception(
                    f"Job '{function.__module__}.{function.__name__}' failed!"
                )
            else:
                return result

        wrapper.timer = timer
        _JOBS[wrapper] = time()

        return wrapper

    return decorator


async def _run_jobs():
    await registry.setup()
    while True:
        tasks = []
        for func, next_run_on in _JOBS.items():
            current_time = time()
            if next_run_on and current_time >= next_run_on:
                tasks.append(func())
                if func.timer is not None:
                    _JOBS[func] = current_time + func.timer
                else:
                    _JOBS[func] = None
        await asyncio.gather(*tasks)
        await asyncio.sleep(0.1)


def run():
    asyncio.run(_run_jobs())
