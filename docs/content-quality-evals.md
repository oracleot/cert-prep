# Content Quality Evaluation Harness

Issue: `7.7`

## Command

Run from the agents directory:

```bash
python -m evals.content_quality --exam-id dva-c02
```

Default mode is `mock`, which exercises artifact coverage, prompt construction, JSON-shape checks, citation availability, duplicate detection, and leakage checks without calling OpenRouter.

For a live Rex generation audit, export `OPENROUTER_API_KEY` in the shell and run:

```bash
python -m evals.content_quality --exam-id dva-c02 --mode live
```

Use `--max-topics 5` for a quick partial smoke run. Full runs omit `--max-topics` and sample every topic in the selected artifact.

## Output Path

Reports are written under `agents/reports/evals/` as paired `.json` and `.md` files. That directory is ignored by Git because reports may contain generated LLM content and local audit notes.

## Automated Pass/Fail Criteria

- Artifact shape has no validation errors.
- Every generated challenge has `domain`, `topic`, `scenario`, and `question` string fields.
- Full runs cover every topic in the selected exam artifact; partial runs state `Scope: partial`.
- Duplicate challenge rate is below 10%.
- Every sampled topic resolves at least one official `https://docs.aws.amazon.com/` citation through Sage grounding.
- Non-DVA exam samples contain no obvious `DVA-C02` / Developer Associate leakage.

## Human Review Rubric

Score each sampled challenge and Sage response 1-5.

| Dimension | 1 | 3 | 5 |
|---|---|---|---|
| Challenge realism | Toy or implausible | Plausible but generic | Operationally specific and exam-like |
| Exam relevance | Off-blueprint | Related but shallow | Directly tests the target domain/topic |
| Source grounding | No official source trail | Source exists but weakly connected | Claim maps clearly to AWS docs/guide |
| Sage correctness | Factually wrong | Mostly right with gaps | Correct, precise, and cites official docs |
| Difficulty fit | Mismatched | Close | Matches requested difficulty |

Manual pass bar: average score >= 4.0 and no Sage correctness score below 3.
