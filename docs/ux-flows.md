# UX & User Flows
Status: draft | Date: 2026-06-15

## Platform Strategy
Mobile-primary, desktop-capable. Card UI designed mobile-first from day one. Daily ~20-min habit loop lives on mobile (commute, lunch break). Desktop is first-class for Phase 1 prototype. Ship as PWA in Phase 5.

## Information Architecture

**Navigation (post-onboarding):**
- Bottom nav (mobile) / sidebar (desktop): **Dashboard · Session · Progress**
- Agent feed: onboarding overlay only — not a nav destination
- Onboarding: one-time flow, not in nav
- Session screen: full-focus mode when active — nav hidden, no escape routes mid-session

## Onboarding Flow

1. **Welcome screen** — one-line product description, "Get started" CTA
2. **Exam input** — "What exam are you preparing for?" Text field, DVA-C02 autocomplete for MVP
3. **Learning style** — single select from 3 options:
   - *Throw me in the deep end* — Rex starts hard, Sage is brief and direct
   - *Challenge and explain* *(default)* — Rex starts medium, Sage is thorough with analogies
   - *Guide me through it* — Rex starts easy, Sage is detailed and patient
4. **Agent feed** — live status overlay while background agents build curriculum. Non-skippable (~10–30s). Shows Blueprint Scout → Curriculum Builder progress.
5. **Plan reveal** — exam name, 4 domains with weightings, "Let's go" CTA
6. **Dashboard** — curriculum ready, "Start your first session" prominent CTA

## Core User Loop

Daily re-entry pattern:
- Dashboard shows **"Continue"** as primary CTA — picks up current domain from curriculum
- One tap → session screen → session begins immediately
- No domain selection — curriculum decides, Rex delivers
- Coach open recap: yesterday's performance, today's domain + topic, time estimate

## Key User Journeys

### Session loop (daily, ~20 mins, 2 cycles)
1. Coach open — recap, today's mission, time estimate
2. Rex throws scenario-based challenge (card UI, domain + topic tag visible)
3. User submits answer
4. Conditional routing:
   - Correct → Sage adds depth (animates in below card)
   - Incorrect → Sage explains the gap (animates in below card)
5. Rex rechallenges — same domain, harder variant
6. Repeat × 2 cycles
7. Coach close — performance summary, Readiness Score updated, domain progress delta

**Wow moment:** End of first Rex→Sage exchange. Sage's explanation quality is the product — confident, specific, no hedging, cites the relevant AWS concept directly. Animates in below the challenge card with distinct visual treatment from Rex. No interruption before rechallenge.

### Session screen behaviour
- Full-focus mode: nav hidden on entry
- Each challenge is a focused card
- Sage response animates in below the challenge card
- Distraction-free — no notifications, no nav, no escape routes mid-session

## Edge States

### Empty states (per screen)
| Screen | Empty state |
|--------|-------------|
| Dashboard (first visit) | Readiness Score shows 0% with ghost/projected overlay. Rex's record shows 0–0. "Start your first session" is the only CTA. |
| Session screen | Never truly empty — Rex always has a challenge ready. If curriculum hasn't built yet, show loading state with agent feed. |
| Progress map | All domains shown at 0% with lock icons — conveys full terrain before any progress. |
| Agent feed | Only visible during onboarding background processing — never shown empty. |

### Error states
| Error | What user sees | What user can do |
|-------|---------------|-----------------|
| OpenRouter fails mid-session | Inline card error: "Rex is having trouble — tap to retry." Auto-retry ×1, then manual retry button. | Retry. Session state preserved — no progress lost. |
| OpenRouter fails at session start | "Something's off on our end — try again in a moment." Retry CTA. | Retry. Dashboard still accessible. |
| Postgres write fails | Silent retry ×3, then: "We couldn't save your progress — your session will continue but may not be recorded." | Continue session in-memory. |
| BullMQ job fails during onboarding | Agent feed shows failure with "Retry" option. | Re-trigger curriculum build. |
| Clerk unavailable (Phase 4+) | "Sign-in is temporarily unavailable." | Nothing — auth gates everything. No partial authenticated states. |

**Rule:** Never show a generic "Something went wrong." Name what happened and what the user can do.

### Success states
| Action | Success state |
|--------|--------------|
| Correct Rex challenge | Subtle green card treatment, Rex's record ticks up. No confetti. Sage still animates in (adds depth). |
| Completing a session | Coach close screen: X/Y correct, domain progress delta, Readiness Score updated. Calm debrief, not celebration. |
| Completing a domain | "Domain complete" card with Boss Battle unlock teaser (Phase 5). Slightly more prominent but not over the top. |
| Onboarding complete | Plan reveal screen is the success state. No separate celebration. |

## External Integration Degradation
| Integration | Failure | User sees | Still works |
|------------|---------|-----------|------------|
| OpenRouter mid-session | LLM timeout/failure | Inline retry on card | Everything except current card |
| OpenRouter at session start | Can't generate challenge | "Try again in a moment" + retry CTA | Dashboard, Progress map |
| Postgres/checkpointer | DB write failure | Silent retry, then warning if unresolved | Session continues in-memory |
| BullMQ during onboarding | Job failure | Agent feed failure + Retry option | Onboarding re-triggerable |
| Clerk (Phase 4+) | Auth unavailable | Graceful block | Nothing |

## Trust Moments
| Moment | What user must believe | How the product earns it |
|--------|----------------------|-------------------------|
| First Rex challenge | "This is relevant to the real exam" | Challenge card shows domain + topic tag (e.g. "DVA-C02 · Deployment") |
| Sage explanation after wrong answer | "This is accurate — I can trust it for the exam" | Sage is confident, specific, never hedges, cites relevant AWS service/concept directly |
| Exam Readiness Score | "This number means something" | Score formula is visible — weighted by official domain weights shown in UI, not a black box |
| Sage explanation | "This is grounded, not invented" | Sage cites only resources attached to the selected concept; if no real URL exists, it shows no link instead of inventing one. |

### Review next block
After Sage's explanation, show a compact `Review next` block with 1–3 resources.

- Official AWS docs links are allowed when present in the curated concept record.
- Skill Builder lessons without URLs appear as source references, not clickable links.
- Missed concepts prioritize docs; hands-on gaps prioritize labs or SimuLearn when available.

## Destructive Actions
| Action | Risk | Prevention |
|--------|------|-----------|
| Reset exam progress | Permanent loss of session history + score | Buried in settings, confirmation modal with 3s delay before confirm button activates: "This will permanently delete your DVA-C02 progress. This cannot be undone." |
| Abandon session mid-way | Incomplete session recorded | No confirmation — LangGraph checkpointer saves state, incomplete sessions don't hurt score |
| Change learning style post-onboarding | Curriculum rebuild | Warn: "Changing this will rebuild your curriculum. Your progress history is kept." Not blocked — just informed. |

## V2 UX Deferrals
- Coach agent (replaced with static summary screen in MVP)
- Boss Battle UI (Phase 5)
- Difficulty progression indicator (Rex upgrades silently in MVP)
- Streak display (Phase 5)
- Rex's record on session screen (dashboard only in MVP)
- Diagnostic challenge during onboarding (v1.1)
