# Task Breakdown
<!-- IN PROGRESS — gaps: hard dependency chain, MVP cut line, definition of done per phase, scope traps, cross-cutting work -->
Status: draft | Date: 2026-06-15

## Build Order Proof Points
The sequential user-visible outcomes that prove the build is progressing:

1. **You can have a Rex+Sage challenge exchange and it feels engaging** (Phase 1 done)
2. **Your session survives a browser refresh — state is persisted** (Phase 2 done)
3. **A new user can pick their exam and get a personalised curriculum** (Phase 3 done)
4. **You can log in and your progress is yours across devices** (Phase 4 done)
5. **You can use this app daily to actually prep for DVA-C02** (Phase 5 done)

## Milestones

| Milestone | Phase | User-Visible Outcome |
|-----------|-------|---------------------|
| M1 | Phase 1 | Complete a Rex+Sage challenge exchange on a DVA-C02 topic |
| M2 | Phase 2 | Session state persists; resume a session after page reload |
| M3 | Phase 3 | Onboarding complete: input exam, get a personalised curriculum |
| M4 | Phase 4 | Authenticated user with persistent progress across sessions |
| M5 | Phase 5 | Full daily study loop with Rex's record, streaks, and PWA install |

## Phase Details

### Phase 1: Rex + Sage Loop (Weeks 1–2)
**Iron rule:** Do not build infrastructure before validating the loop is fun. The only question Phase 1 answers is: does Rex + Sage create a moment where you think "this is actually good"?

**Done when:** You can complete a full Rex→Sage→Rex exchange on a hardcoded DVA-C02 topic and the experience feels engaging.

**Epics:**
- Rex challenge generation (raw OpenRouter call)
- User answer submission (card UI)
- Answer evaluation (LLM judge)
- Sage response (depth or explain, conditional)
- Rex rechallenge
- Basic session screen (Next.js, no auth, no DB)

**Key stories:**
- Rex generates a scenario-based challenge for a hardcoded DVA-C02 topic
- User types an answer and submits
- System evaluates correctness and routes to Sage depth vs explain
- Sage response streams in below the challenge card
- Rex generates a harder rechallenge on the same domain
- Session runs 2 full cycles before showing a summary

### Phase 2: LangGraph + State Persistence (Weeks 3–4)
**Done when:** Session state is stored in Postgres via LangGraph checkpointer; reloading the page does not lose progress.

**Epics:**
- Port SessionSubgraph into LangGraph
- Postgres + LangGraph checkpointer setup (Railway)
- BullMQ + Redis setup (for future background jobs)
- Hardcoded user_id (no auth yet)

**Key stories:**
- SessionSubgraph executes the same Rex+Sage loop but via LangGraph nodes
- State is checkpointed to Postgres at each node completion
- Exchange records written to Postgres on completion
- Background infrastructure (BullMQ + Redis) deployed on Railway

### Phase 3: Onboarding + Curriculum (Weeks 5–6)
**Done when:** A new user can input an exam name, select a learning style, watch background agents build their curriculum, and land on a dashboard ready for their first session.

**Epics:**
- Onboarding Agent (exam input + learning style)
- Blueprint Scout (hardcoded DVA-C02 domain weights)
- Curriculum Builder (LangGraph subgraph)
- BullMQ job dispatch for background agents
- Agent feed UI (live SSE status display)
- Dashboard (basic)

**Key stories:**
- User enters "AWS DVA-C02" and selects a learning style
- Blueprint Scout loads hardcoded domain weights
- Curriculum Builder generates personalised study plan
- Agent feed shows live status while jobs run
- Dashboard shows curriculum on completion

### Phase 4: Auth + Progress (Weeks 7–8)
**Done when:** A user can create an account, log in, and see their progress and Exam Readiness Score maintained across devices.

**Epics:**
- Clerk auth integration
- User table + user_id wired through all LangGraph state
- Dashboard: Readiness Score (prominent), Rex's record, domain overview
- Progress map: domain breakdown, % complete
- Exam Readiness Score formula implemented

