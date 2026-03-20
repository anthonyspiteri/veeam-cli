---
name: "bakufu-session-last-failed"
version: "1.0.0"
description: "Find the most recent failed session for a job."
metadata:
  openclaw:
    category: "helper"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-shared"
---
# Bakufu Session Last Failed

PREREQUISITE: Load the following utility skills first: `bakufu-shared`

Find the most recent failed session for a job.

## Relevant Commands

- `bakufu --help`
- `bakufu run <Tag> <OperationId>`

## Instructions
- Use this helper to perform focused task execution with structured output.
- Confirm prerequisites and identifiers before issuing writes.
- Capture resulting IDs and state for downstream workflows.

## Tips
- Prefer helper commands before low-level operation calls.
- Attach raw JSON when handing off to other operators.
