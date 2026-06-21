import json
import re
import google.generativeai as genai
from config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

_SINGLE_LETTERS = set("ABCDE")


def _parse_json(raw: str) -> dict:
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if match:
        return json.loads(match.group())
    return {}


def solve_inline_quiz(message_text: str, button_labels: list[str]) -> tuple[str, str]:
    """
    Handle inline-keyboard quizzes.

    Two modes:
    - Button labels are single letters (A–E): the full options are embedded in
      message_text; ask Gemini which letter is correct.
    - Button labels are full option texts: assign letters A, B, C… and ask Gemini
      which letter/option is correct.

    Returns (correct_letter: str, explanation: str).
    """
    are_letters = all(b.strip().upper() in _SINGLE_LETTERS for b in button_labels)

    if are_letters:
        letters = [b.strip().upper() for b in button_labels]
        prompt = (
            "You are a quiz expert. Below is a multiple-choice quiz question "
            "with its answer options already included in the text.\n\n"
            f"{message_text}\n\n"
            f"The selectable answer buttons are: {', '.join(letters)}\n\n"
            "Identify the correct answer letter and explain why in one sentence.\n"
            "Reply with ONLY valid JSON (no markdown):\n"
            '{ "answer": "<single letter, e.g. B>", "explanation": "<one sentence>" }'
        )
    else:
        options_text = "\n".join(
            f"{chr(65 + i)}. {opt}" for i, opt in enumerate(button_labels)
        )
        prompt = (
            "You are a quiz expert. Answer the following multiple-choice question.\n\n"
            f"Question: {message_text}\n\n"
            f"Options:\n{options_text}\n\n"
            "Reply with ONLY valid JSON (no markdown):\n"
            '{ "answer": "<single letter, e.g. B>", "explanation": "<one sentence>" }'
        )

    response = model.generate_content(prompt)
    data = _parse_json(response.text.strip())
    answer = data.get("answer", "A").strip().upper()
    if answer not in _SINGLE_LETTERS:
        answer = "A"
    return answer, data.get("explanation", "")


def solve_quiz(question: str, options: list[str]) -> tuple[str, str]:
    """
    For poll/text quizzes: given question + option texts, return
    (correct_option_text, explanation).
    """
    options_text = "\n".join(f"{i + 1}. {opt}" for i, opt in enumerate(options))
    prompt = (
        "You are a quiz expert. Answer the following multiple-choice question.\n\n"
        f"Question: {question}\n\n"
        f"Options:\n{options_text}\n\n"
        "Reply with ONLY valid JSON (no markdown):\n"
        '{ "answer": "<exact option text>", "explanation": "<one sentence why>" }'
    )

    response = model.generate_content(prompt)
    data = _parse_json(response.text.strip())
    return data.get("answer", options[0]), data.get("explanation", "")


def solve_open_quiz(question: str) -> str:
    """Short answer for open-ended questions."""
    prompt = (
        "You are a quiz expert. Answer this question concisely (1-2 sentences max):\n\n"
        f"{question}"
    )
    return model.generate_content(prompt).text.strip()
