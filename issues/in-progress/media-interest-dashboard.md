---
title: "Show what people watch and hear in the last 30 days"
state: in-progress     # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: medium       # critical | high | medium | low
effort: medium         # small | medium | large | x-large
tags: [feature, grafana, jellyfin] # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
created: 2026-11-02
closed:                # YYYY-MM-DD. Set this only when state is closed.
owner: claude          # The person or agent working on the issue. Cleared when the issue returns to open.
approver:              # The person or agent who accepts the issue when it closes.
bookmark: media-interest # The jj bookmark of the work on the issue. Set this when work starts.
workspaces: [fable]    # jj workspaces where local work on the issue has happened, for example [fix-login-bug].
metadata: {}           # Optional. Arbitrary key-value notes, for example an AI agent session id to resume work with context: {session-id: "abc123"}.
deferred-from:         # Optional. The issue (as a quoted wikilink) or bookmark that deferred this work.
parent:                # Optional. The parent issue (as a quoted wikilink), if this issue is a sub-issue.
depends-on: []           # Optional. Issues (as quoted wikilinks) that must close before this one can start, for example `["[[faster-startup]]"]`.
remote:                # Optional. A URL: the GitHub issue or Jira ticket that tracks this issue outside the repo.
---

# Show what people watch and hear in the last 30 days

## Summary

Show what people watch and hear in the last 30 days: titles, watch time for each person, and top directors, studios, genres, artists and albums.

## Context

The human needs the last 30 days, not a full year. Prometheus and Loki keep 30 days, so this work needs no new database.

- `jellyfin-exporter` now reports `jellyfin_stream_playing` for each stream that is not paused. Each sample is 30 seconds of watch time.
- Director, studio and genre come from the Jellyfin item data. The metric uses the first value of each.
- Roon sends its plays to last.fm. `lastfm-exporter` reads the top artists, albums and tracks of the last month. It logs each new play, and Alloy sends the logs to Loki.
- Jellyfin logs `started playback of` for each play, so the plays panels have data from before this change.

## Acceptance criteria

- [x] Grafana provisions the Media Interest dashboard.
- [x] A test with the real Jellyfin 12.2 gives director, studio, genre, artist and album, and leaves out paused streams.
- [ ] After the deploy, the watch time panels have real data, including Watch time by person over time.
- [ ] The human sets `LASTFM_API_KEY` and `LASTFM_USER`, and the last.fm panels have real data.

## Out of scope

- Data for more than 30 days. This needs a database.
- Music for each person from Roon. last.fm has one account, and it does not show who listened.

## Notes

2026-11-02: From the human: show watch history and popularity for the last 30 days. A full year in review is not necessary. Roon already sends plays to last.fm.

2026-11-02: `lastfm-exporter` was tested with a stub that uses the documented response format, not with the real API, because no API key was available. A restart can log the last 100 plays again.

2026-11-02: This dashboard shows the watch history of each person to all Grafana users. Tailnet users can sign up as Viewers. See [[grafana-roles-from-tailscale]].

## Resolution
