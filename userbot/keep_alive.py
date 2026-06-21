import os
import logging
from threading import Thread
from flask import Flask

log = logging.getLogger(__name__)

app = Flask(__name__)


@app.route("/")
def home():
    return "Telegram Quiz Userbot is alive ✅", 200


@app.route("/health")
def health():
    return {"status": "ok"}, 200


def run():
    port = int(os.environ.get("PORT", 8080))
    log.info(f"Keep-alive server starting on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


def keep_alive():
    t = Thread(target=run, daemon=True)
    t.start()
