import asyncio
import logging
from functools import wraps
from time import time

from qbot.core import registry

_JOBS = {}
logger = logging.getLogger(__name__)


def job(timer: float):
    """
    Bieda-cron.
    """

    def decorator(function):
        @wraps(function)
        async def wrapper():
            try:
                return await function()
            except Exception:
                logger.exception(
                    f"Job '{function.__module__}.{function.__name__}' failed!"
                )

        wrapper.timer = timer
        _JOBS[wrapper] = time()

        return wrapper

    return decorator


async def _run_jobs():
    await registry.setup()
    logger.info("Started scheduler process.")
    while True:
        tasks = []
        for func, next_run_on in _JOBS.items():
            current_time = time()
            if current_time >= next_run_on:
                tasks.append(func())
                _JOBS[func] = current_time + func.timer
        await asyncio.gather(*tasks)
        await asyncio.sleep(0.1)


def run():
    asyncio.run(_run_jobs())
