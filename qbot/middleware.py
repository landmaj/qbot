class CloudflareMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] in ("http", "websocket"):
            headers = dict(scope["headers"])

            if b"x-forwarded-proto" in headers:
                # Determine if the incoming request was http or https based on
                # the X-Forwarded-Proto header.
                x_forwarded_proto = headers[b"x-forwarded-proto"].decode("ascii")
                scope["scheme"] = x_forwarded_proto.strip()

            if b"cf-connecting-ip" in headers:
                # Determine the client address from the CF-Connecting-IP header.
                # We've lost the connecting client's port # information by now,
                # so only include the host.
                host = headers[b"cf-connecting-ip"].decode("ascii")
                port = 0
                scope["client"] = (host, port)

            if b"cf-ipcountry" in headers:
                # Determine the client country from the CF-IPCountry header.
                country_code = headers[b"cf-ipcountry"].decode("ascii")
                scope["country_code"] = country_code

        return await self.app(scope, receive, send)
