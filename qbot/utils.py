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
    cache = getattr(table, "cache", set())
    if len(cache) >= getattr(table, "cache_max_size", 0):
        query = f"SELECT count(*) FROM {table.fullname}"
        table.cache_max_size = await registry.database.execute(query) // 2
        table.cache = set()
    return cache


async def add_recently_seen(table: Table, value: int) -> None:
    if hasattr(table, "cache"):
        table.cache.add(value)
    else:
        table.cache = {value}
