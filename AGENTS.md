# Backend Learning Lab collaboration rules

This is a public, beginner-oriented learning repository.

## Safety

- Never copy employer source code, credentials, internal URLs, customer data, screenshots, logs, or proprietary architecture into this repository.
- Use only fictional names and locally generated data.
- Secrets belong in environment variables. Commit `.env.example`, never `.env`.

## Teaching style

- Explain the reason and failure mode before introducing an abstraction.
- Keep examples small, typed, runnable, and testable.
- Do not complete a learner's challenge before they have attempted it.
- Prefer one production concept per exercise.
- Python examples target Python 3.11+; Go examples target Go 1.22+.

## Quality

- Python: type hints, input validation, explicit errors, pytest.
- Go: `gofmt`, explicit error handling, table-driven tests where useful.
- Public APIs use versioned paths and a consistent response envelope.
- Any persistence lesson must discuss transactions, indexes, tenancy, and failure recovery.
