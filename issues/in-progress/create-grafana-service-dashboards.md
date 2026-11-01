---
title: "Create Grafana dashboards for container health and the media stack"
state: in-progress     # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: medium       # critical | high | medium | low
effort: medium         # small | medium | large | x-large
tags: [feature, grafana, observability] # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
created: 2026-11-01
closed:                # YYYY-MM-DD. Set this only when state is closed.
owner: claude          # The person or agent working on the issue. Cleared when the issue returns to open.
approver:              # The person or agent who accepts the issue when it closes.
bookmark: grafana-dashboards # The jj bookmark of the work on the issue. Set this when work starts.
workspaces: [fable]    # jj workspaces where local work on the issue has happened, for example [fix-login-bug].
metadata: {}           # Optional. Arbitrary key-value notes, for example an AI agent session id to resume work with context: {session-id: "abc123"}.
deferred-from:         # Optional. The issue (as a quoted wikilink) or bookmark that deferred this work.
parent:                # Optional. The parent issue (as a quoted wikilink), if this issue is a sub-issue.
depends-on: []           # Optional. Issues (as quoted wikilinks) that must close before this one can start, for example `["[[faster-startup]]"]`.
remote:                # Optional. A URL: the GitHub issue or Jira ticket that tracks this issue outside the repo.
---

# Create Grafana dashboards for container health and the media stack

## Summary

Provision Grafana dashboards for container health and for the media stack, and collect the data that they need.

## Context

The human asked for a dashboard of container health and general telemetry, and for a dashboard of the Jellyfin and arr stack. This work depends on [[collect-all-homelab-telemetry]]. cAdvisor does not report Docker health, restart counts, or OOM kills. Jellyfin and the arr applications had no metrics in Prometheus.

## Acceptance criteria

- [x] Grafana provisions the Container Health and Media Stack dashboards in the Homelab folder.
- [x] `docker-state-exporter` reports state, health, restarts, OOM kills and exit code for each container.
- [x] Prometheus scrapes Sonarr, Radarr, Bazarr and Jellyfin metrics.
- [x] A Grafana Viewer token runs all panel queries with no errors in the sandbox.
- [ ] After the deploy on minerva, all targets show `up`, and the host panels show data.

## Out of scope

- Metrics for other applications. See [[add-app-metrics-exporters]].
- Alert rules.

## Notes

2026-11-01: Test results from the sandbox:

- Sonarr 4.0.20 with exportarr 2.3.0, and Jellyfin 12.2, ran as real applications.
- A real HLS transcode in Jellyfin showed `jellyfin_streams{method="Transcode"} 1`.
- A Viewer service account token ran all 79 panel queries with no errors. A push to Loki through the Grafana proxy with this token returned 403.
- Both dashboards were rendered and examined in a browser.

These items were not tested:

- Radarr, because it did not start in the sandbox. Its panels used a stub with metric names from the exportarr source.
- Bazarr. Its panels used a stub with metric names from the exportarr source.
- Grafana 13.2.3. The test used Grafana 13.1.1, because the Docker disk was full.
- Host pressure, ZFS, `eno1` and pool panels. The sandbox has no such data.
- Per-container disk panels for the media containers had no data in the test. cAdvisor can also report little disk IO on ZFS. Check these panels on minerva.

The dashboards select the data sources with variables, so the panels do not depend on a data source UID.

## Resolution
