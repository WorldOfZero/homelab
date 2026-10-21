---
title: "Use a Roon image that includes ps"
state: open            # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: low          # critical | high | medium | low
effort: small          # small | medium | large | x-large
tags: [roon]           # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
created: 2026-10-21
closed:                # YYYY-MM-DD. Set this only when state is closed.
owner:                 # The person or agent working on the issue. Cleared when the issue returns to open.
approver:              # The person or agent who accepts the issue when it closes.
bookmark:              # The jj bookmark of the work on the issue. Set this when work starts.
workspaces: []         # jj workspaces where local work on the issue has happened, for example [fix-login-bug].
metadata: {}           # Optional. Arbitrary key-value notes, for example an AI agent session id to resume work with context: {session-id: "abc123"}.
deferred-from: "[[diagnose-roon-disconnects]]" # Optional. The issue (as a quoted wikilink) or bookmark that deferred this work.
parent:                # Optional. The parent issue (as a quoted wikilink), if this issue is a sub-issue.
depends-on: []           # Optional. Issues (as quoted wikilinks) that must close before this one can start, for example `["[[faster-startup]]"]`.
remote:                # Optional. A URL: the GitHub issue or Jira ticket that tracks this issue outside the repo.
---

# Use a Roon image that includes ps

## Summary

Run RoonServer from an image that includes `ps`. The wrapper script uses `ps` to find a RoonServer process that does not respond, and the slim image does not have it.

## Context

The RoonServer wrapper script logs `/app/RoonServer/Server/RoonServer: line 65: ps: command not found`. The `steefdebruijn/docker-roonserver:debian-12-slim` image does not include `procps`. Without `ps`, the wrapper cannot find or stop a RoonServer process that does not respond ("Not responding" in the log).

Options:

- Use a tag of the same image that includes `procps`, if one exists.
- Build a small image in `services/roon/` from the slim image, and install `procps`.

Do not change the network configuration of the stack. See [[diagnose-roon-disconnects]].

## Acceptance criteria

- [ ] The Roon log no longer shows `ps: command not found`.
- [ ] `services/roon/docker-compose.yaml` uses the new image or build, and Roon remotes still connect to `192.168.1.212`.

## Out of scope

- File permissions under the Roon config. See [[check-roon-exec-bits]].

## Notes


## Resolution

