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
        - "bakufu-repositories"
        - "bakufu-cloud-browser"
        - "bakufu-cloud-credentials-add"
        - "bakufu-object-storage-browse"
---
# Recipe Create Wasabi Repo

PREREQUISITE: Load the following utility skills first: `bakufu-repositories`, `bakufu-cloud-browser`, `bakufu-cloud-credentials-add`, `bakufu-object-storage-browse`

Create Wasabi credentials and repository mapping.

## Relevant Commands

- `bakufu workflows createWasabiRepo --spec @repo.json`
- `bakufu call /api/v1/cloudBrowser --method POST --json @browse.json --pretty`
- `bakufu run Repositories GetAllRepositories --pretty`

## Instructions
- Create or verify cloud credentials before repository creation.
- Browse the target bucket and folder to confirm path accessibility.
- Run the createWasabiRepo workflow with a validated spec file.
- Verify the new repository appears healthy in the repository list after creation.

## Tips
- Keep repository specs as versioned JSON files for repeatable provisioning.
- Validate immutability and retention settings align with policy before creation.
