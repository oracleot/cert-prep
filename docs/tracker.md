# Build-Ready Tracker

## Project
- **Name:** AI Certification Prep App (working name: Gauntlet)
- **Type:** greenfield
- **Started:** 2026-06-15
- **Last updated:** 2026-06-16
- **Phase 6 closed 2026-06-16** — all dogfood-driven UX refinements shipped; 2-cycle default kept (ADR-0001).

## Sessions
| # | Session | Status | Output Doc | Last Updated |
|---|---------|--------|------------|--------------|
| 1 | Vision & Feasibility | 🔄 In Progress | docs/product-spec.md | 2026-06-15 |
| 2 | UX & User Flows | ✅ Complete | docs/ux-flows.md | 2026-06-15 |
| 2.5 | Design System *(optional)* | ⏭ Skipped | DESIGN.md | — |
| 3 | System Design | 🔄 In Progress | docs/system-design.md | 2026-06-15 |
| 4 | Tech Stack | ✅ Complete | docs/tech-stack.md | 2026-06-15 |
| 5 | Security & Compliance | ⏭ Skipped | docs/security-compliance.md | post-MVP |
| 6 | Task Breakdown | 🔄 In Progress | docs/task-breakdown.md | 2026-06-15 |
| 7 | Implementation Backlog | ✅ Complete | docs/implementation-backlog.md | 2026-06-15 |
| P1 | Phase 1 — Rex+Sage loop | ✅ Complete | issues 1.3–1.9 shipped | 2026-06-15 |
| P2 | Phase 2 — LangGraph + state persistence | 🔄 In Progress | issues 2.1, 2.2, 2.3, 2.4, 2.5, 2.6 shipped; 2.7 remaining | 2026-06-15 |
| P3 | Phase 3 — Onboarding + Curriculum | ✅ Complete | issues 3.1–3.8 shipped locally; E2E verified | 2026-06-16 |
| P6 | Phase 6 — Dogfood-Driven UX Refinements | ✅ Complete | issues 6.1–6.8 shipped locally; dogfood validation done | 2026-06-16 |
| P7 | Phase 7 — Exam Reliability + Grounded Content | 🔄 In Progress | issues 7.1, 7.2, 7.3 shipped locally; 7.4 next | 2026-06-16 |
| P8 | Phase 8 — Testing Infrastructure | ⏳ Planned | test runners for Next.js + agents, smoke tests for highest-value targets, CI wiring | 2026-06-16 |
| 9 | Pilot/Launch Checklist | ⏭ Skipped | docs/pilot/ | post-MVP |

## Key Constraints
<!-- Populated from handoff 2026-06-15 -->
- Phase 1 iron rule: do not build infrastructure before validating the Rex+Sage loop is fun
- V1 is DVA-C02 only — do not generalise Blueprint Scout beyond hardcoded domains until Phase 3
- Rex and Sage are the product — never swap their models without an explicit A/B test showing quality parity
- The user wants to learn LangGraph deeply — do not abstract it away; expose graph structure, state typing, and conditional edges explicitly
- No codebase exists — start from scratch
- Auth (Clerk) added in Phase 4, not before
- Diagnostic challenge, Coach, Gap Tracker, Boss Battles, RAG pipeline all deferred to v1.1
- DATABASE_URL must be set in `.env.local` for Phase 2 (the agents service validates it on startup and the lifespan refuses to boot without it)
- Current MVP is dogfood-ready, not exam-reliability complete: Rex can only cover the topic inventory and scheduler provided by the app.
- No system can guarantee every possible exam question; Phase 7 targets full official exam guide coverage, source-traced topic maps, and broad scenario variation.
- Sage is currently prompt-instructed to cite AWS concepts/docs, but not retrieval-grounded. Treat Sage as useful coaching until Phase 7 citation enforcement ships.
- Multi-cert support remains blocked until official-source blueprint ingestion and DVA-C02 prompt/copy leakage are handled.

## Gaps to Grill (from handoff analysis)
### Session 1 gaps
- Competitors not formally named or analysed
- Pricing deferred — needs a decision before UX (pricing affects feature gating + onboarding)
- Success metrics (3mo / 6mo / 12mo) not defined
- Riskiest assumptions not formalised
- Regulatory / compliance check not performed

### Session 2 gaps
- Edge states (empty, error, success) not defined per screen
- Degraded UX for external integration failures (OpenRouter down, etc.)
- Trust moments not mapped
- Destructive actions not named
- V2 UX deferrals not explicitly listed

### Session 3 gaps
- Failure handling per external dependency not defined
- Formal provider abstraction map not written

### Session 4 gaps
- Local dev setup procedure not documented
- One-way vs two-way door classification not made explicit
- Provider abstraction interfaces not named

### Session 6 gaps
- Hard dependency chain not formalised
- MVP cut line (50% scope cut scenario) not defined
- Definition of done per phase not stated
- Scope traps not explicitly named
- Cross-cutting work (testing, observability, security) not embedded in phases

## Reference Docs
- Handoff: /var/folders/kx/3xrxjz2x0q70mb_8295rm5v40000gn/T/opencode/cert-prep/HANDOFF.md
