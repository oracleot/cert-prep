# Domain Context

## Glossary

### Concept Packet
A curated, ready concept record selected by app code before Rex runs. It carries the grounding facts, exam traps, expected answer criteria, and allowed review resources used by Rex, the Evaluator, Sage, and rechallenge.

### Study Session
One complete Rex→Sage study run for a learner.

### Exchange
One learner answer and the immediate evaluation/Sage outcome for it.

### Learner Response
The learner’s answer before evaluation.

### Session Ledger
The canonical record of a Study Session and its Exchanges, including active/excluded review status, feedback effects, aggregate updates, and read projections for restore/history.

### Session Deletion
A permanent removal of one study Session and its related Exchanges from history.

### Session Submit Stream
The typed event stream produced while a submitted answer moves through evaluation and Sage response: token, evaluation, citations, done, and error events.

### Onboarding Run/Feed
The onboarding build lifecycle for a learner: start, restore, live agent-feed events, stale-feed recovery, and plan-reveal handoff.
