import asyncio
import logging
import time
from functools import wraps

from qbot.core import registry

_JOBS = {}
logger = logging.getLogger(__name__)


def cron_job(function):
    job_name = f"{function.__module__}.{function.__name__}"

    @wraps(function)
    async def wrapper():
        start = time.time()
        try:
            logger.info(f"Running job '{job_name}'.")
            result = await function()
        except Exception:
            execution_time = time.time() - start
            logger.exception(
                f"Job '{job_name}' failed after {execution_time:.2f} seconds!"
            )
        else:
            execution_time = time.time() - start
            logger.info(
                f"Job '{job_name}' completed after {execution_time:.2f} seconds."
            )
            return result

    _JOBS[job_name] = wrapper()

    return wrapper


async def _run_jobs():
    await registry.setup()
    await asyncio.gather(*_JOBS.values())


def run():
    asyncio.run(_run_jobs())
