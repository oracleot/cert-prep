#!/usr/bin/env python3
"""Lesson validation CLI. Run: python validate_lessons.py [--before f.json] [--after f.json]"""
import argparse, json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from lessons_parser import scan_lessons, load_aws_terms
from shared_terms import NON_AWS_HARDCODED, AWS_ALLOWLIST

LESSONS_DIR = Path(__file__).parent.parent / "public" / "lessons"
CONCEPTS_DIR = Path(__file__).parent.parent / "agents" / "data" / "concepts" / "dva-c02"


def _build_allowlist() -> set[str]:
    return load_aws_terms(str(CONCEPTS_DIR)) | AWS_ALLOWLIST


def _soft_non_aws(text: str, allowlist: set[str]) -> bool:
    """True if text looks like a non-AWS distractor (soft gate)."""
    stripped = text.lstrip("ABCD) ").strip()
    words = stripped.split()
    return not any(w.rstrip(".,;:!") in allowlist for w in words if len(w.rstrip(".,;:!")) > 2)


def _collect_distractors(results, allowlist):
    hard, soft = [], []
    for r in results:
        for q in r.get("quizzes", []):
            for ch in q["choices"]:
                txt = ch["text"]
                for term in NON_AWS_HARDCODED:
                    if term in txt: hard.append((r["file"], str(q["id"]), txt))
                if _soft_non_aws(txt, allowlist) and not ch["correct"]:
                    soft.append((r["file"], str(q["id"]), ch["letter"], txt))
    return hard, soft


def _snapshot(results):
    total_dist = {"A": 0, "B": 0, "C": 0, "D": 0}
    total_q, all_a, multi = 0, 0, 0
    multi_dist = {"A": 0, "B": 0, "C": 0, "D": 0}
    for r in results:
        for k, v in r.get("dist", {}).items(): total_dist[k] += v
        total_q += r.get("total_questions", 0)
        if r.get("all_a"): all_a += 1
        for k, v in r.get("multi_dist", {}).items(): multi_dist[k] += v
        multi += r.get("multi_count", 0)
    return {
        "files": [{"file": r["file"], "lessons": r.get("lessons", 1),
            "quizzes": len(r.get("quizzes", [])), "total_questions": r.get("total_questions", 0),
            "dist": r.get("dist", {}), "dist_pct": r.get("dist_pct", {}), "all_a": r.get("all_a", False)}
            for r in results],
        "summary": {
            "total_files": len(results), "total_questions": total_q,
            "dist": total_dist,
            "dist_pct": {k: round(v / total_q * 100, 1) if total_q else 0.0 for k, v in total_dist.items()},
            "all_a_lessons": all_a,
        },
        "multi_count": multi,
        "multi_dist": multi_dist,
        "multi_dist_pct": {k: round(v / sum(multi_dist.values()) * 100, 1) if sum(multi_dist.values()) else 0.0 for k, v in multi_dist.items()},
    }


