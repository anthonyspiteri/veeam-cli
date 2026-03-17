---
name: "recipe-auditor-monthly-pack"
version: "1.0.0"
description: "Build a monthly compliance evidence pack for auditors."
metadata:
  openclaw:
    category: "recipe"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-sessions"
        - "bakufu-security"
        - "bakufu-license"
        - "bakufu-repositories"
        - "bakufu-session-logs"
---
# Recipe Auditor Monthly Pack

PREREQUISITE: Load the following utility skills first: `bakufu-sessions`, `bakufu-security`, `bakufu-license`, `bakufu-repositories`, `bakufu-session-logs`

Build a monthly compliance evidence pack for auditors.

## Relevant Commands

- `bakufu workflows capacityReport`
- `bakufu workflows validateImmutability`
- `bakufu run Security GetBestPracticesComplianceResult --pretty`
- `bakufu run Security GetFourEyesAuthorizationEvents --pretty`
- `bakufu run License GetLicense --pretty`
- `bakufu run Sessions GetAllSessions --params '{"limit": 500}' --page-all --pretty`

## Instructions
- Collect evidence from capacity, immutability, security, and license domains.
- Export session history for the reporting period with all result states.
- Gather four-eyes authorization events and best-practice compliance results.
- Assemble all artifacts into a dated evidence pack with source timestamps.
- Validate that every finding has a traceable session or object ID.

## Tips
- Use consistent date ranges across all evidence sources for the pack.
- Separate raw JSON evidence from summarized findings for reviewer clarity.
- Cross-check control evidence between sessions, security, and capacity outputs.
