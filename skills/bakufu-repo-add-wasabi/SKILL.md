---
name: "bakufu-repo-add-wasabi"
version: "1.0.0"
description: "Create a Wasabi object storage repository."
metadata:
  openclaw:
    category: "helper"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-repositories"
        - "bakufu-cloud-browser"
        - "bakufu-cloud-credentials-add"
---
# Bakufu Repo Add Wasabi

PREREQUISITE: Load the following utility skills first: `bakufu-repositories`, `bakufu-cloud-browser`, `bakufu-cloud-credentials-add`

Create a Wasabi object storage repository.

## Relevant Commands

- `bakufu workflows createWasabiRepo --spec @repo.json`

## Instructions
- Validate credentials, region, bucket, and folder before creation.
- Confirm immutability and retention settings align with policy.
- Verify repository health after create before assigning jobs.

## Tips
- Keep repository specs versioned for repeatable provisioning.
- Use dedicated credentials for principle-of-least-privilege.
