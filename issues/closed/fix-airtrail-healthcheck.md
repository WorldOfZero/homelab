---
title: "Fix the AirTrail health check"
state: closed          # open | in-progress | closed. Must match the directory of the file.
resolution: completed  # completed | abandoned. Set this only when state is closed.
priority: medium       # critical | high | medium | low
effort: small          # small | medium | large | x-large
tags: [bug, airtrail]  # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
created: 2026-11-02
closed: 2026-11-02     # YYYY-MM-DD. Set this only when state is closed.
owner: claude          # The person or agent working on the issue. Cleared when the issue returns to open.
approver:              # The person or agent who accepts the issue when it closes.
bookmark: airtrail-healthcheck # The jj bookmark of the work on the issue. Set this when work starts.
workspaces: [fable]    # jj workspaces where local work on the issue has happened, for example [fix-login-bug].
metadata: {}           # Optional. Arbitrary key-value notes, for example an AI agent session id to resume work with context: {session-id: "abc123"}.
deferred-from:         # Optional. The issue (as a quoted wikilink) or bookmark that deferred this work.
parent:                # Optional. The parent issue (as a quoted wikilink), if this issue is a sub-issue.
depends-on: []           # Optional. Issues (as quoted wikilinks) that must close before this one can start, for example `["[[faster-startup]]"]`.
remote:                # Optional. A URL: the GitHub issue or Jira ticket that tracks this issue outside the repo.
---

# Fix the AirTrail health check

## Summary

Fix the AirTrail health check, and fix the owner of its upload directory. AirTrail shows as unhealthy all the time, although the application runs.

## Context

The health check uses `wget`, and the image has no `wget`. The health log shows `/bin/sh: 1: wget: not found`. Thus a healthy application fails each check. The URL `/api/v1/settings/public` is also not in AirTrail v3.11.1, which has `/api/ping`. The image includes its own `airtrail-healthcheck` command.

The log also shows `EACCES` for `/app/uploads`. On the host this is `/mnt/Fast/Configuration/flights/airtrail`, which root owns. The application runs as UID 1000. See [[flights-tandoor-dashboard]].

## Acceptance criteria

- [x] The health check uses the `airtrail-healthcheck` command of the image.
- [x] After the deploy, `app-airtrail` shows as healthy.
- [ ] The human sets the owner of the upload directory to `1000:1000`, and the `EACCES` error stops after a restart.

## Out of scope

- Other AirTrail settings.

## Notes

2026-11-02: From the human: the health log shows `wget: not found`, and the upload directory is `drwxr-xr-x 0 0`.

## Resolution

The human confirmed that this work is finished. The health check uses the airtrail-healthcheck command, and app-airtrail shows as healthy. The container has not restarted since the last EACCES line at 2026-11-02 04:08 UTC, so the logs do not yet show the result of the upload directory fix.

