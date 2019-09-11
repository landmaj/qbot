from bs4 import BeautifulSoup

from qbot.registry import registry
from qbot.slack_utils import send_slack_message, slack_keyword


@slack_keyword("nosacz", "losowe memiszcze")
async def nosacz(text: str, channel_id: str, **kwargs):
    async with registry.http_session.get("http://www.janusznosacz.pl/losuj") as resp:
        body = await resp.text()

    soup = BeautifulSoup(body, "html.parser")
    image = soup.find("div", {"class": "img-inner-box"}).find("a").find("img")
    image_url = image["src"]

    await send_slack_message(image_url, channel_id)
