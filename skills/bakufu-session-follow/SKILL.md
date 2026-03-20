---
name: "bakufu-session-follow"
version: "1.0.0"
description: "Poll a session until terminal state."
metadata:
  openclaw:
    category: "helper"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-sessions"
---
# Bakufu Session Follow

PREREQUISITE: Load the following utility skills first: `bakufu-sessions`

Poll a session until terminal state.

## Relevant Commands

- `bakufu sessions show <session-id>`
- `bakufu sessions logs <session-id>`

## Instructions
- Poll active sessions until terminal state before reporting completion.
- Stop polling only on terminal states or timeout.
- Pull logs automatically for failed or warning outcomes.

## Tips
- Use shorter intervals for incident response, longer for background checks.
- Persist timeout outcomes for retry analysis.
