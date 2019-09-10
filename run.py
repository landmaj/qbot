import os

import uvicorn

from qbot.registry import registry

HOST = os.environ.get("Q_HOST", "0.0.0.0")
PORT = os.environ.get("Q_PORT", 5000)

if __name__ == "__main__":
    uvicorn.run(registry.app, host=HOST, port=int(PORT))
