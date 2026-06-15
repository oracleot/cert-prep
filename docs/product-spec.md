# Product Spec
<!-- IN PROGRESS — gaps: competitors, pricing, success metrics, riskiest assumptions, regulatory check -->
Status: draft | Date: 2026-06-15

## One-liner
An AI-powered certification prep app that replaces passive reading with scenario-based challenges and AI tutoring — for working professionals prepping for tech certifications.

## Target User
- **Primary:** Working professionals and experienced developers preparing for a specific tech certification
- **Secondary:** Students with hands-on development experience
- **Qualifier:** Baseline technical knowledge assumed — no hand-holding on fundamentals
- **Persona:** Time-poor, competitive, motivated by a concrete goal (passing the exam), allergic to boring courses
- **Who does NOT qualify:** Beginners learning fundamentals, people who prefer text-heavy study methods, non-technical professionals

## Problem
- **Status quo:** Passive study materials — documentation, video courses, practice tests — are reading/watching-heavy and difficult to sustain for busy developers
- **Pain:** Time-poor professionals fail to study consistently because the format doesn't engage them; they want to pass the exam but find the prep process tedious
- **What changes with this:** Challenge-first, scenario-based learning that mirrors how experienced devs actually learn — struggle with a real problem first, then receive targeted explanation

## Core Promise
Replace passive reading with an engaging challenge loop that is fun enough to open daily and effective enough to measurably increase exam readiness.

## V1 Scope
### In scope
- Onboarding Agent (exam input + learning style selection only)
- Blueprint Scout (hardcoded DVA-C02 domain weights for V1)
- Curriculum Builder
- Rex (challenge generator + evaluator)
- Sage (post-challenge tutor)
- Session loop: Coach open → Rex challenge → evaluate → Sage respond → Rex rechallenge → Coach close
- Progress tracking (domain-level)
- Exam Readiness Score
- Clerk auth (Phase 4)
- Dashboard + Progress map
- Session screen (card UI, full-focus mode)

### Explicit non-goals (V1)
- Diagnostic challenge during onboarding (v1.1)
- Coach agent (replaced with static summary screen in MVP)
- Gap Tracker (replaced with simple rule-based logic)
- Boss Battles (v1.1)
- Resource Gatherer + RAG pipeline (v1.1)
- Difficulty progression — Rex starts at medium for V1
- Score decay / spaced repetition model (v1.1)
- Native mobile apps (post-validation)
- Multi-exam support beyond DVA-C02 (Phase 3+)

## Competitor Landscape
<!-- GAP: Not formally analysed in prior session — needs grilling -->
*To be completed in Session 1 gap-fill.*

## Business Model
<!-- GAP: Deferred in prior session — recommendation exists but not locked -->
**Recommended (not yet locked):** Freemium.
- Free tier: first domain of any exam
- Paid: full curriculum, all agents, analytics
- Price point: ~$20–30/month
- Revisit post-validation

*Needs a decision before UX is locked — pricing affects feature gating and onboarding flow.*

## Rollout Strategy
| Phase | Scope |
|-------|-------|
| Phase 1 | Rex + Sage loop prototype — single page, hardcoded DVA-C02 topic, no auth/DB |
| Phase 2 | LangGraph + Postgres — state persists, still hardcoded user |
| Phase 3 | Onboarding + Blueprint Scout + Curriculum Builder |
| Phase 4 | Clerk auth, Dashboard, Progress map, Readiness Score |
| Phase 5 | PWA, mobile polish, Rex's record, streaks, Boss Battles, dogfood for DVA-C02 |

## Success Metrics
<!-- GAP: Not defined in prior session — needs grilling -->
*To be completed in Session 1 gap-fill.*

## Riskiest Assumptions
<!-- GAP: Not formalised in prior session — needs grilling -->
*To be completed in Session 1 gap-fill.*

## Regulatory / Compliance Constraints
<!-- GAP: Not addressed in prior session — needs a check -->
*To be completed in Session 1 gap-fill.*
