# Telegram Quiz Userbot

A Telethon userbot that scrapes quiz questions from a source Telegram group, solves them instantly with Google Gemini, and forwards the question + highlighted answer to a target group where the account is admin.

## Run & Operate

- **Start the bot:** Use the "Telegram Userbot" workflow (Run button), or `python userbot/bot.py`
- First run will prompt for a Telegram login code in the console — enter it there to create a session file

## Stack

- Python 3.11
- Telethon — Telegram MTProto userbot client
- google-generativeai — Gemini 2.0 Flash for quiz solving
- python-dotenv (optional, secrets are loaded from Replit env)

## Where things live

- `userbot/bot.py` — main entry point, event handler
- `userbot/config.py` — loads all env vars/secrets
- `userbot/quiz_parser.py` — detects and parses poll quizzes and text-based quizzes
- `userbot/gemini_solver.py` — sends quiz to Gemini, returns correct answer + explanation
- `userbot/formatter.py` — formats the forwarded message with answer highlighted
- `userbot_session.session` — Telethon auth session (auto-created, gitignored)

## Required Secrets

| Secret | Description |
|---|---|
| `TELEGRAM_API_ID` | From https://my.telegram.org/apps |
| `TELEGRAM_API_HASH` | From https://my.telegram.org/apps |
| `TELEGRAM_PHONE` | Your phone in international format, e.g. +12345678900 |
| `GEMINI_API_KEY` | From https://aistudio.google.com/app/apikey |
| `SOURCE_GROUP_ID` | Group ID to watch for quizzes (negative integer) |
| `TARGET_GROUP_ID` | Group ID to post answers to (negative integer, you must be admin) |

## Architecture decisions

- **Userbot (not bot account):** Telethon logs in as a real user account so it can read messages in any group it's a member of, including groups that don't allow bots.
- **Gemini 2.0 Flash:** Fast, cost-effective model well-suited for real-time quiz answering.
- **Two quiz modes:** Handles both native Telegram Poll/Quiz messages and plain-text quiz messages with numbered options.
- **Session file:** Telethon stores auth in `userbot_session.session` — keep it safe and never commit it.

## First-run login flow

On first start, Telethon will ask for your phone number (pre-filled from env) and then send a login code to your Telegram app. Enter the code in the console. After that, the session is saved and future starts are automatic.

## User preferences

- Python project, not Node/TypeScript
- Uses Telethon userbot (not Bot API)
- Gemini 2.0 Flash for AI solving
