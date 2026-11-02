---
title: "Fix image pulls that stop Portainer Git updates"
state: in-progress     # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: high         # critical | high | medium | low
effort: small          # small | medium | large | x-large
tags: [bug, portainer] # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
created: 2026-11-02
closed:                # YYYY-MM-DD. Set this only when state is closed.
owner: claude          # The person or agent working on the issue. Cleared when the issue returns to open.
approver:              # The person or agent who accepts the issue when it closes.
bookmark: karakeep-chrome-docker-hub # The jj bookmark of the work on the issue. Set this when work starts.
workspaces: [fable]         # jj workspaces where local work on the issue has happened, for example [fix-login-bug].
metadata: {}           # Optional. Arbitrary key-value notes, for example an AI agent session id to resume work with context: {session-id: "abc123"}.
deferred-from:         # Optional. The issue (as a quoted wikilink) or bookmark that deferred this work.
parent:                # Optional. The parent issue (as a quoted wikilink), if this issue is a sub-issue.
depends-on: []           # Optional. Issues (as quoted wikilinks) that must close before this one can start, for example `["[[faster-startup]]"]`.
remote:                # Optional. A URL: the GitHub issue or Jira ticket that tracks this issue outside the repo.
---

# Fix image pulls that stop Portainer Git updates

## Summary

Make all image pulls work, so that Portainer Git updates reach each stack.

## Context

A Git update stops when a pull fails, so the stack keeps its old containers. Since at least 2026-10-31, Portainer logs `denied` for all `ghcr.io` images on minerva. Public images fail too, but the same public images give 200 to an anonymous request from another machine, so the credentials on minerva are the likely cause. Also, `gcr.io/zenika-hub/alpine-chrome` fails for all users, because the project has no billing.

## Acceptance criteria

- [x] Karakeep uses `zenika/alpine-chrome:124` from Docker Hub.
- [ ] The human replaces or removes the `ghcr.io` credentials on minerva.
- [ ] No `denied` lines in the Portainer logs after the next poll.
- [ ] The stacks that failed have their new containers.
- [ ] All `tailscale` Prometheus targets are up.

## Out of scope

- Pin the hotio images, which have no tag.

## Notes

2026-11-02: The sidecars that were not updated (bazarr, gamescores, karakeep, radarr, seerr, sonarr, themearr, tsidp) are all in stacks with a failed pull. An earlier note said that polling was probably off. That was wrong.

2026-11-02: The digest of the Docker Hub image was not compared with the `gcr.io` image, because `gcr.io` denies access. Both have the tag 124.

## Resolution

<Complete this section when you close the issue.
- Completed: tell what was done. Link to the changelog version and the decision records, for example `[[0.0.5]]`.
- Abandoned: tell why the work stopped. Link to the issue or decision that replaces it, if one exists.>
