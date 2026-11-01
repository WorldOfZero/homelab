---
title: "Add streaming problem panels and a Roon dashboard"
state: in-progress     # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: high         # critical | high | medium | low
effort: medium         # small | medium | large | x-large
tags: [feature, grafana, roon, jellyfin] # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
created: 2026-11-01
closed:                # YYYY-MM-DD. Set this only when state is closed.
owner: claude          # The person or agent working on the issue. Cleared when the issue returns to open.
approver:              # The person or agent who accepts the issue when it closes.
bookmark: streaming-dashboards # The jj bookmark of the work on the issue. Set this when work starts.
workspaces: [fable]    # jj workspaces where local work on the issue has happened, for example [fix-login-bug].
metadata: {}           # Optional. Arbitrary key-value notes, for example an AI agent session id to resume work with context: {session-id: "abc123"}.
deferred-from:         # Optional. The issue (as a quoted wikilink) or bookmark that deferred this work.
parent:                # Optional. The parent issue (as a quoted wikilink), if this issue is a sub-issue.
depends-on: []           # Optional. Issues (as quoted wikilinks) that must close before this one can start, for example `["[[faster-startup]]"]`.
remote:                # Optional. A URL: the GitHub issue or Jira ticket that tracks this issue outside the repo.
---

# Add streaming problem panels and a Roon dashboard

## Summary

Make problems with Jellyfin streams easy to find on the Media Stack dashboard, and add a Roon dashboard. Roon has caused many problems. See [[diagnose-roon-disconnects]].

## Context

Roon has no metrics, so the Roon dashboard uses its log file, its container output, cAdvisor and host metrics. `jellyfin-exporter` now also reports each stream. See [[create-grafana-service-dashboards]].

## Acceptance criteria

- [x] The Roon dashboard shows core starts, stream problems, endpoint drops, errors, core resources and host load.
- [x] The Media Stack dashboard shows each stream, its buffer and speed, playback errors and host load.
- [x] Alloy uses the time in the Roon log line, not the time that Alloy read the line.
- [x] All queries run through the live Grafana with no errors.
- [ ] After the deploy, `jellyfin_stream_info` has data during playback.
- [ ] The next Roon stream problem is visible on the dashboard at the correct time.

## Out of scope

- Grafana alert rules.
- A fix for the causes that the dashboards show.

## Notes

2026-11-01: From the human: expand the media dashboard to find streaming problems, and add a Roon dashboard.

2026-11-01: The Roon log patterns come from the live logs: `Track Stopped Due to`, `StoppedLostEndpoint`, `poor connection`, `too much time locked`, `=> Disconnected`, `Critical:`. `media_slow` and `NetworkUnreachable` come from [[disable-roon-ipv6]]. They were not in the current log. `Slow HTTP Response` is a string from the Jellyfin binaries. It was not in the current log.

2026-11-01: The Roon container started on 2026-10-26, and its restart count is 0. Its output shows a second core start on 2026-10-27 at 20:37 UTC, after `ps: command not found`. Thus the core restarts in the container, and Docker metrics do not show this. Use the Core starts panel.

2026-11-01: Lines that Alloy read before this change have the time that Alloy read them. Their time on the dashboard is wrong, and new lines are correct.

2026-11-01: The tests used the real Jellyfin 12.2 with a real transcode, and real data through a Viewer token. A stub gave the Now Playing rows in the render, so that the low buffer state was visible. A real slow transcode was not tested. Jellyfin reports transcode speed and completion only while ffmpeg runs.

## Resolution
