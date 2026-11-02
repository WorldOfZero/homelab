---
title: "Give each application its own dashboard"
state: in-progress     # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: low          # critical | high | medium | low
effort: small          # small | medium | large | x-large
tags: [feature, grafana] # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
created: 2026-11-02
closed:                # YYYY-MM-DD. Set this only when state is closed.
owner: claude          # The person or agent working on the issue. Cleared when the issue returns to open.
approver:              # The person or agent who accepts the issue when it closes.
bookmark: split-app-dashboards # The jj bookmark of the work on the issue. Set this when work starts.
workspaces: [fable]    # jj workspaces where local work on the issue has happened, for example [fix-login-bug].
metadata: {}           # Optional. Arbitrary key-value notes, for example an AI agent session id to resume work with context: {session-id: "abc123"}.
deferred-from:         # Optional. The issue (as a quoted wikilink) or bookmark that deferred this work.
parent:                # Optional. The parent issue (as a quoted wikilink), if this issue is a sub-issue.
depends-on: []           # Optional. Issues (as quoted wikilinks) that must close before this one can start, for example `["[[faster-startup]]"]`.
remote:                # Optional. A URL: the GitHub issue or Jira ticket that tracks this issue outside the repo.
---

# Give each application its own dashboard

## Summary

Give Flights, Tandoor, Karakeep and Kavita a dashboard each, in place of the two combined dashboards.

## Context

[[flights-tandoor-dashboard]] and [[monitor-apps-and-tsidp]] added combined dashboards. The dashboard provider now has `disableDeletion: false`, so Grafana removes a dashboard when its file is removed.

## Acceptance criteria

- [x] Each application has its own dashboard.
- [x] A test shows that Grafana removes the combined dashboards when their files are removed.
- [ ] After the deploy, Grafana shows the four dashboards, and not the combined dashboards.

## Out of scope

- New panels.

## Notes

2026-11-02: From the human: Karakeep, Flights, Kavita and Tandoor must each have a dashboard.

## Resolution
