import re

_OPTION_RE = re.compile(r'^([A-Ea-e])[.\)]\s*(.+)')
_SINGLE_LETTERS = set("ABCDE")

# ── Result-message cleaning ───────────────────────────────────────────────────

_RESULT_CUTOFF_PATTERNS = [
    r"earned \d+ Wheel of Fortune spin(?:s)? each\s*🎉",
    r"earned \d+ spin(?:s)? each\s*🎉",
    r"🎉[^\n]*$",
]

_PROMO_START_RE = re.compile(
    r"Not getting prizes\?|Want more rewards\?|Join our|Follow us|t\.me/",
    re.IGNORECASE,
)


def clean_result_message(text: str) -> str:
    """
    Keep everything from '✅ Quiz finished!' up to and including the
    'earned N spin(s) each 🎉' line, then drop all promo lines.
    """
    lines = text.splitlines()
    cutoff_idx = None

    for i, line in enumerate(lines):
        for pat in _RESULT_CUTOFF_PATTERNS:
            if re.search(pat, line, re.IGNORECASE):
                cutoff_idx = i
                break

    if cutoff_idx is not None:
        lines = lines[: cutoff_idx + 1]
    else:
        while lines and _PROMO_START_RE.search(lines[-1]):
            lines.pop()

    clean = []
    for line in lines:
        if _PROMO_START_RE.search(line):
            break
        clean.append(line)

    return "\n".join(clean).strip()


# ── Quiz formatting ───────────────────────────────────────────────────────────

def _extract_options(text: str) -> tuple[str, list[tuple[str, str]]] | None:
    """
    Split message text into (question_block, [(letter, option_text), ...]).
    Returns None if no options found.
    """
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    option_pairs: list[tuple[str, str]] = []
    first_opt_idx = None

    for i, line in enumerate(lines):
        m = _OPTION_RE.match(line)
        if m:
            if first_opt_idx is None:
                first_opt_idx = i
            option_pairs.append((m.group(1).upper(), m.group(2).strip()))

    if len(option_pairs) < 2 or first_opt_idx is None or first_opt_idx == 0:
        return None

    question_block = "\n".join(lines[:first_opt_idx])
    return question_block, option_pairs


def format_quiz_with_ai_answer(
    message_text: str,
    button_labels: list[str],
    correct_letter: str,
) -> str:
    """
    Build a clean quiz message and append the AI answer at the bottom.

    Output shape:
        <question text>

        A) Option one
        B) Option two
        ...

        AI Suggested Answer is 🎯
        B) Option two
    """
    correct = correct_letter.strip().upper()
    are_letters = all(b.strip().upper() in _SINGLE_LETTERS for b in button_labels)

    lines: list[str] = []
    correct_option_text: str = correct  # fallback if we can't resolve it

    if are_letters:
        parsed = _extract_options(message_text)
        if parsed:
            question_block, option_pairs = parsed
            lines.append(question_block)
            lines.append("")
            for letter, opt_text in option_pairs:
                lines.append(f"{letter}) {opt_text}")
                if letter == correct:
                    correct_option_text = opt_text
        else:
            # Can't parse options from text — show raw text and just name the letter
            lines.append(message_text)
            correct_option_text = correct
    else:
        # Buttons carry the full option text; assign letters A, B, C…
        lines.append(message_text)
        lines.append("")
        for i, opt in enumerate(button_labels):
            letter = chr(65 + i)
            lines.append(f"{letter}) {opt}")
            if letter == correct:
                correct_option_text = opt

    lines.append("")
    lines.append("AI Suggested Answer is 🎯")
    lines.append(f"{correct}) {correct_option_text}")

    return "\n".join(lines)