def _print_report(results, allowlist, before_snap=None):
    total_dist = {"A": 0, "B": 0, "C": 0, "D": 0}
    total_q, multi_count, all_a_lessons, over50 = 0, 0, [], []
    multi_dist = {"A": 0, "B": 0, "C": 0, "D": 0}
    for r in results:
        for k, v in r.get("dist", {}).items(): total_dist[k] += v
        total_q += r.get("total_questions", 0)
        if r.get("all_a"): all_a_lessons.append(r["file"])
        a_pct = r.get("dist_pct", {}).get("A", 0.0)
        if a_pct > 50.0 and r.get("total_questions", 0) > 0: over50.append(r["file"])
        for k, v in r.get("multi_dist", {}).items(): multi_dist[k] += v
        multi_count += r.get("multi_count", 0)

    print("## Per-lesson A% (single-select only)")
    print(f"{'file':<52} {'N':>2}  {'A%':>5}  {'B%':>5}  {'C%':>5}  {'D%':>5}  flag")
    for r in results:
        n = r.get("total_questions", 0)
        p = r.get("dist_pct", {})
        flag = "ALL_A" if r.get("all_a") else ""
        print(f"{r['file'][:50]:<52} {n:>2}  {p.get('A',0):5.1f}  {p.get('B',0):5.1f}  {p.get('C',0):5.1f}  {p.get('D',0):5.1f}  {flag}")

    print("\n## Global distribution (single-select)")
    for k in "ABCD":
        v = total_dist[k]
        print(f"{k}: {v:3d} ({v/total_q*100:.1f}%)" if total_q else f"{k}:   0 (0.0%)")

    print("\n## Multi-select coverage")
    print(f"Multi-select questions: {multi_count}")
    print(f"Multi-select correct-button distribution: total correct buttons = {sum(multi_dist.values())}")
    for k in "ABCD":
        v = multi_dist[k]
        print(f"  {k}: {v}")

    print("\n## Distractor check")
    hard_hits, soft_hits = _collect_distractors(results, allowlist)
    print(f"Non-AWS terms found (hard list): {len(hard_hits)}")
    for fname, qid, txt in hard_hits:
        print(f'  - "{txt.strip()}" in {fname} Q{qid}')
    print(f"\nCandidate non-AWS distractors (soft check, warn only): {len(soft_hits)}")
    for fname, qid, letter, txt in soft_hits[:10]:
        print(f'  - "{txt.strip()}" in {fname} Q{qid} choice {letter}')

    print("\n## Acceptance gates")
    a_pct = total_dist["A"] / total_q * 100 if total_q else 0
    if over50: print(f"[FAIL] no lesson >50% A: {len(over50)} offending\n        " + "\n        ".join(over50))
    else: print("[PASS] no lesson >50% A")
    if a_pct <= 35.0: print("[PASS] global A ≤ 35%")
    else: print(f"[FAIL] global A ≤ 35%: current {a_pct:.1f}%")
    if multi_count >= 10: print("[PASS] ≥10 multi-select")
    else: print(f"[FAIL] ≥10 multi-select: current {multi_count}")
    if not hard_hits: print("[PASS] no non-AWS distractor (hard list)")
    else: print(f"[FAIL] no non-AWS distractor: {len(hard_hits)} found (hard list)")

    snap = _snapshot(results)
    snap["hard_hits"] = hard_hits
    snap["soft_hits"] = soft_hits[:20]
    snap["over50_lessons"] = over50
    snap["global_a_pct"] = round(a_pct, 1)

    if before_snap:
        print("\n## Before/After diff")
        b, a = before_snap.get("summary", {}), snap["summary"]
        print(f"  Total Q:   {b.get('total_questions','?')} → {a.get('total_questions','?')}")
        for k in "ABCD":
            bp = b.get("dist_pct", {}).get(k, 0); ap = a.get("dist_pct", {}).get(k, 0)
            print(f"  {k}: {b.get('dist',{}).get(k,0)} ({bp:.1f}%) → {a.get('dist',{}).get(k,0)} ({ap:.1f}%)")
        print(f"  ALL_A lessons: {b.get('all_a_lessons','?')} → {a.get('all_a_lessons','?')}")
        print(f"  Multi-select:  {before_snap.get('multi_count','?')} → {snap['multi_count']}")

    return snap


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--before", metavar="FILE", help="Load snapshot and diff")
    ap.add_argument("--after", metavar="FILE", help="Save snapshot to FILE")
    args = ap.parse_args()
    results = scan_lessons(str(LESSONS_DIR))
    allowlist = _build_allowlist()
    before_snap = json.load(open(args.before)) if args.before else None
    snap = _print_report(results, allowlist, before_snap)
    if args.after:
        json.dump(snap, open(args.after, "w"), indent=2)
    failures = bool(snap["hard_hits"] or snap["over50_lessons"] or snap["multi_count"] < 10 or snap["global_a_pct"] > 35)
    sys.exit(1 if failures else 0)


if __name__ == "__main__": main()
