import random

from qbot.plugins.excuse import excuse_command
from qbot.plugins.fortunka import fortunka_cmd
from qbot.plugins.nosacz import janusz, nosacz
from qbot.plugins.sucharki import sucharek_cmd
from qbot.scheduler import job


@job(3600)
async def poke():
    func = random.choice([fortunka_cmd, nosacz, janusz, sucharek_cmd, excuse_command])
    await func()
