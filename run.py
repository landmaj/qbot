import os

import uvicorn
from qbot.app import app

PORT = os.environ.get("QBOT_PORT", 5000)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=int(PORT))
