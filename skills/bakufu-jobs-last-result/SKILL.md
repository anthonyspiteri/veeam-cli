---
name: "bakufu-jobs-last-result"
version: "1.0.0"
description: "Get latest job session result and status."
metadata:
  openclaw:
    category: "helper"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-jobs"
        - "bakufu-sessions"
---
# Bakufu Jobs Last Result

PREREQUISITE: Load the following utility skills first: `bakufu-jobs`, `bakufu-sessions`

Get latest job session result and status.

## Relevant Commands

- `bakufu jobs list`
- `bakufu sessions show <session-id>`

## Instructions
- Resolve the latest session for the target job before escalation.
- Use session state and result together; state alone is not enough.
- Escalate repeated warnings as operational debt before they become failures.

## Tips
- Track trends across runs, not just the latest result.
- Attach session IDs in incident summaries.
