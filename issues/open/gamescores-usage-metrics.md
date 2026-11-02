---
title: "Track GameScores rooms, users and missing games"
state: open            # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: medium       # critical | high | medium | low
effort: medium         # small | medium | large | x-large
tags: [feature, grafana, gamescores] # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
created: 2026-11-02
closed:                # YYYY-MM-DD. Set this only when state is closed.
owner:                 # The person or agent working on the issue. Cleared when the issue returns to open.
approver:              # The person or agent who accepts the issue when it closes.
bookmark:              # The jj bookmark of the work on the issue. Set this when work starts.
workspaces: []         # jj workspaces where local work on the issue has happened, for example [fix-login-bug].
metadata: {}           # Optional. Arbitrary key-value notes, for example an AI agent session id to resume work with context: {session-id: "abc123"}.
deferred-from:         # Optional. The issue (as a quoted wikilink) or bookmark that deferred this work.
parent:                # Optional. The parent issue (as a quoted wikilink), if this issue is a sub-issue.
depends-on: []           # Optional. Issues (as quoted wikilinks) that must close before this one can start, for example `["[[faster-startup]]"]`.
remote:                # Optional. A URL: the GitHub issue or Jira ticket that tracks this issue outside the repo.
---

# Track GameScores rooms, users and missing games

## Summary

Report rooms and users for each game, and the games that users request but GameScores does not have. The homelab monitoring stack will show this data on the GameScores Grafana dashboard.

## Context

The GameScores logs and container metrics do not have this data, so the application must report it. GameScores is an ASP.NET application. It runs in Docker on port 8080 behind a Tailscale sidecar. Prometheus reaches it at `tailscale-gamescores:8080`, and Alloy sends its console log to Loki with 30 days of retention.

This issue was written in the homelab repo, without access to the GameScores source. Change the names and the code examples to match the application.

### Proposed data

| Data | Method | Name |
|---|---|---|
| Active rooms for each game | Prometheus gauge | `gamescores_rooms_active{game}` |
| Active users for each game | Prometheus gauge | `gamescores_users_active{game}` |
| Rooms created for each game | Prometheus counter | `gamescores_rooms_created_total{game}` |
| Requested games that do not exist | One log line for each request | `game_not_found requested="<name>"` |

### Label rules

- Use `game` as a label only with a value from the list of known games.
- Do not use a room ID, a user ID, or a requested game name as a label. Each new value creates a new time series.
- A requested game name comes from the user, so its values have no limit. Log it, and do not use it as a label.
- Limit the length of a requested name, and remove control characters and quotes before the application logs it.

### Example with prometheus-net.AspNetCore

```csharp
// Program.cs
app.MapMetrics(); // Exposes /metrics

// Metrics
static readonly Gauge RoomsActive =
    Metrics.CreateGauge("gamescores_rooms_active", "Active rooms", new[] { "game" });
static readonly Gauge UsersActive =
    Metrics.CreateGauge("gamescores_users_active", "Active users", new[] { "game" });
static readonly Counter RoomsCreated =
    Metrics.CreateCounter("gamescores_rooms_created_total", "Rooms created", new[] { "game" });

// Update these where rooms and users change
RoomsActive.WithLabels(game.Id).Set(roomCount);
UsersActive.WithLabels(game.Id).Set(userCount);
RoomsCreated.WithLabels(game.Id).Inc();

// When a requested game does not exist
logger.LogInformation("game_not_found requested=\"{Requested}\"", Clean(requested));

// Limits the length, and removes characters that can break or forge a log line
static string Clean(string value) =>
    new string(value.Where(c => !char.IsControl(c) && c != '"').Take(100).ToArray());
```

A gauge for a game that has no rooms must return to 0. Set each known game on each update, or the dashboard keeps the last value.

`/metrics` has no login, and all clients that can reach the application can read it. These counts are not sensitive if the label rules are followed.

### Work in the homelab repo after this issue

- Add a Prometheus scrape job for `tailscale-gamescores:8080`.
- Add panels to the GameScores dashboard for rooms and users for each game, the highest user counts, and the most requested missing games.

## Open questions

- Q1: What does an active user mean? Proposed: a user with an open connection.
- Q2: When does a room stop being active? Proposed: when it has no users.
- Q3: How long must missing game requests stay available? Loki keeps them for 30 days. For more time, store them in the application database. Proposed: start with 30 days.

## Acceptance criteria

- [ ] Each open question has an answer in Notes.
- [ ] GameScores exposes `/metrics`, with the rooms and users metrics for each game.
- [ ] A game with no rooms reports 0.
- [ ] GameScores logs one `game_not_found` line for each request for a game that does not exist.
- [ ] A test shows that a long name or a name with control characters or quotes cannot break or forge a log line.
- [ ] No metric label uses a room ID, a user ID, or a requested game name.

## Out of scope

- Other application metrics for GameScores.
- The homelab scrape job and dashboard panels. These are in the homelab repo.

## Notes

2026-11-02: From the human: track rooms and users by game, and games that are requested but not in the application. Move this issue to the GameScores repo.

## Resolution