**Key stories:**
- User signs up with Clerk, session is tied to real user_id
- Exam Readiness Score calculated from domain performance
- Dashboard renders score, streak, and today's mission
- Progress map shows domain completion status
- All previous session data attached to authenticated user

### Phase 5: Polish + Dogfood (Weeks 9–10)
**Done when:** You are using this app every day to actually prep for DVA-C02.

**Epics:**
- PWA configuration
- Mobile layout polish
- Rex's record (win/loss rivalry mechanic)
- Streaks
- Boss Battles (10-challenge gauntlet at end of each domain)
- Difficulty progression (Rex upgrades: easy → medium → hard based on rolling accuracy)
- Full dogfood pass

**Key stories:**
- App is installable as a PWA on mobile
- Rex's running record is displayed on dashboard and session screen
- Boss Battle unlocks when a domain reaches completion threshold
- Rex explicitly upgrades difficulty based on performance
- User completes at least one full domain prep for DVA-C02

## Hard Dependency Chain
<!-- GAP: To be formalised in Session 6 gap-fill -->
*Summary from build order:*
- Phase 2 requires Phase 1 (can't port to LangGraph before the loop is validated)
- Phase 3 requires Phase 2 (Curriculum Builder needs LangGraph subgraph infrastructure)
- Phase 4 requires Phase 3 (auth must be wired to a real curriculum/session flow)
- Phase 5 can partially parallel Phase 4 (PWA config is independent; Boss Battles need Phase 4 progress data)

## MVP Cut Line
<!-- GAP: 50% cut scenario not formally defined — needs decision -->
*If scope were cut by 50%, what survives:*
- Rex + Sage session loop (non-negotiable — this is the product)
- Hardcoded DVA-C02 curriculum
- Basic session screen
- Exam Readiness Score
- Auth (Clerk)

*What would be cut:*
- Boss Battles
- Streaks / Rex's record gamification
- Agent feed UI
- Progress map (replace with simple domain list)
- Mobile polish (functional but unpolished)

## Highest Execution Risks
<!-- GAP: To be formalised in Session 6 gap-fill -->

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Rex+Sage loop isn't actually engaging | Invalidates the product — everything built on top is worthless | Phase 1 validates this before any infrastructure is built |
| LangGraph learning curve delays Phase 2 | 1–2 week timeline slip | Acceptable — user explicitly wants to learn it; schedule buffer built in |
| OpenRouter reliability / latency | Degrades session quality | Monitor in Phase 1; add retry + fallback logic in Phase 2 |
| LLM evaluation accuracy (evaluate_answer node) | Wrong outcomes damage trust | Test extensively with DVA-C02 challenges in Phase 1 |

## Scope Traps
<!-- GAP: To be explicitly named in Session 6 gap-fill -->
*Known scope traps:*
- "Let me add a second exam while I'm at it" (Phase 3 generalisation) → blocked until Phase 3 milestone is met
- "The agent feed should be interactive" → read-only status display only in V1
- "I should add a notes feature" → passive note-taking is antithetical to the challenge-first model
- "Let me add a leaderboard" → social features are a v2 concern

## Cross-Cutting Work (every phase)
<!-- GAP: Not embedded in phase details above — needs explicit statement -->
- **Testing:** At minimum, test Rex's LLM evaluation accuracy per phase
- **Observability:** Log session outcomes and LLM costs from Phase 1 onwards
- **Security baseline:** Deferred until Phase 4 (auth) — but no user data exists before then
- **Mobile usability:** Card layout must be tested on mobile viewport from Phase 1

## Definition of Done per Phase
<!-- GAP: Needs explicit user-confirmed criteria -->

| Phase | Definition of Done |
|-------|-------------------|
| Phase 1 | Complete a Rex→Sage→Rex exchange and it feels genuinely engaging. You want to do another. |
| Phase 2 | Reload the page mid-session. Your session is intact. |
| Phase 3 | A fresh user flow: input exam → watch agents build curriculum → land on dashboard. No hardcoded user_id. |
| Phase 4 | Log in on a different device. Your progress, score, and Rex's record are there. |
| Phase 5 | You have installed the PWA and used it for at least one week of DVA-C02 prep. |
