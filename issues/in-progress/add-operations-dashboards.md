---
title: "Add overview, security, storage, GPU and network dashboards"
state: in-progress     # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: high         # critical | high | medium | low
effort: medium         # small | medium | large | x-large
tags: [feature, grafana, security] # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
created: 2026-11-02
closed:                # YYYY-MM-DD. Set this only when state is closed.
owner: claude          # The person or agent working on the issue. Cleared when the issue returns to open.
approver:              # The person or agent who accepts the issue when it closes.
bookmark: operations-dashboards # The jj bookmark of the work on the issue. Set this when work starts.
workspaces: [fable]    # jj workspaces where local work on the issue has happened, for example [fix-login-bug].
metadata: {}           # Optional. Arbitrary key-value notes, for example an AI agent session id to resume work with context: {session-id: "abc123"}.
deferred-from:         # Optional. The issue (as a quoted wikilink) or bookmark that deferred this work.
parent:                # Optional. The parent issue (as a quoted wikilink), if this issue is a sub-issue.
depends-on: []           # Optional. Issues (as quoted wikilinks) that must close before this one can start, for example `["[[faster-startup]]"]`.
remote:                # Optional. A URL: the GitHub issue or Jira ticket that tracks this issue outside the repo.
---

# Add overview, security, storage, GPU and network dashboards

## Summary

Add overview, security, storage and backups, GPU and Ollama, and network dashboards.

## Context

The Plex compromise ran for days and nobody saw it. The dashboards show the signs of such a problem. Most data exists already. An NVIDIA exporter adds GPU metrics, and the probes now include Ollama.

## Acceptance criteria

- [x] Grafana provisions the five dashboards.
- [ ] After the deploy, the NVIDIA exporter shows GPU memory. This exporter was not tested on a real GPU.
- [ ] The overview shows a real problem correctly.
- [x] Media Stack, GPU and Network show stream events as marks.
- [x] Media Stack has a Group playback row for SyncPlay.
- [ ] After the deploy, `jellyfin_stream_position_seconds` has data, and Position gap shows a value in a watch party.
- [ ] The `flights-tandoor` and `karakeep-kavita` dashboards are gone from Grafana.

## Out of scope

- Disk health and scrub results. See [[add-disk-health-metrics]].
- UniFi client details that need the UniFi API.

## Notes

2026-11-02: From the human: add these five dashboards.

2026-11-02: UniFi logged IDS events on ports 8999 and 1080 to `192.168.1.43` with `act=allowed`, after the human removed port forwards. Nothing answered. Check if the `qbt` forward still exists.

2026-11-02: From the human: add alerts for unhealthy containers, crash loops, old backups, full disks and high CPU. The file `alerting/rules.yaml` adds them. Free space is used, because a percentage for one ZFS dataset is misleading. `/mnt/Vault/Media` shows 0.1% used.

2026-11-02: From the human: qBittorrent uses port 1080 because it runs through NordVPN.

2026-11-02: From the human: show Jellyfin stream events as marks on the other streaming panels, and add panels to debug group playback.

2026-11-02: The 2026-10-29 SyncPlay logs have 16 changes from Playing to Waiting and 18 Buffer requests. Session `cee8d58f` made 10 of the 18 requests. The logs do not show the cause.

2026-11-02: `/SyncPlay/List` metrics are not in the exporter. The exporter uses an API key, and the list was not tested with an API key. The logs and session positions give the same signals.

2026-11-02: Live panels of `tandoor` and `karakeep` match commit `c0a3335e`, which removed the two old dashboard files, but Grafana still lists the old dashboards as provisioned. The cause is not known. Deletion worked in a test on Grafana 13.1.1. Minerva runs 13.2.3, which was not tested because the sandbox could not get the image.

## Resolution
