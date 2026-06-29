"""String-level HTML manipulation for quiz <section class="quiz"> blocks.

Pure functions: read/modify a single section substring, return the rewrite.
No side effects, no I/O.  Letter keys are 'A'|'B'|'C'|'D'.
"""

from __future__ import annotations

import re
from typing import Optional

# Single <button class="choice" [data-correct]>X) text</button> line.
_BUTTON_RE = re.compile(
    r'<button\s+class="choice"(?:\s+data-correct)?\s*>([^<]*)</button>',
    re.IGNORECASE,
)
_PREFIX_RE = re.compile(r"^([A-D])\)\s*(.*)$", re.S)
_RATIONALE_RE = re.compile(
    r'<aside\s+data-rationale-for="([A-D])"\s*>(.*?)</aside>', re.DOTALL,
)
_EXPLANATION_RE = re.compile(
    r'<aside\s+class="explanation"\s*>(.*?)</aside>', re.DOTALL,
)
_LETTERS = ("A", "B", "C", "D")


def _strip_prefix(inner: str) -> tuple[str, str]:
    """Return (letter, body) from a button's inner text."""
    m = _PREFIX_RE.match(inner.strip())
    if m:
        return m.group(1), m.group(2).strip()
    for ch in inner.strip():
        if ch in _LETTERS:
            return ch, inner.strip()[1:].lstrip(") ").strip()
    return "", inner.strip()


def extract_choices(section_html: str) -> list[str]:
    """Return the four choice button lines in DOM order."""
    return [m.group(0) for m in _BUTTON_RE.finditer(section_html)] or []


def extract_option_texts(section_html: str) -> dict[str, str]:
    """Map letter -> option text body."""
    out: dict[str, str] = {}
    for btn in extract_choices(section_html):
        m = _BUTTON_RE.search(btn)
        if not m:
            continue
        letter, body = _strip_prefix(m.group(1))
        if letter:
            out[letter] = body
    return out


def find_correct_letter(section_html: str) -> Optional[str]:
    """Return the letter whose button carries data-correct, else None."""
    for btn in extract_choices(section_html):
        if "data-correct" in btn.split(">", 1)[0]:
            m = _BUTTON_RE.search(btn)
            if not m:
                continue
            letter, _ = _strip_prefix(m.group(1))
            return letter or None
    return None


def extract_rationales(section_html: str) -> dict[str, str]:
    """Map letter -> full <aside data-rationale-for="X">...</aside> substring."""
    return {m.group(1): m.group(0) for m in _RATIONALE_RE.finditer(section_html)}


def extract_explanation(section_html: str) -> Optional[str]:
    """Return the full <aside class="explanation">...</aside> substring or None."""
    m = _EXPLANATION_RE.search(section_html)
    return m.group(0) if m else None


def relabel_button(button_html: str, new_letter: str) -> str:
    """Replace the "X) " prefix in a button's inner text with "Y) "."""
    m = _BUTTON_RE.search(button_html)
    if not m:
        return button_html
    inner = m.group(1)
    _, body = _strip_prefix(inner)
    return button_html.replace(inner, f"{new_letter}) {body}", 1)


def _replace_choice_block(section_html: str, new_choices: list[str]) -> str:
    """Swap the contiguous run of choice button lines."""
    matches = list(_BUTTON_RE.finditer(section_html))
    if not matches:
        return section_html
    first, last = matches[0].start(), matches[-1].end()
    return section_html[:first] + "\n    ".join(new_choices) + section_html[last:]


def move_correct_to(section_html: str, target_letter: str) -> tuple[str, str, str]:
    """Swap the correct button into target_letter's slot.

    Displaced text fills the slot the correct button vacated.  All four option
    texts are preserved; only letter prefixes and DOM order change.  Rationales
    are re-keyed by option-text identity so each rationale follows its option.
    Returns (new_section, new_correct_letter, old_correct_letter).
    """
    old_letter = find_correct_letter(section_html)
    if old_letter is None or old_letter == target_letter:
        return section_html, old_letter or "", old_letter or ""

    old_texts = extract_option_texts(section_html)
    buttons = extract_choices(section_html)
    correct_idx = next(
        i for i, b in enumerate(buttons) if "data-correct" in b.split(">", 1)[0]
    )
    target_idx = _LETTERS.index(target_letter)

    # Strip data-correct from the displaced button and relabel it to old_letter.
    displaced = buttons[target_idx]
    if "data-correct" in displaced.split(">", 1)[0]:
        displaced = re.sub(r"\s+data-correct", "", displaced, count=1)
    displaced = relabel_button(displaced, old_letter)

    # Relabel the correct button with target_letter and swap into target slot.
    correct_btn = relabel_button(buttons[correct_idx], target_letter)
    new_buttons = list(buttons)
    new_buttons[target_idx] = correct_btn
    new_buttons[correct_idx] = displaced
    section_html = _replace_choice_block(section_html, new_buttons)

    # Re-key rationales by option-text identity in a single pass so later
    # rewrites never clobber earlier ones.
    new_texts = extract_option_texts(section_html)
    text_to_new_letter = {text: lt for lt, text in new_texts.items()}
    rekey_map: dict[str, str] = {
        old_lt: text_to_new_letter.get(old_texts.get(old_lt, ""), old_lt)
        for old_lt in _LETTERS
    }

    def _rewrite_tag(match: re.Match) -> str:
        return f'<aside data-rationale-for="{rekey_map.get(match.group(1), match.group(1))}">'

    section_html = re.sub(
        r'<aside\s+data-rationale-for="([A-D])"\s*>', _rewrite_tag, section_html,
    )
    return section_html, target_letter, old_letter