from typing import Optional

import validators
from sqlalchemy import Table, func
from sqlalchemy.dialects.postgresql import insert

from qbot.core import registry
from qbot.utils import get_recently_seen


async def query_with_recently_seen(
    table: Table, identifier: Optional[int] = None
) -> Optional[dict]:
    if identifier:
        return await registry.database.fetch_one(
            table.select().where(table.c.id == identifier)
        )
    recently_seen = await get_recently_seen(table)
    query = table.select()
    if len(recently_seen) != 0:
        query = query.where(table.c.id.notin_(recently_seen))
    query = query.order_by(func.random()).limit(1)
    return await registry.database.fetch_one(query)


async def add_urls(table: Table, urls: str) -> str:
    validated, rejected = [], []
    for line in urls.split("\n"):
        # for some reason Slack adds triangular brackets to URLs
        line = line.strip("<> ")
        if validators.url(line):
            validated.append(line)
        else:
            rejected.append(line)
    if len(validated) == 0:
        return "Nie podałeś żadnych poprawnych URL-i."
    query = insert(table).on_conflict_do_nothing(index_elements=["url"])
    values = [{"url": x} for x in validated]
    await registry.database.execute_many(query, values)
    response = f"Dodano {len(validated)} wiersz[y/ów]."
    if len(rejected) != 0:
        text = "\n".join(rejected)
        incorrect_urls = (
            f"*Poniższe wartości są niepoprawne i nie zostały dodane:*\n{text}"
        )
        response = f"{response}\n{incorrect_urls}"
    return response
