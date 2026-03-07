---
name: "recipe-create-wasabi-repo"
version: "1.0.0"
description: "Create Wasabi credentials and repository mapping."
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
# Recipe Create Wasabi Repo

PREREQUISITE: Load the following utility skills first: `bakufu-shared`, `bakufu-jobs`, `bakufu-sessions`

Create Wasabi credentials and repository mapping.

## Relevant Commands

- `bakufu workflows createWasabiRepo`
- `bakufu jobs list --pretty`
- `bakufu sessions show <session-id> --pretty`

## Instructions
- Start with the highest-level workflow/command for this recipe.
- Collect identifiers (job/session/repository) and keep them in every step.
- Escalate to targeted `bakufu run` calls when additional detail is required.

## Tips
- Keep recipe outputs concise: status, evidence, and next action.
- Store raw JSON artifacts for repeatability and auditing.
