# Option-Based Session Spec

Status: accepted for implementation
Date: 2026-07-01

## Goal
Replace free-text session answers with exam-style answer selection while preserving Sage as the differentiator.

## Why
- DVA-C02 uses both multiple-choice and multiple-response items.
- The app should feel closer to the real exam.
- Sage remains the product edge by explaining the correct option(s) deeply and distractors briefly.

## Core decisions
- Sessions use option-based prompts, not free-text answers.
- Support both:
  - **Single-response**: exactly 1 correct option
  - **Multiple-response**: exact-match scoring, no partial credit
- Each prompt always has **4 options** labeled **A/B/C/D**.
- Option order may be shuffled per prompt.
- No `all of the above` or `none of the above`.
- Multiple-response uses **at most 2 correct options** in V1.
- Prompt mode is shown on the prompt itself:
  - `Select ONE`
  - `Select TWO`
- Mode can vary inside the same session.
- App controls mode distribution, targeting an approximate **60/40 single-to-multiple** mix across many sessions.

## Prompt contract
Each Rex prompt must include:
- scenario
- question
- response mode
- 4 labeled options
- answer key label(s)

Distractor rules:
- each distractor must be plausible
- each distractor must be wrong for a distinct reason
- narrow concepts still require 4 options

Rechallenge rules:
- stays on the same concept
- keeps 4 options
- may be single-response or multiple-response
- difficulty rises through nuance, not format changes alone

## Learner response
- Selection-only; no free-text justification
- At least 1 option must be selected before submit
- Multi-response may be submitted with only 1 selected option and be marked incorrect
- Learner may change selections before submit without penalty
- Response locks after submit

## Evaluation
- Verdict remains binary: `correct` or `incorrect`
- Multiple-response is correct only when the learner selects the exact full answer key
- Verdict payload should immediately expose:
  - chosen labels
  - correct labels
- UI should immediately mark:
  - correct options
  - missed correct options
  - incorrectly chosen options

## Sage behavior
- Prompt stays visible while Sage streams
- Learner cannot proceed until Sage finishes
- Sage explains correct option(s) first and in more depth
- Sage explains distractors briefly
- Sage refers to options by label plus short paraphrase, not full repetition
- On multi-response misses, Sage explicitly names:
  - missed correct options
  - incorrectly chosen options

## History and failure semantics
- Review state and Sage feedback remain exchange-level, not option-level
- If verdict never arrives, no Aborted Exchange exists
- If verdict arrives but Sage fails to finish, record an Aborted Exchange and recreate the same pending prompt
- Aborted Exchanges remain internal and do not affect readiness/progress metrics

## Non-goals for V1
- free-text rationale grading
- partial credit
- option-level review workflows
- variable option counts
- 3+ correct answers in one prompt
