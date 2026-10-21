---
title: "Raise the container log retention above 1 MB"
state: in-progress     # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: low          # critical | high | medium | low
effort: small          # small | medium | large | x-large
tags: [repo, logging]  # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
created: 2026-10-11
closed:                # YYYY-MM-DD. Set this only when state is closed.
owner: claude          # The person or agent working on the issue. Cleared when the issue returns to open.
approver:              # The person or agent who accepts the issue when it closes.
bookmark: jellyfin-reliability # The jj bookmark of the work on the issue. Set this when work starts.
workspaces: [fable]    # jj workspaces where local work on the issue has happened, for example [fix-login-bug].
metadata: {}           # Optional. Arbitrary key-value notes, for example an AI agent session id to resume work with context: {session-id: "abc123"}.
deferred-from:         # Optional. The issue (as a quoted wikilink) or bookmark that deferred this work.
parent:                # Optional. The parent issue (as a quoted wikilink), if this issue is a sub-issue.
depends-on: []           # Optional. Issues (as quoted wikilinks) that must close before this one can start, for example `["[[faster-startup]]"]`.
remote:                # Optional. A URL: the GitHub issue or Jira ticket that tracks this issue outside the repo.
---

# Raise the container log retention above 1 MB

## Summary

Raise the Docker log limit in the shared `x-logging-config` anchor. With 1 MB and one file, the logs of a failure are gone within minutes.

## Context

20 compose files under `services/` use this anchor:

```yaml
x-logging-config: &logging-config
  driver: "json-file"
  options:
    max-size: "1m"
    max-file: "1"
```

During the 2026-10-11 Jellyfin investigation, `docker logs` showed only the last few minutes. The Tailscale sidecar log was mostly `localapi` lines every 15 seconds. Any event older than that was lost.

A value such as `max-size: "10m"` with `max-file: "3"` keeps up to 30 MB for each container. For about 40 containers, that is about 1.2 GB as a maximum. Check the free space of the Docker data root on minerva before you select the value. Promtail sends some containers to Loki already (the `logging: "promtail"` label), so those containers need less local retention.

## Acceptance criteria

- [ ] The free space of the Docker data root is recorded in Notes.
- [ ] Each compose file that uses the anchor has the new values.
- [ ] `docker compose config` passes for each changed file.

## Out of scope

- Sending all containers to Loki.

## Notes

2026-10-20: All 20 compose files that use the anchor now set `max-size: "10m"` and
`max-file: "3"`. `docker compose config -q` passes for each changed file (themearr only
reports its required `THEMEARR_AUTH_TOKEN` variable as unset, which is expected outside the
deploy environment). Still to do on minerva: record the free space of the Docker data root,
then redeploy the stacks so the new limits take effect (log options apply on container
recreate, not on the fly).

## Resolution
