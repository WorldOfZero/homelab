---
title: "Add a dashboard for Flights and Tandoor"
state: in-progress     # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: medium       # critical | high | medium | low
effort: small          # small | medium | large | x-large
tags: [feature, grafana] # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
created: 2026-11-02
closed:                # YYYY-MM-DD. Set this only when state is closed.
owner: claude          # The person or agent working on the issue. Cleared when the issue returns to open.
approver:              # The person or agent who accepts the issue when it closes.
bookmark: flights-tandoor-dashboard # The jj bookmark of the work on the issue. Set this when work starts.
workspaces: [fable]    # jj workspaces where local work on the issue has happened, for example [fix-login-bug].
metadata: {}           # Optional. Arbitrary key-value notes, for example an AI agent session id to resume work with context: {session-id: "abc123"}.
deferred-from:         # Optional. The issue (as a quoted wikilink) or bookmark that deferred this work.
parent:                # Optional. The parent issue (as a quoted wikilink), if this issue is a sub-issue.
depends-on: []           # Optional. Issues (as quoted wikilinks) that must close before this one can start, for example `["[[faster-startup]]"]`.
remote:                # Optional. A URL: the GitHub issue or Jira ticket that tracks this issue outside the repo.
---

# Add a dashboard for Flights and Tandoor

## Summary

Add a dashboard for Flights (AirTrail) and Tandoor that shows health, backups, resources and logs.

## Context

These applications have no metrics in use, so the dashboard uses Docker state, cAdvisor, logs and a tailnet probe. Tandoor has an `ENABLE_METRICS` setting. It is not on, because it was not tested with several Gunicorn workers.

## Acceptance criteria

- [x] The dashboard shows status, backups, resources and logs for each application.
- [x] All queries run through the live Grafana with no errors.
- [ ] After the deploy, the probes show success.

## Out of scope

- A fix for the AirTrail health state and upload permission error.

## Notes

2026-11-02: From the human: add this dashboard.

2026-11-02: `app-airtrail` was unhealthy when the data collection started. Its log shows `EACCES` for `/app/uploads`, which is `/mnt/Fast/Configuration/flights/airtrail` on the host. The health check is a separate request, so the cause of the unhealthy state is not confirmed.

## Resolution
