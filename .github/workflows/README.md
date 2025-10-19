# GitHub Actions Workflows

This directory contains automated workflows for the TrafficLab repository.

## sync-upstream-and-merge.yml

This workflow automatically syncs the fork with the upstream repository (Turgibot/TrafficLab) and merges updates into the feature branch.

### What it does:

1. **Syncs fork with upstream**: Checks for updates from Turgibot/TrafficLab master branch and syncs them to this fork's master branch
2. **Creates Pull Request**: Opens a PR from master → feature/rm-nginx-to-use-traefik
3. **Builds Docker images**: Verifies that all Docker images in docker-compose.yml build successfully
4. **Auto-merges**: If all checks pass, automatically approves and merges the PR

### Trigger schedule:

- Runs every 6 hours automatically
- Can be manually triggered via GitHub Actions UI

### Requirements:

- The feature/rm-nginx-to-use-traefik branch must exist (workflow will create it if missing)
- Docker Compose build must succeed for auto-merge to proceed
