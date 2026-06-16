# Exam Reliability Readiness Rubric (Issue 7.1)

Status: Draft for sign-off
Owner: TBD
Last updated: 2026-06-16
Related: `docs/implementation-backlog.md` Phase 7; `docs/tracker.md` P7

## What this document is

The minimum bar for calling Gauntlet "exam-prep reliable" rather than "MVP dogfood-ready." A failed rubric item blocks declaring Phase 7 complete, even when the UI works. A passed rubric item means a real human could prep for the supported exam with this app and not hit an obvious gap.

This is not a coverage promise. No system can guarantee every possible exam question. The rubric targets the official exam guide: full domain coverage, source-traced topic maps, grounded Sage explanations, and a second-cert smoke path that does not leak DVA-C02.

## Decision: "official source" semantics

**Chosen approach: curated allowlist of hand-authored blueprint JSONs under version control.**

The "official AWS source" referenced in 7.3 is implemented as:

- A small set of `agents/data/exam_artifacts/<exam_id>.json` files, one per supported exam, hand-authored from the official exam guide.
- A new `exam_artifacts` Postgres table (lands in 7.2) whose rows are seeded from those JSONs on service boot. Source URL, captured_at timestamp, and content checksum are stored alongside the JSON so drift can be detected.
- A new `validate_exam_id` function (lands in 7.2) that replaces the hardcoded DVA-C02 check in `agents/blueprint.py:24-28` and returns `accepted: False` for any code not in the allowlist — never silently coerced to DVA-C02.

Rejected alternatives:

- **Live scrape of `aws.training` / `aws.amazon.com/certification/` pages.** High variance in page structure, brittle to AWS marketing-site changes, and not strictly necessary — the exam guide is a stable, well-versioned document. Defer until/unless AWS ships blueprint updates faster than the hand-authored artifacts can be refreshed (quarterly check is the fallback).
- **Embeddings + vector store over AWS docs.** Explicitly v1.1 deferred in `docs/tracker.md`. Would also lock the V1 cost profile to an embedding API.
- **LLM-only blueprint extraction.** Hallucination risk on a load-bearing input.

## Supported exam allowlist (initial)

Both entries are sourced from the official AWS exam guide pages linked below. The user will verify each URL before 7.4 data work begins.

| Exam code | Display name | Status | Exam guide URL | Marketing page |
|---|---|---|---|---|
| `dva-c02` | AWS Certified Developer - Associate (DVA-C02) | Primary | https://docs.aws.amazon.com/aws-certification/latest/developer-associate-02/developer-associate-02.html | https://aws.amazon.com/certification/certified-developer-associate/ |
| `saa-c03` | AWS Certified Solutions Architect - Associate (SAA-C03) | Smoke (lands in 7.8) | https://docs.aws.amazon.com/aws-certification/latest/solutions-architect-associate-03/solutions-architect-associate-03.html | https://aws.amazon.com/certification/certified-solutions-architect-associate/ |

