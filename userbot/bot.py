import asyncio
import logging
import sys
import os
import time

sys.path.insert(0, os.path.dirname(__file__))

from telethon import TelegramClient, events
from telethon.tl.types import User, Channel

from config import API_ID, API_HASH, PHONE, SESSION_NAME, SOURCE_GROUP_ID, TARGET_GROUP_ID
from keep_alive import keep_alive
from quiz_parser import parse_inline_keyboard_quiz, diagnose_message
from gemini_solver import solve_inline_quiz
from formatter import format_quiz_with_ai_answer, clean_result_message

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
log = logging.getLogger(__name__)

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)


@client.on(events.NewMessage(chats=SOURCE_GROUP_ID))
async def handle_message(event):
    message = event.message
    text = message.text or message.message or ""
    text_preview = text[:80].replace("\n", " ") if text else "<no text>"

    # ── Sender identification ─────────────────────────────────────────────────
    sender = await event.get_sender()
    sender_type = type(sender).__name__
    sender_name = (
        getattr(sender, "username", None)
        or getattr(sender, "title", None)
        or getattr(sender, "first_name", None)
        or str(getattr(sender, "id", "unknown"))
    )
    is_bot_account = isinstance(sender, User) and getattr(sender, "bot", False)
    is_channel_post = isinstance(sender, Channel) or sender is None
    is_human = isinstance(sender, User) and not getattr(sender, "bot", False)

    log.info(
        f"[MSG id={message.id}] sender={sender_name!r} "
        f"type={sender_type} bot={is_bot_account} channel={is_channel_post} "
        f"has_keyboard={message.reply_markup is not None} | {text_preview!r}"
    )

    # Only process messages from the exact quiz bot
    QUIZ_BOT_USERNAME = "fun_message_scoring_bot"
    sender_username = getattr(sender, "username", None) or ""
    if sender_username.lower() != QUIZ_BOT_USERNAME:
        log.info(f"  → SKIP: sender is not {QUIZ_BOT_USERNAME!r} (got {sender_username!r})")
        return

    log.info(f"  → PASS: sender is {QUIZ_BOT_USERNAME!r}")

    try:
        # ── Quiz result message ───────────────────────────────────────────────
        if text.startswith("✅ Quiz finished!"):
            log.info("  → Quiz result message detected — cleaning and forwarding.")
            cleaned = clean_result_message(text)
            if cleaned:
                await client.send_message(TARGET_GROUP_ID, cleaned)
                log.info("  → Cleaned quiz result forwarded.")
            else:
                log.warning("  → Quiz result cleaned to empty string — skipped.")
            return

        # ── Inline keyboard quiz ──────────────────────────────────────────────
        diagnosis = diagnose_message(message)
        log.info(f"  → Quiz diagnosis: {diagnosis}")

        inline = parse_inline_keyboard_quiz(message)
        if inline:
            t0 = time.monotonic()
            msg_text, buttons = inline
            log.info(f"  → Inline quiz confirmed | buttons: {buttons}")

            correct_letter, _ = await asyncio.to_thread(
                solve_inline_quiz, msg_text, buttons
            )
            log.info(f"  → Gemini answer: {correct_letter!r}")

            out = format_quiz_with_ai_answer(msg_text, buttons, correct_letter)
            await client.send_message(TARGET_GROUP_ID, out)
            elapsed = (time.monotonic() - t0) * 1000
            log.info(f"  → ✅ Posted in {elapsed:.0f} ms")
            return

        log.info("  → No quiz pattern matched — message ignored.")

    except Exception as e:
        log.error(f"  → ERROR: {e}", exc_info=True)


async def main():
    keep_alive()
    log.info("Starting Telegram userbot...")
    await client.start(phone=PHONE)
    me = await client.get_me()
    log.info(f"Logged in as: {me.first_name} (@{me.username})")
    log.info(f"Watching: {SOURCE_GROUP_ID}  →  Posting to: {TARGET_GROUP_ID}")
    log.info("Filter: only processing messages from @fun_message_scoring_bot")
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
