import re
from telethon.tl.types import Message, MessageMediaPoll, ReplyInlineMarkup

# Matches A) A. A: A - with optional leading emoji/whitespace
_OPTION_LINE_RE = re.compile(r'^\s*[^\w]*([A-Ea-e])\s*[.):|\-]\s*(.+)')
# Matches button labels that are (or start with) a single letter A-E
_LETTER_BTN_RE = re.compile(r'^([A-Ea-e])\s*[.):|\-]?\s*$')


def _normalize_buttons(raw_labels: list[str]) -> list[str]:
    """
    Normalize button labels: if a button is purely a letter like 'A', 'B)', 'C.'
    return just the uppercase letter. Otherwise return the original text stripped.
    """
    normalized = []
    for label in raw_labels:
        m = _LETTER_BTN_RE.match(label.strip())
        normalized.append(m.group(1).upper() if m else label.strip())
    return normalized


def parse_inline_keyboard_quiz(message: Message) -> tuple[str, list[str]] | None:
    """
    Detect a quiz sent as a text message with inline keyboard buttons.
    Returns (message_text, normalized_button_labels) or None.
    """
    if not message.reply_markup or not isinstance(message.reply_markup, ReplyInlineMarkup):
        return None

    raw_buttons: list[str] = []
    for row in message.reply_markup.rows:
        for btn in row.buttons:
            label = getattr(btn, "text", "").strip()
            if label:
                raw_buttons.append(label)

    if len(raw_buttons) < 1:
        return None

    buttons = _normalize_buttons(raw_buttons)

    text = (message.text or message.message or "").strip()
    # Accept even if text is empty — caption might be on media
    if not text and message.media is None:
        return None

    return text or "", buttons


def parse_text_quiz(text: str) -> tuple[str, list[str]] | None:
    """
    Detect a plain-text quiz with lettered/numbered options (no keyboard).
    Returns (question, [option_text, ...]) or None.
    """
    if not text:
        return None

    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    if len(lines) < 3:
        return None

    option_lines = [(i, l) for i, l in enumerate(lines) if _OPTION_LINE_RE.match(l)]
    if len(option_lines) < 2:
        return None

    first_option_idx = option_lines[0][0]
    if first_option_idx == 0:
        return None

    question = " ".join(lines[:first_option_idx])
    options = [_OPTION_LINE_RE.sub(r'\2', l).strip() for _, l in option_lines]
    return question, options


def parse_poll_quiz(message: Message) -> tuple[str, list[str]] | None:
    """Extract question and options from a native Telegram Poll/Quiz message."""
    if not message.media or not isinstance(message.media, MessageMediaPoll):
        return None
    poll = message.media.poll
    question = poll.question.text if hasattr(poll.question, "text") else str(poll.question)
    options = [
        (a.text.text if hasattr(a.text, "text") else str(a.text))
        for a in poll.answers
    ]
    return question, options


def diagnose_message(message: Message) -> str:
    """
    Return a human-readable string explaining what the parser sees in the message.
    Used for debug logging.
    """
    parts = []

    text = message.text or message.message or ""
    parts.append(f"text_len={len(text)}")

    if message.reply_markup and isinstance(message.reply_markup, ReplyInlineMarkup):
        raw = []
        for row in message.reply_markup.rows:
            for btn in row.buttons:
                raw.append(getattr(btn, "text", "?"))
        normalized = _normalize_buttons(raw)
        parts.append(f"keyboard_buttons={raw} → normalized={normalized}")
    else:
        markup_type = type(message.reply_markup).__name__ if message.reply_markup else "None"
        parts.append(f"no_inline_keyboard (markup={markup_type})")

    if message.media:
        parts.append(f"media={type(message.media).__name__}")

    if text:
        option_hits = [l.strip() for l in text.splitlines() if _OPTION_LINE_RE.match(l.strip())]
        parts.append(f"option_lines_found={option_hits[:5]}")

    return " | ".join(parts)


def is_quiz_message(message: Message) -> bool:
    """Return True if the message looks like any supported quiz format."""
    if message.media and isinstance(message.media, MessageMediaPoll):
        return True
    if parse_inline_keyboard_quiz(message):
        return True
    if message.text and parse_text_quiz(message.text):
        return True
    return False
