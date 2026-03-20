---
name: "recipe-audit-four-eyes-events"
version: "1.0.0"
description: "Collect authorization events for four-eyes audit evidence."
metadata:
  openclaw:
    category: "recipe"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-shared"
        - "bakufu-jobs"
        - "bakufu-sessions"
---
# Recipe Audit Four Eyes Events

PREREQUISITE: Load the following utility skills first: `bakufu-shared`, `bakufu-jobs`, `bakufu-sessions`

Collect authorization events for four-eyes audit evidence.

## Relevant Commands

- `bakufu jobs list`
- `bakufu sessions show <session-id>`

## Instructions
- Start with the highest-level workflow/command for this recipe.
- Collect identifiers (job/session/repository) and keep them in every step.
- Escalate to targeted `bakufu run` calls when additional detail is required.

## Tips
- Keep recipe outputs concise: status, evidence, and next action.
- Store raw JSON artifacts for repeatability and auditing.
