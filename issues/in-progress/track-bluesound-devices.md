---
title: "Track Bluesound devices on the Roon dashboard"
state: in-progress     # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: medium       # critical | high | medium | low
effort: small          # small | medium | large | x-large
tags: [feature, grafana, roon] # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
created: 2026-11-02
closed:                # YYYY-MM-DD. Set this only when state is closed.
owner: claude          # The person or agent working on the issue. Cleared when the issue returns to open.
approver:              # The person or agent who accepts the issue when it closes.
bookmark: bluesound-panels # The jj bookmark of the work on the issue. Set this when work starts.
workspaces: [fable]    # jj workspaces where local work on the issue has happened, for example [fix-login-bug].
metadata: {}           # Optional. Arbitrary key-value notes, for example an AI agent session id to resume work with context: {session-id: "abc123"}.
deferred-from:         # Optional. The issue (as a quoted wikilink) or bookmark that deferred this work.
parent:                # Optional. The parent issue (as a quoted wikilink), if this issue is a sub-issue.
depends-on: []           # Optional. Issues (as quoted wikilinks) that must close before this one can start, for example `["[[faster-startup]]"]`.
remote:                # Optional. A URL: the GitHub issue or Jira ticket that tracks this issue outside the repo.
---

# Track Bluesound devices on the Roon dashboard

## Summary

Show the health of each Bluesound device on the Roon dashboard. These devices give audio to all of the home.

## Context

Roon logs each RAAT connection as `Bluesound <model> @ <ip>:<port>`, and reports endpoint availability when it loads a zone. Two devices of the same model have the same name, so the panels also show the IP address. See [[streaming-and-roon-dashboards]].

## Acceptance criteria

- [x] The Roon dashboard shows drops, reconnects and write errors for each device.
- [x] The Roon dashboard shows endpoint availability reports and the connection events.
- [x] All queries run through the live Grafana with no errors.
- [ ] After the deploy, a new drop appears on the dashboard at the correct time.

## Out of scope

- Direct monitoring of each device through the BluOS API. This data shows only what Roon sees, so it cannot show a device problem when Roon is not connected. Direct monitoring needs fixed device addresses and network access from Prometheus.

## Notes

2026-11-01: From the human: track the Bluesound devices on the Roon dashboard.

2026-11-01: The log has one event for 7 devices at 02:01:54 and 02:01:55 on 2026-11-01. They all dropped and connected again in the same seconds. One event does not show a cause.

## Resolution
