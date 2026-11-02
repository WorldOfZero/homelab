---
title: "Show tailnet traffic through DERP"
state: in-progress     # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: medium       # critical | high | medium | low
effort: small          # small | medium | large | x-large
tags: [feature, grafana, tailscale] # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
created: 2026-11-02
closed:                # YYYY-MM-DD. Set this only when state is closed.
owner: claude          # The person or agent working on the issue. Cleared when the issue returns to open.
approver:              # The person or agent who accepts the issue when it closes.
bookmark: tailscale-derp-metrics # The jj bookmark of the work on the issue. Set this when work starts.
workspaces: [fable]         # jj workspaces where local work on the issue has happened, for example [fix-login-bug].
metadata: {}           # Optional. Arbitrary key-value notes, for example an AI agent session id to resume work with context: {session-id: "abc123"}.
deferred-from:         # Optional. The issue (as a quoted wikilink) or bookmark that deferred this work.
parent:                # Optional. The parent issue (as a quoted wikilink), if this issue is a sub-issue.
depends-on: []           # Optional. Issues (as quoted wikilinks) that must close before this one can start, for example `["[[faster-startup]]"]`.
remote:                # Optional. A URL: the GitHub issue or Jira ticket that tracks this issue outside the repo.
---

# Show tailnet traffic through DERP

## Summary

Show the tailnet traffic that goes through Tailscale DERP relays on the Network dashboard.

## Context

Traffic through DERP is slower than a direct path. Tailscale clients count bytes on each path in `tailscaled_inbound_bytes_total` and `tailscaled_outbound_bytes_total`. The sidecars did not serve these metrics, and they served health only on `127.0.0.1`.

## Acceptance criteria

- [x] Prometheus has a scrape job for all running sidecars and the minerva node.
- [x] The Network dashboard has a Tailscale paths row.
- [ ] After the deploy, each `tailscale` target is up.
- [ ] The panels show real traffic.

## Out of scope

- Traffic of tailnet devices that are not on minerva.
- Alerts on DERP traffic. Look at normal values first.

## Notes

2026-11-02: From the human: "can we show the amount of traffic being routed through tailscale DERP servers?"

2026-11-02: The metric names were read from a real `tailscale/tailscale:v1.98` container with no tailnet login, so the counters were 0. The panels were not rendered, because the sandbox has no Grafana image. The first deploy restarts each application that shares a sidecar network.

## Resolution

<Complete this section when you close the issue.
- Completed: tell what was done. Link to the changelog version and the decision records, for example `[[0.0.5]]`.
- Abandoned: tell why the work stopped. Link to the issue or decision that replaces it, if one exists.>