Per-domain sub-pages (used as source IDs in 7.4's topic map):

- DVA-C02: `/developer-associate-02-domain{1..4}.md`, `dva-02-in-scope-services.md`, `dva-02-out-of-scope-services.md`, `dva-technologies-concepts.md`, `dva-service-mentions.md`, `dva-02-revisions.md`
- SAA-C03: `/solutions-architect-associate-03-domain{1..4}.md`, `saa-03-in-scope-services.md`, `saa-03-out-of-scope-services.md`, `saa-technologies-concepts.md`, `saa-service-mentions.md`

Cross-cutting AWS references (used by 7.6 for Sage citations):

- AWS service short / long names: https://aws.amazon.com/certification/policies/general-information/#AWS_Service_Names
- Per-service docs root (used for per-topic citation URLs): `https://docs.aws.amazon.com/<service>/latest/<guide>/<page>.html` (per-topic paths get authored into the curated snippet bundles in 7.6)
- AWS "What's New" / service changelogs are out of scope for V1 citations; Sage should not cite changelog posts as authoritative reference material.

## The rubric

Each item is binary: pass or fail. Partial credit does not pass. The status column tracks where this stands today (2026-06-16).

### R1 — Blueprint completeness

- [ ] R1.1 Every supported exam has a versioned artifact row in `exam_artifacts` with non-null `source_url`, `captured_at`, and `content_checksum`.
- [ ] R1.2 Every artifact's domain weights match the official exam guide exactly (sum to 100, integer percentages, ordered as in the guide).
- [ ] R1.3 Every artifact's task statements are present in the artifact JSON (the per-domain markdown files linked above are the source of truth).
- [ ] R1.4 The full topic inventory for each artifact covers every task statement with at least one topic; topic names align with AWS service names from the official short-name list.
- [ ] R1.5 `validate_exam_id(exam_id)` returns `accepted: True` for every supported code and `accepted: False` (with a clear message) for everything else. No silent coercion.

**Current status (2026-06-16): PARTIAL.** DVA-C02 now uses the artifact-backed official weights and full 101-topic skill inventory from the four official domain pages. R1 remains open until every supported exam, including the SAA-C03 smoke artifact, has the same complete artifact coverage.

### R2 — Topic coverage

- [x] R2.1 `curriculum_repository.choose_today_target` uses the artifact-driven topic map (not the hardcoded 4×4 grid).
- [x] R2.2 Curriculum Builder prompt preserves full topic coverage while still sequencing per learning style.
- [x] R2.3 `dashboard_summary` and `progress_map` expose per-topic coverage, not just per-domain totals.
- [x] R2.4 Coverage matrix (R1.4) renders for the user — every topic has a "covered / in progress / untouched" status visible from the dashboard or progress screen.

**Current status: PASS for DVA-C02.** DVA-C02 now has a full topic inventory, `choose_today_target` uses topic-level coverage/correctness with domain weights, and dashboard/progress views expose per-topic coverage.

### R3 — Question quality (Rex)

- [ ] R3.1 Generated challenges for every (domain, topic) pair in every supported exam pass JSON shape validation (lands in 8.4).
- [ ] R3.2 Duplicate rate across 100 generations per domain stays below 10% (harness in 7.7 measures this).
- [ ] R3.3 Generated challenges reference specific AWS services from the in-scope services list, not generic cloud terms.
- [ ] R3.4 Difficulty is honored (easy/medium/hard produces visibly different scenarios — manual rubric).
- [ ] R3.5 Challenges for non-DVA exams show no DVA-C02 domain/topic leakage (harness in 7.7 asserts this).

**Current status: NOT MEASURED.** Eval harness now exists; append a live run before sign-off.

### R4 — Answer evaluation quality

- [ ] R4.1 Evaluator distinguishes correct / incorrect with >= 85% agreement against a hand-labeled set of 30 (domain, topic, answer) triples (harness in 7.7).
- [ ] R4.2 Evaluator never marks a clearly-correct answer wrong because of formatting or trivial wording differences.
- [ ] R4.3 Evaluator's `reasoning` field is specific enough that Sage can use it directly (no re-evaluation needed).
- [ ] R4.4 Multiple-response exam questions (per official guide: 2+ correct out of 5+) are at least supported in the prompt, even if the UI is single-select for MVP.

**Current status: NOT MEASURED.** Eval harness now exists; append a live run before sign-off.

### R5 — Sage citation quality (7.6)

- [x] R5.1 For every topic in the artifact, Sage can build a source bundle from `source_ids`, optional `agents/data/sage_snippets/<exam_id>/<topic>.md` overrides, and the curated AWS service-doc catalog.
- [x] R5.2 Sage's prompt receives the relevant source bundle for the active (domain, topic) before generation.
- [ ] R5.3 In a 50-sample audit, >= 80% of substantive Sage responses cite at least one official AWS source (URL present in `exchanges.citations` JSONB column added in 7.2).
- [x] R5.4 When no acceptable source is available, Sage produces a clearly-labelled "unverified" marker instead of inventing a citation. Manual rubric on a curated set of intentionally-unsourceable prompts.
- [x] R5.5 Citations render as clickable links in the Sage card without breaking streaming readability (lands in 7.6 alongside the markdown renderer added in 6.5).
- [x] R5.6 Citations in the stored exchange are auditable: `exchanges.citations` is a JSONB array of `{ url, title, snippet_id }` objects.

**Current status: PARTIAL.** Runtime grounding now passes source bundles into Sage, streams citation metadata to the UI, and stores auditable citations on exchanges. R5.3 remains open until the 7.7 evaluation harness runs the 50-sample citation audit.

### R6 — Unsupported cert behavior

- [ ] R6.1 Onboarding `validate_exam_id` rejects unsupported codes with a clear message and no fake curriculum.
- [ ] R6.2 ExamStep autocomplete (`components/onboarding/exam-step.tsx:34-37`) lists exactly the supported codes — pulled from the artifact store, not hardcoded.
- [ ] R6.3 No prompt, event message, default topic, or domain weight is hardcoded to DVA-C02 in any code path the second-cert smoke (7.8) would exercise.
- [ ] R6.4 Second-cert smoke: a full happy path (onboarding → feed → curriculum → first session) completes for SAA-C03 with no DVA-C02 text appearing anywhere user-visible.

**Current status: FAIL.** `agents/blueprint.py:5-7` hardcodes `EXAM_ID = "dva-c02"`. `agents/prompts/curriculum_builder.py:8` says "DVA-C02" in the system prompt. `agents/routes/onboarding.py:18-21` has hardcoded "DVA-C02 only" event messages. `agents/routes/jobs.py:39-41` has a hardcoded "Deployment 32%..." event message.

### R7 — Manual QA (the human bar)

- [ ] R7.1 At least 20 DVA-C02 sessions have been run by a real human (not the eval harness) across all 4 official domains.
- [ ] R7.2 At least 5 SAA-C03 sessions have been run by a real human across all 4 official domains.
- [ ] R7.3 For every session, the runner recorded: time-to-complete, perceived challenge realism (1-5), perceived Sage helpfulness (1-5), perceived citation accuracy (1-5), any factual errors spotted.
- [ ] R7.4 No factual error spotted in any session is left unaddressed at sign-off.
- [ ] R7.5 The eval harness output (7.7) is appended to this rubric's appendix before sign-off.

**Current status: NOT STARTED.** Begins after 7.4 / 7.6 ship.

## Sign-off criteria

Phase 7 is "done" when:

1. R1 through R6 are all PASS for `dva-c02`.
2. R6.4 (second-cert smoke) is PASS for `saa-c03`.
3. R7.1, R7.2, R7.3, R7.4 are PASS.
4. R3.1, R3.2, R4.1, R5.3 have a recorded eval-harness run (7.7) appended to the appendix below.

The user verifies R1, R5.1, R6.2 by clicking the URLs in the "Supported exam allowlist" table above and confirming the page is the real exam guide, the marketing page, or the official AWS docs page.

## Appendix (filled in at sign-off)

### A.1 — Eval harness run, DVA-C02

Pending live run from `python -m evals.content_quality --exam-id dva-c02 --mode live`.

### A.2 — Eval harness run, SAA-C03

Pending after the SAA-C03 smoke artifact ships in 7.8.

### A.3 — Manual QA session log

TBD — appended when R7 is run.

## Open questions for the user to verify

1. The two exam guide URLs in the "Supported exam allowlist" table — both fetched 2026-06-16 and showed the expected exam names + domain lists. Confirm the URLs are what you want pinned in the allowlist.
2. The per-domain sub-page pattern (e.g., `developer-associate-02-domain1.md`) — used as source IDs in the artifact JSON. Confirm the AWS-hosted markdown URL pattern is stable enough to treat as a versioned source.
3. The "unverified" marker behavior in R5.4 — proposed wording is something like `_(Source unverified — I couldn't find a definitive AWS reference for this specific claim.)_` rendered distinctly from a normal citation. Acceptable, or do you want a different shape?
4. The SAA-C03 pick for the smoke cert — it's the natural choice (Associate-level, popular, blueprint structure is different enough from DVA-C02 to expose leakage). Confirm or name a different cert.
