import os


def _parse_group_id(value: str):
    """Accept either a numeric group ID (e.g. -1001234567890) or a username/invite slug."""
    try:
        return int(value)
    except ValueError:
        return value  # username string like 'FUNToken_OfficialChat'


API_ID = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]
PHONE = os.environ["TELEGRAM_PHONE"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
SOURCE_GROUP_ID = _parse_group_id(os.environ["SOURCE_GROUP_ID"])
TARGET_GROUP_ID = _parse_group_id(os.environ["TARGET_GROUP_ID"])

SESSION_NAME = "userbot_session"
