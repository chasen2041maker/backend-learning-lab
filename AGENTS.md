# Backend Learning Lab collaboration rules

This repository is a public, beginner-oriented backend learning knowledge base and experiment lab. It is maintained mainly from learning conversations, code reviews, debugging sessions, and small experiments. The repository must preserve durable understanding, not raw chat transcripts and not an artificial “complete backend encyclopedia.”

## Repository purpose

The primary learning loop is conversation/problem -> explanation -> experiment -> evidence -> durable note.

Do not force the learner to follow a calendar or finish files in numeric order. `LEARNING_ROADMAP.md` is a dependency map, not a deadline schedule. The current active implementation language may be Go or Python. Concepts come first; language examples exist to make the concept executable.

Use directories intentionally:

- `lessons/`: mature explanations with a complete causal chain;
- `notes/learning-journal/`: valuable conclusions from a specific conversation/debugging session;
- `notes/*-cheatsheet.md`: compact recovery material for returning after weeks away;
- `notes/glossary.md`: short term definitions, not mini-lessons;
- `exercises/`: knowledge that should be proven by running or breaking something;
- `projects/`: staged integration work, never a request to generate a full production system at once.

## Explicit repository-update trigger

When the learner says `更新仓库` (or an equivalent explicit request to update this repository), treat it as a maintenance operation, not as permission to dump the current chat verbatim.

Follow this order:

1. inspect the current conversation for genuinely new, durable knowledge;
2. read the relevant existing repository files before writing;
3. if the knowledge is already covered well, do not create duplicate notes just to make a commit;
4. if the new material corrects or completes an existing weak page, improve that page instead of adding another fragment;
5. use `notes/learning-journal/` for a valuable learning trajectory that is still tied to the discussion;
6. create/update an exercise only when executable failure evidence materially improves understanding;
7. fetch the latest remote `main` immediately before committing so concurrent changes are not overwritten;
8. prefer one coherent atomic commit for one maintenance pass;
9. after pushing, verify the branch/compare result and inspect CI/status when available;
10. report honestly when there was nothing worth persisting or when verification could not be completed.

The trigger means “curate and persist what became durable,” not “every sentence must become a Markdown file.”

## Safety

- Never copy employer source code, credentials, internal URLs, customer data, screenshots, logs, private prompts, or proprietary architecture into this public repository.
- Use only fictional names and locally generated/synthetic data.
- Secrets belong in environment variables or a secret manager. Commit `.env.example`, never `.env`.
- Do not paste real access tokens into examples, tests, logs, issues, or learning journals.

## Teaching style

- Start with the problem the abstraction solves, then the mental model, then the failure mode, then syntax/tooling.
- Prefer plain language first; introduce precise terminology immediately after the intuition.
- Explain where an analogy stops being accurate.
- Do not dump a framework solution before the learner understands the underlying HTTP/data/concurrency boundary.
- Keep implementation exercises small enough that the learner can type, run, test, and explain them.
- Do not complete a learner challenge before they have attempted it unless the user explicitly asks for a complete reference implementation.
- Prefer one new production concept per exercise.
- Always distinguish “demo works,” “tests pass,” and “production-ready.”

## Lesson quality bar

A durable lesson should normally contain:

1. what problem this concept solves;
2. the minimum prerequisite mental model;
3. a concrete request/data flow;
4. a small code/SQL/config example when useful;
5. at least two realistic failure modes or common misconceptions;
6. the production boundary: what the toy example does not prove;
7. a runnable or observable exercise/evidence target;
8. several “close the document and explain it” questions;
9. links to the relevant repository exercise instead of duplicating full solutions.

A page that is only a list of terms is a note/outline, not a finished lesson.

## Conversation-to-repository promotion

When a conversation produces durable knowledge:

1. capture the corrected mental model in `notes/learning-journal/` if it is tied to the discussion;
2. remove repeated dialogue, filler, and temporary troubleshooting details;
3. preserve the misconception, why it was wrong, the corrected model, and a failure example;
4. promote it into a lesson only when it is general enough to teach independently;
5. update the glossary/knowledge map only if the new concept materially improves navigation;
6. avoid duplicating the same explanation in three files.

## Language tracks

- Go examples target Go 1.22+ and should prefer the standard library for foundational HTTP/concurrency lessons.
- Python examples target Python 3.11+; FastAPI/Pydantic are appropriate when the lesson is about API/Agent application engineering rather than language fundamentals.
- SQL examples target PostgreSQL semantics unless stated otherwise.
- Redis examples must state whether Redis is being used as cache, coordination state, session state, or message transport.

Do not enforce “Python first, Go later.” When the learner is actively learning Go backend engineering, Go may be the primary implementation track while Python remains useful for comparison and Agent/RAG work.

## Engineering quality

- Python: type hints, explicit validation/errors, deterministic tests, pytest where already used.
- Go: `gofmt`, explicit errors, context propagation for request-scoped cancellation/deadlines, table-driven tests where useful.
- Public APIs use explicit contracts, stable machine-readable error codes, and versioning when compatibility matters.
- Client-provided identity/tenant/role fields are never trusted merely because a UI normally supplies them.
- Any persistence lesson must discuss constraints, indexes from actual queries, transactions, tenancy/ownership, and failure recovery.
- Any retry lesson must discuss idempotency and retry amplification.
- Any async lesson must discuss duplicate delivery, ACK/commit order, recovery, and observability.
- Any distributed-system lesson must first ask whether a single-process or single-database design is sufficient.

## Project scope discipline

The capstone must evolve from the smallest coherent system:

```text
single service + memory
-> single service + PostgreSQL
-> transactions/auth/idempotency
-> Redis/concurrency where justified
-> async Outbox/worker where justified
-> Agent/RAG integration
-> optional service split/gateway/K8s only after the boundaries are understood
```

Do not require multiple languages, microservices, Redis, Kubernetes, or message brokers just to make the architecture look advanced.

## Review standard

When reviewing the repository or a change:

- report only evidence-backed issues;
- identify the file and a concrete misleading/failure scenario;
- prefer the smallest correction that restores the intended learning model;
- do not add abstractions merely to satisfy style preferences;
- preserve good, already-detailed lessons instead of rewriting them for churn;
- after changes, verify links/contracts/tests when the available environment allows it and state any verification limits honestly.
