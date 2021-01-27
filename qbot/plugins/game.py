from asyncio import sleep
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import partial
from typing import Any, List, Optional

import pytz
from sqlalchemy import func, select

from qbot.command import add_command as _add_command
from qbot.core import registry
from qbot.cron import cron_job
from qbot.db import game as GameTable
from qbot.message import (
    IncomingMessage,
    OutgoingMessage,
    Text,
    send_message,
    send_reply,
)

add_command = partial(
    _add_command,
    channel="gejming",
    safe_to_fix=False,
)

DT_FORMAT = "%d/%m/%Y %H:%M"
WARSAW_TZ = pytz.timezone("Europe/Warsaw")


@dataclass()
class Game:
    id: Optional[int]
    timestamp: datetime
    name: str
    players: List[str]
    reminders_sent: Optional[bool]


async def _active_game_exists() -> bool:
    query = (
        select([func.count()]).select_from(GameTable).where(GameTable.c.active == True)
    )
    return await registry.database.fetch_val(query) >= 1


async def _get_game_details() -> Game:
    result = await registry.database.fetch_one(
        GameTable.select().where(GameTable.c.active == True)
    )
    return Game(
        id=result["id"],
        timestamp=result["timestamp"],
        name=result["data"]["name"],
        players=result["data"]["players"],
        reminders_sent=result["reminders_sent"],
    )


async def _add_game(game: Game):
    return await registry.database.execute(
        query=GameTable.insert(),
        values={
            "timestamp": game.timestamp,
            "active": True,
            "data": {
                "name": game.name,
                "players": [],
            },
        },
    )


async def _cancel_game(game: Game):
    return await registry.database.execute(
        GameTable.update().where(GameTable.c.id == game.id).values(active=False)
    )


async def _update_players(game: Game):
    return await registry.database.execute(
        query=GameTable.update()
        .where(GameTable.c.id == game.id)
        .values(data={"name": game.name, "players": game.players})
    )


@add_command("game", "show currently scheduled game")
async def game_details(message: IncomingMessage) -> Any:
    if not await _active_game_exists():
        return await send_reply(message, text="There is no scheduled game.")
    game = await _get_game_details()
    players = " ".join([f"<@{player}>" for player in game.players])
    local_dt = game.timestamp.astimezone(WARSAW_TZ)
    text = (
        f"{game.name} at {local_dt.strftime(DT_FORMAT)}\n"
        f"Players: {players or 'none'}"
    )
    return await send_reply(message, text)


@add_command("game create", "create a new game", aliases=["game add"])
async def game_create(message: IncomingMessage) -> Any:
    async def _send_error():
        await send_reply(
            message, text="Expected format: !game create -- 27/01/2021 21:37 Among Us"
        )

    if not message.text:
        return await _send_error()
    if await _active_game_exists():
        return await send_reply(
            message, text="There is already a game scheduled, cancel it first."
        )

    message_parts = message.text.split(" ", 2)
    if len(message_parts) < 3:
        return await _send_error()

    time_to_parse = " ".join(message_parts[:2])
    try:
        naive_dt = datetime.strptime(time_to_parse, DT_FORMAT)
    except ValueError:
        return await _send_error()

    dt_local = WARSAW_TZ.localize(naive_dt)
    dt_utc = dt_local.astimezone(pytz.utc)
    if dt_utc <= pytz.utc.localize(datetime.utcnow()) + timedelta(minutes=10):
        return await send_reply(message, text="Please provide a future date.")

    name = message_parts[-1]
    await _add_game(
        Game(
            timestamp=dt_utc.replace(tzinfo=None),
            name=name,
            players=[],
            id=None,
            reminders_sent=False,
        )
    )
    await send_reply(message, text="Game created.")
    return await game_details(message)


@add_command("game cancel", "cancel scheduled game", aliases=["game remove"])
async def game_cancel(message: IncomingMessage) -> Any:
    if not await _active_game_exists():
        return await send_reply(message, text="There is no scheduled game.")
    game = await _get_game_details()
    await _cancel_game(game)
    return await send_reply(message, text="Game canceled.")


@add_command("game join", "join the game", aliases=["join"])
async def game_join(message: IncomingMessage) -> Any:
    if not await _active_game_exists():
        return await send_reply(message, text="There is no scheduled game.")
    game = await _get_game_details()
    if message.user in game.players:
        return await send_reply(message, text="You are already on the list.")
    game.players.append(message.user)
    await _update_players(game)
    await send_reply(message, text="Player added.")


@add_command("game leave", "leave the game", aliases=["leave"])
async def game_leave(message: IncomingMessage) -> Any:
    if not await _active_game_exists():
        return await send_reply(message, text="There is no scheduled game.")
    game = await _get_game_details()
    if message.user not in game.players:
        return await send_reply(message, text="You are not on the list.")
    game.players.remove(message.user)
    await _update_players(game)
    await send_reply(message, text="Player removed.")


@cron_job
async def reminder():
    if not await _active_game_exists():
        return
    game = await _get_game_details()
    while game.timestamp <= datetime.utcnow() + timedelta(minutes=10):
        if game.timestamp <= datetime.utcnow():
            await _cancel_game(game)
            await send_message(
                OutgoingMessage(
                    channel=registry.CHANNEL_GEJMING,
                    thread_ts=None,
                    blocks=[
                        Text(f"It is time for {game.name}!"),
                    ],
                )
            )
            players = " ".join([f"<@{player}>" for player in game.players])
            await send_message(
                OutgoingMessage(
                    channel=registry.CHANNEL_GEJMING,
                    thread_ts=None,
                    blocks=[
                        Text(f"Calling: {players}"),
                    ],
                )
            )
            return
        await sleep(30)
        if not await _active_game_exists():
            return
        game = await _get_game_details()


@cron_job
async def user_reminder():
    if not await _active_game_exists():
        return
    game = await _get_game_details()
    if (
        game.timestamp <= datetime.utcnow() + timedelta(minutes=30)
        and not game.reminders_sent
    ):
        await registry.database.execute(
            GameTable.update()
            .where(GameTable.c.id == game.id)
            .values(reminders_sent=True)
        )
        for player in game.players:
            await send_message(
                OutgoingMessage(
                    channel=player,
                    thread_ts=None,
                    blocks=[
                        Text(
                            f"You have a game ({game.name}) starting in less than half an hour."
                        ),
                    ],
                )
            )
