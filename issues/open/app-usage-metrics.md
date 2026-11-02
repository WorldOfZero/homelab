---
title: "Track flights, recipes and bookmarks"
state: open            # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: medium       # critical | high | medium | low
effort: medium         # small | medium | large | x-large
tags: [feature, grafana] # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
created: 2026-11-02
closed:                # YYYY-MM-DD. Set this only when state is closed.
owner:                 # The person or agent working on the issue. Cleared when the issue returns to open.
approver:              # The person or agent who accepts the issue when it closes.
bookmark:                   # The jj bookmark of the work on the issue. Set this when work starts.
workspaces: [fable]    # jj workspaces where local work on the issue has happened, for example [fix-login-bug].
metadata: {}           # Optional. Arbitrary key-value notes, for example an AI agent session id to resume work with context: {session-id: "abc123"}.
deferred-from:         # Optional. The issue (as a quoted wikilink) or bookmark that deferred this work.
parent:                # Optional. The parent issue (as a quoted wikilink), if this issue is a sub-issue.
depends-on: []           # Optional. Issues (as quoted wikilinks) that must close before this one can start, for example `["[[faster-startup]]"]`.
remote:                # Optional. A URL: the GitHub issue or Jira ticket that tracks this issue outside the repo.
---

# Track flights, recipes and bookmarks

## Summary

Show real usage on the application dashboards: flights taken, recipes recorded, and bookmarks added.

## Context

- Karakeep has these numbers at `/api/metrics`.
- AirTrail has no metrics endpoint. Tandoor can report activity counters, but not totals.
- Grafana has a PostgreSQL data source, so the Flights and Tandoor dashboards read their databases directly. No exporter is necessary.

Grafana Viewers can send any SQL that the role allows through the API. Thus the `grafana_reader` role has `SELECT` on selected tables only, and it can read only `id` and `username` in the AirTrail `user` table.

The databases and the Grafana sidecar share the external `app-databases` network. Only these containers join it.

## Acceptance criteria

- [x] The Flights and Tandoor dashboards show totals and lists from their databases.
- [x] A test shows that a Viewer cannot read password hashes or sessions, and cannot change data.
- [ ] After the deploy, the panels show real data. Check that `duration` in AirTrail is in seconds.
- [ ] After the Karakeep redeploy, its panels show real data.

## Out of scope

- Kavita library counts.
- Tandoor request metrics.

## Notes

2026-11-02: From the human: track flights, recipes and bookmarks. Do not use an exporter when Grafana can read the database.

2026-11-02: A first design used `sql_exporter`, and it was removed before any commit.

2026-11-02: The test used Grafana 13.1.1 and Postgres 16, with tables from the AirTrail schema and sample data. The Tandoor panels were not run against tables.

2026-11-02: From the human: do not add the database readers now. The Karakeep bookmark panels continue. The bookmark `app-usage-metrics` keeps the tested work for Flights and Tandoor: the data sources, the `app-databases` network, the panels, and the `grafana_reader` role commands. Start from that work if this issue continues.

## Resolution
