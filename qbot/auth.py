import base64
import binascii

from passlib.handlers.pbkdf2 import pbkdf2_sha256
from starlette.authentication import (
    AuthCredentials,
    AuthenticationBackend,
    AuthenticationError,
    SimpleUser,
)

from qbot.core import registry
from qbot.db import credentials


async def validate_password(login: str, password: str) -> SimpleUser:
    result = await registry.database.fetch_one(
        credentials.select().where(credentials.c.login == login)
    )
    if result is None or not pbkdf2_sha256.verify(password, result["password"]):
        raise AuthenticationError("Invalid credentials")
    return SimpleUser(result["username"])


class BasicAuthBackend(AuthenticationBackend):
    async def authenticate(self, request):
        if "Authorization" not in request.headers:
            return

        auth = request.headers["Authorization"]
        try:
            scheme, credentials = auth.split()
            if scheme.lower() != "basic":
                return
            decoded = base64.b64decode(credentials).decode("ascii")
        except (ValueError, UnicodeDecodeError, binascii.Error):
            raise AuthenticationError("Invalid credentials")

        username, _, password = decoded.partition(":")
        user = await validate_password(username, password)
        return AuthCredentials(["authenticated"]), user
