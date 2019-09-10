import os

import uvicorn

from qbot.app import app

HOST = os.environ.get("Q_HOST", "0.0.0.0")
PORT = os.environ.get("Q_PORT", 5000)

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=int(PORT))
