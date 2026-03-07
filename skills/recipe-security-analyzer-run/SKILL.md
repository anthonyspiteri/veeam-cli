---
name: "recipe-security-analyzer-run"
version: "1.0.0"
description: "Run Security Analyzer and summarize findings."
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
# Recipe Security Analyzer Run

PREREQUISITE: Load the following utility skills first: `bakufu-shared`, `bakufu-jobs`, `bakufu-sessions`

Run Security Analyzer and summarize findings.

## Relevant Commands

- `bakufu workflows runSecurityAnalyzer`
- `bakufu jobs list --pretty`
- `bakufu sessions show <session-id> --pretty`

## Instructions
- Start with the highest-level workflow/command for this recipe.
- Collect identifiers (job/session/repository) and keep them in every step.
- Escalate to targeted `bakufu run` calls when additional detail is required.

## Tips
- Keep recipe outputs concise: status, evidence, and next action.
- Store raw JSON artifacts for repeatability and auditing.
