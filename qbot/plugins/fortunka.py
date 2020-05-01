from asyncpg import UniqueViolationError

from qbot.backblaze import upload_image
from qbot.command import add_command
from qbot.core import registry
from qbot.db import add_recently_seen, fortunki, query_with_recently_seen
from qbot.message import Image, IncomingMessage, TextWithButton, send_reply

PLUGIN_NAME = "fortunka"


@add_command(
    "fortunka", "`!fortunka [-- ID]`", channel="fortunki", aliases=["f", "funia"]
)
async def fortunka_cmd(message: IncomingMessage):
    identifier = None
    if message.text:
        try:
            identifier = int(message.text)
        except ValueError:
            await send_reply(message, text="Niepoprawne ID.")
            return
    result = await query_with_recently_seen(fortunki, identifier)
    if result is None:
        await send_reply(
            message, text="Do 2137 fortunek jeszcze trochę. Tej o którą prosisz nie ma."
        )
        return
    if result["image"]:
        await send_reply(
            message,
            blocks=[
                Image(image_url=result["text"], alt_text=f"fortunka #{result['id']}")
            ],
        )
    else:
        await send_reply(
            message,
            blocks=[TextWithButton(text=result["text"], button_text=str(result["id"]))],
        )
    await add_recently_seen(fortunki, result["id"])


@add_command(
    "fortunka dodaj", "`!fortunka dodaj -- TEXT`", channel="fortunki", safe_to_fix=False
)
async def fortunka_dodaj(message: IncomingMessage):
    if not message.text and not message.files:
        await send_reply(message, text="Pustych fortunek nie dodaję!")
        return
    elif message.text and message.files:
        await send_reply(message, text="Tekst albo obrazek, ale nie oba jednocześnie.")
        return
    elif message.files:
        if len(message.files) != 1:
            await send_reply(message, text="Poproszę pojedynczy plik.")
            return
        mimetype: str = message.files[0]["mimetype"]
        if mimetype.split("/")[0] != "image":
            await send_reply(message, text="Przesłany plik nie jest obrazkiem.")
            return
        img_url: str = message.files[0]["url_private"]
        resp = await registry.http_client.get(
            img_url,
            headers={"Authorization": f"Bearer {str(registry.SLACK_TOKEN)}"},
            allow_redirects=False,  # to avoid login screen
        )
        if not 200 <= resp.status_code < 300:
            await send_reply(message, "Nie udało się pobrać obrazka.")
            return
        b2_image = await upload_image(
            content=resp.content, plugin=PLUGIN_NAME, bucket=registry.b3
        )
        if b2_image is None:
            await send_reply(message, "Coś poszło nie tak...")
            return
        elif b2_image.exists:
            await send_reply(message, "Taka fortunka już istnieje.")
            return
        try:
            async with registry.database.transaction():
                identifier = await registry.database.execute(
                    query=fortunki.insert(),
                    values={"text": b2_image.url, "image": b2_image.id},
                )
        except UniqueViolationError:
            await send_reply(message, text="Drugi raz nie dodaję!")
            return
    else:
        try:
            async with registry.database.transaction():
                identifier = await registry.database.execute(
                    query=fortunki.insert(), values={"text": message.text}
                )
        except UniqueViolationError:
            await send_reply(message, text="Drugi raz nie dodaję!")
            return
    await send_reply(message, text=f"Fortunka {identifier} dodana!")
