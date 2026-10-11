---
title: "Make start-service.nu check the compose files, not the directory"
state: open            # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: low          # critical | high | medium | low
effort: small          # small | medium | large | x-large
tags: [bug, scripts]   # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
created: 2026-10-11
closed:                # YYYY-MM-DD. Set this only when state is closed.
owner:                 # The person or agent working on the issue. Cleared when the issue returns to open.
approver:              # The person or agent who accepts the issue when it closes.
bookmark:              # The jj bookmark of the work on the issue. Set this when work starts.
workspaces: []         # jj workspaces where local work on the issue has happened, for example [fix-login-bug].
metadata: {}           # Optional. Arbitrary key-value notes, for example an AI agent session id to resume work with context: {session-id: "abc123"}.
deferred-from:         # Optional. The issue (as a quoted wikilink) or bookmark that deferred this work.
parent:                # Optional. The parent issue (as a quoted wikilink), if this issue is a sub-issue.
depends-on: []           # Optional. Issues (as quoted wikilinks) that must close before this one can start, for example `["[[faster-startup]]"]`.
remote:                # Optional. A URL: the GitHub issue or Jira ticket that tracks this issue outside the repo.
---

# Make start-service.nu check the compose files, not the directory

## Summary

Fix the existence checks in `scripts/start-service.nu`. They test the service directory again instead of `docker-compose.yaml` and `docker-compose.local.yaml`, so the clear error messages never appear.

## Context

`main start` and `main stop` run `docker compose -f <service>/docker-compose.yaml -f <service>/docker-compose.local.yaml` by default (`local` is `true`). Each check uses `if not ($serviceDir | path exists)`. The directory exists already at that point, so the check is always false.

If a service has no `docker-compose.local.yaml`, the user gets a `docker compose` error about a missing file. The user does not get the message "Create a local overlay before running the service locally."

`services/jellyfin/docker-compose.local.yaml` is an empty file. It is the only local overlay in the repo. `docker compose` accepts an empty overlay, so `nu scripts/start-service.nu start jellyfin` works now. Do not delete that file: the script needs it.

## Acceptance criteria

- [ ] The checks in `main start` and `main stop` test `$service` and `$localService`.
- [ ] `start` for a service with no `docker-compose.local.yaml` prints the overlay error message.
- [ ] `start jellyfin` still works with the empty overlay.
- [ ] The duplicate code in `main start` and `main stop` is moved into one helper, or Notes tells why not.

## Out of scope

- Local overlays for other services.

## Notes

2026-10-11: Found during the Jellyfin efficiency review. A first draft of this review planned to delete the empty overlay. That would break this script.

## Resolution
