# Upstream Sync Automation

## Overview

This repository has an automated workflow that keeps the fork synchronized with the upstream repository [Turgibot/TrafficLab](https://github.com/Turgibot/TrafficLab).

## How It Works

The workflow runs automatically every 6 hours and:

1. **Checks for upstream updates** - Compares the fork's master branch with upstream's master branch
2. **Syncs the changes** - If updates are found, merges them into the fork's master branch
3. **Creates a Pull Request** - Opens a PR from master → feature/rm-nginx-to-use-traefik
4. **Verifies the build** - Builds all Docker images defined in docker-compose.yml
5. **Auto-merges** - If the build succeeds, automatically approves and merges the PR

## Manual Trigger

You can manually trigger the workflow:

1. Go to the **Actions** tab in GitHub
2. Select **"Sync Fork with Upstream and Auto-Merge to Feature Branch"**
3. Click **"Run workflow"**
4. Select the branch (usually master) and click **"Run workflow"**

## Feature Branch

The workflow targets the `feature/rm-nginx-to-use-traefik` branch. This branch will be automatically created if it doesn't exist.

## Build Verification

Before auto-merging, the workflow builds all Docker services defined in `docker-compose.yml`:
- Frontend (Vue.js application)
- Backend (FastAPI with SUMO)
- Database (PostgreSQL)

If any service fails to build, the PR will remain open for manual review and the auto-merge will not proceed.

## Troubleshooting

### Workflow doesn't run
- Check that the workflow file exists in `.github/workflows/sync-upstream-and-merge.yml`
- Verify the repository has Actions enabled in Settings → Actions

### Build failures
- Check the Actions log for detailed error messages
- Verify that docker-compose.yml is valid
- Ensure all Dockerfiles are present and correct

### PR not auto-merging
- Check that the build-and-verify job completed successfully
- Review the auto-merge job logs for any errors
- Verify repository permissions allow PR merging

## Configuration

The workflow is configured to run every 6 hours. To change the schedule, edit the cron expression in `.github/workflows/sync-upstream-and-merge.yml`:

```yaml
schedule:
  - cron: '0 */6 * * *'  # Every 6 hours
```

Common cron schedules:
- Every hour: `'0 * * * *'`
- Every 12 hours: `'0 */12 * * *'`
- Daily at midnight: `'0 0 * * *'`
- Weekly on Monday: `'0 0 * * 1'`
