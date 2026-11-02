---
title: "Monitor Karakeep, Kavita, GameScores and tsidp"
state: in-progress     # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: medium       # critical | high | medium | low
effort: medium         # small | medium | large | x-large
tags: [feature, grafana] # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
created: 2026-11-02
closed:                # YYYY-MM-DD. Set this only when state is closed.
owner: claude          # The person or agent working on the issue. Cleared when the issue returns to open.
approver:              # The person or agent who accepts the issue when it closes.
bookmark: app-dashboards # The jj bookmark of the work on the issue. Set this when work starts.
workspaces: [fable]    # jj workspaces where local work on the issue has happened, for example [fix-login-bug].
metadata: {}           # Optional. Arbitrary key-value notes, for example an AI agent session id to resume work with context: {session-id: "abc123"}.
deferred-from:         # Optional. The issue (as a quoted wikilink) or bookmark that deferred this work.
parent:                # Optional. The parent issue (as a quoted wikilink), if this issue is a sub-issue.
depends-on: []           # Optional. Issues (as quoted wikilinks) that must close before this one can start, for example `["[[faster-startup]]"]`.
remote:                # Optional. A URL: the GitHub issue or Jira ticket that tracks this issue outside the repo.
---

# Monitor Karakeep, Kavita, GameScores and tsidp

## Summary

Monitor Karakeep, Kavita, GameScores and tsidp, and probe each application at its tailnet address. The human owns GameScores and wants to monitor it closely.

## Context

A blackbox exporter uses the network of the Grafana sidecar, so it reaches each application in the same way as a tailnet client. It tests DNS, Tailscale, TLS and the HTTP response.

- Karakeep has a metrics endpoint at `/api/metrics`, which needs a token.
- Kavita has no metrics endpoint that was found, so its dashboard uses logs and container metrics.
- tsidp has no metrics endpoint, but it logs `token issued` for each login.
- The GameScores source is private and was not available for this work. Its dashboard uses logs, container metrics and the probe.

## Acceptance criteria

- [x] Grafana provisions dashboards for Karakeep and Kavita, GameScores, and tsidp.
- [x] The blackbox exporter passes a test with the real exporter image.
- [ ] After the deploy, all probes show success. The tailnet policy must allow access from the Grafana sidecar.
- [ ] The human decides how GameScores will expose application metrics.

## Out of scope

- Grafana alert rules.
- Karakeep worker metrics. These use a separate port.

## Notes

2026-11-02: From the human: monitor Karakeep, Kavita, GameScores and tsidp.

2026-11-02: GameScores logged an antiforgery error for a data protection key on 2026-10-29. The stack has no volume, so the keys can be lost when the container is recreated. Check how the application stores its keys.

2026-11-02: Karakeep has `OTEL_TRACING_ENABLED: true`, and it writes spans to its log. This gave about 313,000 lines in 7 days.

## Resolution
