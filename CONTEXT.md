# Domain Context

## Glossary

### Concept Packet
A curated, ready concept record selected once for a Study Session before Rex runs. It carries the grounding facts, exam traps, expected answer criteria, and allowed review resources used by Rex, the Evaluator, Sage, and rechallenge. It corresponds to exactly one concept. If an unfinished Study Session is resumed, it keeps the same Concept Packet.

### Study Session
One complete Rex→Sage study run for a learner within a single domain, topic, and concept. It may exist before the first Exchange is recorded. Retrying the same concept later creates a new Study Session rather than reopening a completed one. A learner may also leave a Study Session unfinished without ending its identity.

### Open Study Session
A Study Session that exists but has not yet completed its intended Exchanges. This is internal language rather than a learner-visible term. Abandonment leaves the Study Session Open until cleanup or explicit resume. Only one Open Study Session may exist for the same learner and concept. An Open Study Session remains bound to its original exam and curriculum context.

### Completed Study Session
A Study Session that has completed its intended Exchanges. It does not become Open again; later work creates a new Study Session. This is internal language rather than a learner-visible term.

### Exchange
One learner answer and the immediate evaluation/Sage outcome for it. It is the smallest complete unit of assessed interaction and contains the Learner Response, Evaluation Verdict, and Sage Reply.

### Aborted Exchange
An assessed interaction where the Evaluation Verdict exists but the Sage Reply does not complete, so it is not a full Exchange. The Study Session may continue, but the learner must submit a fresh Learner Response rather than resume the aborted interaction. An Aborted Exchange does not consume a cycle limit, and a Study Session may contain more than one Aborted Exchange. Aborted Exchanges stay internal rather than appearing in learner-visible history, and they do not affect readiness or progress metrics.

### Learner Response
The learner’s answer before evaluation.

### Sage Reply
The system’s response after evaluation.

### Sage Feedback
The learner’s report on a Sage Reply. It belongs to the Exchange that produced that Sage Reply.

### Review Status
The system’s handling state for an Exchange. It may exist even when no Sage Feedback has been submitted, and one Sage Feedback report may cause multiple Review Status transitions over time.

### Evaluation Verdict
The evaluator’s decision on a Learner Response.

### Session Ledger
The canonical record of a Study Session, including its full Exchanges and internal Aborted Exchanges, exchange-level review status, feedback effects, aggregate updates, and read projections for restore/history. Any session-level review view is derived from its Exchanges.

### Session Deletion
A permanent removal of one completed Study Session and its related Exchanges from history. In-progress Study Sessions are not eligible.

### Session Submit Stream
The typed event stream produced for one Learner Response while it moves through evaluation and Sage response: token, evaluation, citations, done, and error events.

### Onboarding Run/Feed
The onboarding build lifecycle for a learner: start, restore, live agent-feed events, stale-feed recovery, and plan-reveal handoff.
