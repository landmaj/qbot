from pathlib import Path
from typing import Set

from sqlalchemy import Table

from qbot.core import registry


def import_all_modules(directory: Path):
    return [
        f.stem
        for f in directory.glob("**/*.py")
        if f.is_file() and not f.stem.startswith("_")
    ]


async def get_recently_seen(table: Table) -> Set[int]:
    if not hasattr(table, "cache"):
        table.cache = set()
    return table.cache


async def add_recently_seen(table: Table, value: int) -> None:
    count = await registry.database.execute(f"SELECT count(*) FROM {table.fullname}")
    max_cache_size = count - 1
    if max_cache_size == 0:
        return
    if not hasattr(table, "cache"):
        table.cache = set()
    if len(table.cache) >= max_cache_size:
        table.cache = {value}
    else:
        table.cache.add(value)
