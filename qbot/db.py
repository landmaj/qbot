import logging
from collections import defaultdict
from html import unescape
from typing import List, Optional

import sqlalchemy
import validators
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Table,
    Text,
    func,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB, insert
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.sql import text

from qbot.core import registry

naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
metadata = sqlalchemy.MetaData(naming_convention=naming_convention)

fortunki = sqlalchemy.Table(
    "fortunki",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("text", Text, nullable=False, unique=True),
    Column("image", ForeignKey("b2_images.id"), nullable=True),
)

b2_images = sqlalchemy.Table(
    "b2_images",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("plugin", Text, nullable=False, index=True),
    Column("extra", Text, nullable=True, index=True),
    Column("deleted", Boolean, server_default="false", nullable=False, index=True),
    Column("file_name", Text, unique=True, nullable=False),
    Column("hash", Text, nullable=False, index=True),
    Column("url", Text, nullable=False),
)

b2_images_interim = sqlalchemy.Table(
    "b2_images_interim",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("plugin", Text, nullable=False, index=True),
    Column("url", Text, unique=True, nullable=False),
)

plugin_storage = sqlalchemy.Table(
    "plugin_storage",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("plugin", Text, nullable=False),
    Column("key", Text, nullable=False),
    Column("data", MutableDict.as_mutable(JSONB)),
)
Index("ix_plugin_key", plugin_storage.c.plugin, plugin_storage.c.key, unique=True)

credentials = sqlalchemy.Table(
    "credentials",
    metadata,
    Column("login", Text, primary_key=True),
    Column("password", Text, nullable=False),
)

game = sqlalchemy.Table(
    "game",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("timestamp", DateTime, nullable=False),
    Column("active", Boolean, nullable=False),
    Column("data", MutableDict.as_mutable(JSONB)),
    Column("reminders_sent", Boolean, default=False),
)


async def b2_images_interim_insert(plugin: str, urls: str) -> str:
    validated, rejected = [], []
    for line in urls.split("\n"):
        # for some reason Slack adds triangular brackets to URLs
        line = line.strip("<> ").split("|")[0]
        if validators.url(line):
            validated.append(line)
        else:
            rejected.append(line)
    if len(validated) == 0:
        return "Nie podałeś żadnych poprawnych URL-i."
    query = insert(b2_images_interim).on_conflict_do_nothing(index_elements=["url"])
    values = [{"url": unescape(x), "plugin": plugin} for x in validated]
    await registry.database.execute_many(query, values)
    response = f"Dodano {len(validated)} wiersz[y/ów]."
    if len(rejected) != 0:
        text = "\n".join(rejected)
        incorrect_urls = (
            f"*Poniższe wartości są niepoprawne i nie zostały dodane:*\n{text}"
        )
        response = f"{response}\n{incorrect_urls}"
    return response


async def b2_images_interim_insert_from_slack(plugin: str, files: List[dict]) -> str:
    errors: List[str] = []
    urls: List[str] = []
    for f in files:
        mimetype: str = f["mimetype"]
        url: str = f["url_private"]
        if mimetype.split("/")[0] != "image":
            logging.error(f"Incorrect MIME type ({mimetype}) for file: {url}.")
            errors.append(url)
            continue
        urls.append(url)
    query = insert(b2_images_interim).on_conflict_do_nothing(index_elements=["url"])
    values = [{"url": x, "plugin": plugin} for x in urls]
    await registry.database.execute_many(query, values)
    response = f"Dodano {len(urls)} wiersz[y/ów]."
    if len(errors) != 0:
        text = "\n".join(errors)
        incorrect_urls = (
            f"*Poniższe pliki są niepoprawne i nie zostały dodane:*\n{text}"
        )
        response = f"{response}\n{incorrect_urls}"
    return response


_cache = defaultdict(set)


async def query_with_recently_seen(
    table: Table, identifier: Optional[int] = None, where: Optional[str] = None
) -> Optional[dict]:
    key = table.name if not where else f"{table.name}_{hash(where)}"
    query = table.select()
    if where:
        query = query.where(text(where))
    if identifier:
        query = query.where(table.c.id == identifier)
    else:
        if len(_cache[key]) > 0:
            query = query.where(table.c.id.notin_(_cache[key]))
        query = query.order_by(func.random()).limit(1)
    result = await registry.database.fetch_one(query)
    if result is None:
        return
    else:
        if where:
            table_size = await count(table, where)
        else:
            table_size = await count(table)
        if table_size > 1:
            if len(_cache[key]) >= table_size - 1:
                _cache[key] = {result["id"]}
            else:
                _cache[key].add(result["id"])
        print(_cache[key])
        return result


async def count(table: Table, where: Optional[str] = None) -> int:
    query = select([func.count()]).select_from(table)
    if where:
        query = query.where(text(where))
    return await registry.database.fetch_val(query)


async def b2_images_count(plugin: str) -> int:
    return await registry.database.fetch_val(
        select([func.count()])
        .select_from(b2_images)
        .where((b2_images.c.plugin == plugin) & (b2_images.c.deleted == False))
    )
