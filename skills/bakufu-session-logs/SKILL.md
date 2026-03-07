---
name: "bakufu-session-logs"
version: "1.0.0"
description: "Fetch session logs and surface failures."
metadata:
  openclaw:
    category: "helper"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-sessions"
---
# Bakufu Session Logs

PREREQUISITE: Load the following utility skills first: `bakufu-sessions`

Fetch session logs and surface failures.

## Relevant Commands

- `bakufu sessions logs <session-id> --pretty`

## Instructions
- Filter to failed/warning records first to reduce noise.
- Correlate task errors with infrastructure objects before remediation.
- Retain raw log JSON as evidence for audits and postmortems.

## Tips
- Use logs with session summary; each alone is incomplete.
- Capture exact error text and object IDs in tickets.
