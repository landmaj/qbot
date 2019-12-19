from pathlib import Path
from typing import Set

from sqlalchemy import Table, func, select

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
    if not hasattr(table, "max_cache_size"):
        await set_max_cache_size(table)
    if len(await get_recently_seen(table)) >= table.max_cache_size != 0:
        await set_max_cache_size(table)
        table.cache = {value}
    elif table.max_cache_size != 0:
        table.cache.add(value)


async def set_max_cache_size(table: Table):
    cnt = await count(table)
    if cnt == 0:
        table.max_cache_size = 0
    else:
        table.max_cache_size = cnt - 1


async def count(table: Table) -> int:
    return await registry.database.fetch_val(select([func.count()]).select_from(table))


def sanitize_field(v: str) -> str:
    """Replace double quotes to fix Loki field parsing."""
    v = v.replace("'", "\\'")
    v = v.replace('"', "'")
    return v
