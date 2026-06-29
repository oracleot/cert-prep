"""Pure-stdlib HTML parser for public/lessons/*.html quiz blocks."""
from __future__ import annotations
import html.parser, os, re
from pathlib import Path
from typing import Any
_RE_CHOICE = re.compile(r"^([A-D])\)\s*(.*)$")
def _strip(t: str) -> str: return re.sub(r"\s+", " ", t).strip()
def _attr(attrs, name, default=""):
    for k, v in attrs:
        if k == name: return v if v is not None else ""
    return default
class QuizHTMLParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.quizzes: list[dict[str, Any]] = []
        self._quiz: dict[str, Any] | None = None
        self._rationale_map: dict[str, str] = {}
        self._choice_correct = False
        self._choice_letter: str | None = None
        self._choice_text_parts: list[str] = []
        self._aside_letter: str | None = None
        self._stack: list[tuple[str, list[str]]] = []
    def parse(self, html: str, src: str = "") -> list[dict[str, Any]]:
        self._source = src
        self.feed(html)
        self.close()
        return self.quizzes
    def _open_quiz(self, attrs) -> None:
        self._quiz = {"id": None, "multi": False, "answers_expected": 1, "choices": []}
        if any(k == "data-quiz" for k, _ in attrs):
            v = _attr(attrs, "data-quiz")
            if v: self._quiz["id"] = v
        if any(k == "data-multi" for k, _ in attrs): self._quiz["multi"] = True
        try: self._quiz["answers_expected"] = int(_attr(attrs, "data-answers", "1"))
        except ValueError: pass
        self._rationale_map = {}
        self._choice_letter = None
        self._choice_text_parts = []
        self._aside_letter = None
        self._stack = []
    def _flush_choice(self) -> None:
        if not self._quiz or not self._choice_letter: return
        text = _strip("".join(self._choice_text_parts))
        m = _RE_CHOICE.match(text)
        letter, choice_text = (m.group(1), m.group(2).strip()) if m else (self._choice_letter, text)
        if any(c["letter"] == letter for c in self._quiz["choices"]):
            self._choice_letter = None; self._choice_text_parts = []; return
        self._quiz["choices"].append({"letter": letter, "text": choice_text,
            "correct": self._choice_correct, "rationale_for": self._rationale_map.get(letter, "")})
        self._choice_letter = None; self._choice_text_parts = []
    def _close_quiz(self) -> None:
        if not self._quiz: return
        if self._choice_letter: self._flush_choice()
        for ch in self._quiz["choices"]:
            if not ch["rationale_for"]: ch["rationale_for"] = self._rationale_map.get(ch["letter"], "")
        self.quizzes.append(self._quiz)
        self._quiz = None
    def handle_starttag(self, tag: str, attrs) -> None:
        cls = _attr(attrs, "class", "")
        if tag == "section" and "quiz" in cls: self._open_quiz(attrs); return
        if not self._quiz: return
        if tag == "button" and "choice" in cls:
            if self._choice_letter is not None: self._flush_choice()
            self._choice_correct = any(k == "data-correct" for k, _ in attrs)
            self._choice_letter = None; self._choice_text_parts = []
            self._stack.append(("button", [])); return
        if tag == "aside":
            rf = _attr(attrs, "data-rationale-for", "")
            if rf: self._aside_letter = rf; self._stack.append(("aside", [])); return
            self._stack.append(("aside-ignore", [])); return
        self._stack.append((tag, []))
    def handle_endtag(self, tag: str) -> None:
        if not self._quiz: return
        if tag == "section": self._close_quiz(); return
        if not self._stack: return
        top, parts = self._stack[-1]
        if top == "button" and tag == "button":
            self._stack.pop()
            text = _strip("".join(parts))
            m = _RE_CHOICE.match(text)
            self._choice_letter = m.group(1) if m else (text[0] if text and text[0] in "ABCD" else None)
            if self._choice_letter is not None: self._flush_choice()
            self._choice_letter = None; self._choice_text_parts = []; return
        if top == "aside" and tag == "aside":
            self._stack.pop()
            if self._aside_letter: self._rationale_map[self._aside_letter] = _strip("".join(parts))
            self._aside_letter = None; return
        if top == "aside-ignore" and tag == "aside": self._stack.pop(); return
        if top == tag: self._stack.pop()
    def handle_data(self, data: str) -> None:
        if not data.strip(): return
        if self._stack: self._stack[-1][1].append(data)
        # Also accumulate in _choice_text_parts when inside a button
        if self._stack and self._stack[-1][0] == "button":
            self._choice_text_parts.append(data)
def parse_file(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as fh: html = fh.read()
    source_file = os.path.basename(path)
    parser = QuizHTMLParser()
    quizzes = parser.parse(html, source_file)
    for i, q in enumerate(quizzes):
        if q["id"] is None: q["id"] = str(i + 1)
    for q in quizzes:
        dist: dict[str, int] = {"A": 0, "B": 0, "C": 0, "D": 0}
        for ch in q["choices"]:
            if ch["correct"]: dist[ch["letter"]] = dist.get(ch["letter"], 0) + 1
        q["answer_dist"] = dist; q["answers_count"] = sum(dist.values())
    total = sum(q["answers_count"] for q in quizzes)
    dist: dict[str, int] = {"A": 0, "B": 0, "C": 0, "D": 0}
    for q in quizzes:
        for k, v in q["answer_dist"].items(): dist[k] += v
    return {
        "file": source_file, "lessons": 1, "quizzes": quizzes,
        "total_questions": total, "dist": dist,
        "dist_pct": {k: round(v / total * 100, 1) if total else 0.0 for k, v in dist.items()},
        "all_a": all(q["answer_dist"].get("A", 0) == q["answers_count"] and q["answers_count"] > 0 for q in quizzes) if quizzes else False,
    }
def scan_lessons(lessons_dir: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    pattern = re.compile(r"^0\d{3}-.+\.html$")
    for entry in sorted(os.listdir(lessons_dir)):
        if pattern.match(entry):
            path = os.path.join(lessons_dir, entry)
            try: results.append(parse_file(path))
            except Exception as exc:
                results.append({"file": entry, "lessons": 0, "quizzes": [], "error": str(exc),
                    "total_questions": 0, "dist": {"A": 0, "B": 0, "C": 0, "D": 0},
                    "dist_pct": {"A": 0.0, "B": 0.0, "C": 0.0, "D": 0.0}, "all_a": False})
    return results
def load_aws_terms(concepts_dir: str) -> set[str]:
    terms: set[str] = set()
    if not os.path.isdir(concepts_dir): return terms
    for fname in sorted(os.listdir(concepts_dir)):
        if not fname.endswith(".yaml"): continue
        path = os.path.join(concepts_dir, fname)
        try: text = Path(path).read_text(encoding="utf-8")
        except Exception: continue
        in_block = False
        for line in text.splitlines():
            s = line.lstrip()
            if s.startswith("facts:") or s.startswith("traps:"): in_block = True; continue
            if in_block and s and not s.startswith(" ") and not s.startswith("-"): in_block = False
            if in_block and s.startswith("- \""):
                for word in re.findall(r"[A-Za-z][A-Za-z0-9\-]*", s[2:].rstrip(",\"").strip()):
                    if len(word) > 2: terms.add(word)
    return terms
