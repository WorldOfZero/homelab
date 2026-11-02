---
title: "Keep Kavita data when its container is recreated"
state: in-progress     # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: high         # critical | high | medium | low
effort: small          # small | medium | large | x-large
tags: [bug, kavita]    # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
created: 2026-11-02
closed:                # YYYY-MM-DD. Set this only when state is closed.
owner: claude          # The person or agent working on the issue. Cleared when the issue returns to open.
approver:              # The person or agent who accepts the issue when it closes.
bookmark: kavita-config-mount # The jj bookmark of the work on the issue. Set this when work starts.
workspaces: [fable]         # jj workspaces where local work on the issue has happened, for example [fix-login-bug].
metadata: {}           # Optional. Arbitrary key-value notes, for example an AI agent session id to resume work with context: {session-id: "abc123"}.
deferred-from:         # Optional. The issue (as a quoted wikilink) or bookmark that deferred this work.
parent:                # Optional. The parent issue (as a quoted wikilink), if this issue is a sub-issue.
depends-on: []           # Optional. Issues (as quoted wikilinks) that must close before this one can start, for example `["[[faster-startup]]"]`.
remote:                # Optional. A URL: the GitHub issue or Jira ticket that tracks this issue outside the repo.
---

# Keep Kavita data when its container is recreated

## Summary

Keep the Kavita database, settings and backups when the container is recreated.

## Context

The compose file mounts the host directory at `/kavita/config`. That path is for the official image. The `linuxserver/kavita` image keeps all data in `/config`, and it has no `VOLUME`, so the data was in the container layer. Each recreate deleted the database, users, settings and backups.

## Acceptance criteria

- [x] A local test keeps the admin account after a recreate, and the second start runs no full migrations.
- [ ] The human copies the current data to the host before the deploy.
- [ ] After the deploy, `kavita.db` is in `/mnt/Fast/Configuration/kavita/config`.
- [ ] Kavita keeps its data after the next recreate.

## Out of scope

- Recover data from earlier containers. Docker deleted their layers.
- Change the image.

## Notes

2026-11-02: From the human: "kavita restarts keep losing data and requiring reconfiguration."

2026-11-02: The logs show full migrations at 04:09Z and 04:41Z. Commit `836a807c` changed the sidecar, which recreated the sidecar and Kavita at 04:09Z. The human registered at 04:31Z, and the 04:41Z recreate deleted that. A restart of the same container keeps data. Only a recreate deletes it.

## Resolution

<Complete this section when you close the issue.
- Completed: tell what was done. Link to the changelog version and the decision records, for example `[[0.0.5]]`.
- Abandoned: tell why the work stopped. Link to the issue or decision that replaces it, if one exists.>
