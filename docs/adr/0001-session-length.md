# ADR-0001: Session length — stay at 2 cycles for MVP

Status: Accepted
Date: 2026-06-16
Context: Phase 6 issue 6.8

## Decision

Keep session length at **2 cycles** for the V1 MVP. Rename `MAX_CYCLES` to `DEFAULT_CYCLES` to make the intent explicit (it is the default, not a hard ceiling). The value stays hardcoded for now — re-evaluate after at least one week of real dogfood usage (see Open question below).

## Context

`MAX_CYCLES = 2` was set during the Phase 1 prototype (`app/session/use-session.ts:10`) to keep sessions short. Phase 6 issue 6.8 flagged that 2 cycles is likely too few for real dogfood usage on DVA-C02 — both for engagement (it is over fast) and for Readiness Score signal (a 2-cycle session is noisy: 1 wrong answer = 50% domain performance).

## Options considered

1. **Stay at 2, rename to DEFAULT_CYCLES** — current behaviour, just clearer naming. Lowest scope. Makes future increases a one-line change.
2. **Increase to 3 cycles** — better signal, marginally longer. Still under ~20 min target. Lowest-risk bump.
3. **Increase to 4–5 cycles** — strongest signal, but pushes the session past the documented ~20-min target and risks completion-rate drop in real dogfood.
4. **Make it configurable per-curriculum** — overkill for MVP. No Curriculum metadata exists yet to attach it to. Punt to v1.1.

## Rationale for staying at 2 (option 1)

- **Phase 2/3 focus is on the loop itself, not the metric.** Until we have real users running multiple sessions a day, picking a "right" cycle count is guessing. Two cycles keeps the session tight, completes the Rex→Sage→Rex→Sage→summary arc in one sitting, and lets the user come back for the next domain topic without burning out.
- **2 cycles is enough to test the design.** The Sage animation, the rechallenge, the summary screen, the in-progress resume — all of those are testable in 2 cycles. The signal from increasing to 3+ is incremental.
- **We have no data yet.** No one has run a real session on the real curriculum. Bumping the count before dogfooding is a cargo-cult change. We can do it in a single line later, with data.
- **The `dashboardSummaryRequest` already aggregates `correct_count` / `total_count` across all exchanges.** Signal accumulates across sessions, not within one — so a single noisy 2-cycle session is not a blocker.
- **Lower risk to commit velocity.** A 1-line rename is reversible instantly. A 3-cycle rollout is also 1 line, but it is also a behaviour change we cannot A/B test without traffic.

## Consequences

- `MAX_CYCLES` is renamed to `DEFAULT_CYCLES` in `app/session/use-session.ts`. Same numeric value (2).
- The "Next challenge →" / "View session summary" boundary in `SageCard` is driven off `cycle >= DEFAULT_CYCLES` — no copy change required.
- The hardcoded value is a known debt. Tracking: revisit after first week of dogfood.

## Open question

After at least one week of real dogfood usage (multiple users, multiple sessions per user, real DVA-C02 prep), revisit and decide between:
- (a) stay at 2
- (b) bump to 3 (single-line change to `DEFAULT_CYCLES`)
- (c) make it a per-user preference / curriculum metadata field

The criteria for the revisit:
- Session completion rate (are users finishing the second cycle or dropping off?)
- Time-to-complete for cycle 2 (does it feel rushed, or is energy still high?)
- Readiness Score stability (does the score still feel meaningful at 2 cycles per session?)
- Engagement signal (are users opening the app the next day, or only once?)

## Rollback

`DEFAULT_CYCLES` is the only moving part. Rollback is reverting that single line.
