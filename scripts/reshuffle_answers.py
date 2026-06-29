"""Reshuffle correct-answer positions to reduce A-position bias in lesson quizzes.

Reads each public/lessons/0NNN-*.html, picks a new target letter for every
data-correct button weighted by global deficit, and writes the file back.  A
backup of every modified file is saved under public/lessons/.backup/ so the
operation is reversible.

Usage:
    python scripts/reshuffle_answers.py [--dry-run]
"""

from __future__ import annotations

import argparse
import os
import random
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

# Allow `python scripts/reshuffle_answers.py` from repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import reshuffle_dom as rd  # noqa: E402
from lessons_parser import parse_file  # noqa: E402

LESSONS_DIR = Path(__file__).resolve().parent.parent / "public" / "lessons"
BACKUP_DIR = LESSONS_DIR / ".backup"
SECTION_RE = re.compile(
    r'(<section class="quiz"[^>]*>.*?</section>)', re.DOTALL,
)
LESSON_RE = re.compile(r"^0\d{3}-.+\.html$")
LETTERS = ("A", "B", "C", "D")
RNG = random.Random(20260629)  # Deterministic across runs.


def _is_all_a(per_letter: Counter) -> bool:
    """A lesson is ALL_A iff every correct answer is A."""
    total = sum(per_letter.values())
    return total > 0 and per_letter.get("A", 0) == total


def _build_dist_tracker(per_file: list[dict]) -> Counter:
    """Aggregate global correct-letter counts across all parsed lessons."""
    dist = Counter({lt: 0 for lt in LETTERS})
    for r in per_file:
        for lt, n in r.get("dist", {}).items():
            dist[lt] += n
    return dist


def _pick_target(
    current_letter: str,
    global_dist: Counter,
    lesson_is_all_a: bool,
    moved_in_lesson: int,
) -> str:
    """Pick the new target letter for one quiz.

    Weighting: prefer the letter with the largest global deficit among letters
    != current_letter.  Tie-break randomly.  For ALL_A lessons, the FIRST move
    is forced to B/C/D so we make real progress against the bias instead of
    re-rotating within {A,B,C,D}.
    """
    others = [lt for lt in LETTERS if lt != current_letter]
    if lesson_is_all_a and moved_in_lesson == 0:
        # Force first move in an ALL_A lesson away from A.
        return RNG.choice(["B", "C", "D"])
    # Inverse-weight by current global count: most under-represented wins.
    min_count = min(global_dist[lt] for lt in others)
    under = [lt for lt in others if global_dist[lt] == min_count]
    return RNG.choice(under)


def _process_file(
    path: Path,
    global_dist: Counter,
    dry_run: bool,
    stats: Counter,
) -> None:
    """Reshuffle one lesson file.  Updates global_dist in place as moves land."""
    src = path.read_text(encoding="utf-8")
    lesson_dist = Counter({lt: 0 for lt in LETTERS})
    for lt, n in parse_file(str(path))["dist"].items():
        lesson_dist[lt] = n
    is_all_a = _is_all_a(lesson_dist)

    moved = 0
    sections_done = 0
    sections_skipped = 0

    def _rewrite(match: re.Match) -> str:
        nonlocal moved, sections_done, sections_skipped
        sec = match.group(1)
        choices = rd.extract_choices(sec)
        if len(choices) != 4:
            sections_skipped += 1
            return sec
        correct_count = sum(1 for c in choices if "data-correct" in c.split(">", 1)[0])
        if correct_count != 1:
            sections_skipped += 1
            return sec
        old_letter = rd.find_correct_letter(sec)
        if old_letter is None:
            sections_skipped += 1
            return sec
        target = _pick_target(old_letter, global_dist, is_all_a, moved)
        if target == old_letter:
            # No-op; don't count as a move.
            sections_done += 1
            return sec
        new_sec, _, _ = rd.move_correct_to(sec, target)
        # Update live global tracker so subsequent picks in this run see it.
        global_dist[old_letter] -= 1
        global_dist[target] += 1
        moved += 1
        sections_done += 1
        stats[f"{old_letter}->{target}"] += 1
        if dry_run:
            return sec  # Don't actually rewrite on dry-run.
        return new_sec

    new_src = SECTION_RE.sub(_rewrite, src)
    stats["quizzes_done"] += sections_done
    stats["quizzes_skipped"] += sections_skipped
    stats["moves"] += moved

    if dry_run or new_src == src:
        return

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, BACKUP_DIR / path.name)
    path.write_text(new_src, encoding="utf-8")
    # Sanity-check the rewritten file still parses cleanly.
    post = parse_file(str(path))
    if post.get("total_questions", 0) == 0:
        raise RuntimeError(f"post-write parse yielded 0 questions: {path.name}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dry-run", action="store_true", help="plan only; do not write")
    args = ap.parse_args()

    files = sorted(
        p for p in LESSONS_DIR.iterdir()
        if LESSON_RE.match(p.name)
    )
    if not files:
        print(f"No lesson files in {LESSONS_DIR}", file=sys.stderr)
        return 1

    parsed = [parse_file(str(p)) for p in files]
    global_dist = _build_dist_tracker(parsed)
    print(
        "Baseline:", " ".join(f"{lt}={global_dist[lt]}" for lt in LETTERS),
        f"(total {sum(global_dist.values())})",
    )

    stats: Counter = Counter()
    for p, r in zip(files, parsed):
        _process_file(p, global_dist, args.dry_run, stats)
        stats["files"] += 1

    print(f"Lessons processed: {stats['files']}")
    print(f"Quizzes reshuffled: {stats['moves']}")
    print(f"Quizzes skipped: {stats['quizzes_skipped']}")
    if stats["quizzes_skipped"]:
        print("  (skipped quizzes had != 4 choices or != 1 data-correct)")
    print("Final global:", " ".join(f"{lt}={global_dist[lt]}" for lt in LETTERS))
    move_summary = {k: v for k, v in stats.items() if "->" in k}
    if move_summary:
        print("Moves:")
        for k in sorted(move_summary):
            print(f"  {k}: {move_summary[k]}")
    if args.dry_run:
        print("(dry-run: no files written)")
    else:
        print(f"Backups: {BACKUP_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())