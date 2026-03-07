---
name: "bakufu-security-analyzer-last-run"
version: "1.0.0"
description: "Get the latest Security Analyzer run state and findings."
metadata:
  openclaw:
    category: "helper"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-shared"
---
# Bakufu Security Analyzer Last Run

PREREQUISITE: Load the following utility skills first: `bakufu-shared`

Get the latest Security Analyzer run state and findings.

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
