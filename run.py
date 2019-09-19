import os
import time

import uvicorn
from starlette.config import environ

from qbot.app import app

HOST = os.environ.get("Q_HOST", "0.0.0.0")
PORT = os.environ.get("Q_PORT", 5000)
environ["DEPLOY_TIMESTAMP"] = str(int(time.time()))

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=int(PORT))
