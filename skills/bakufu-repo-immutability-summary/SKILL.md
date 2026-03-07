---
name: "bakufu-repo-immutability-summary"
version: "1.0.0"
description: "Summarize immutability settings across repositories."
metadata:
  openclaw:
    category: "helper"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-shared"
---
# Bakufu Repo Immutability Summary

PREREQUISITE: Load the following utility skills first: `bakufu-shared`

Summarize immutability settings across repositories.

## Relevant Commands

- `bakufu --help`
- `bakufu run <Tag> <OperationId> --pretty`

## Instructions
- Use this helper to perform focused task execution with structured output.
- Confirm prerequisites and identifiers before issuing writes.
- Capture resulting IDs and state for downstream workflows.

## Tips
- Prefer helper commands before low-level operation calls.
- Attach raw JSON when handing off to other operators.
