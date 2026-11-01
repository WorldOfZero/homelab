---
title: "Collect logs and metrics for all homelab services"
state: in-progress     # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: high         # critical | high | medium | low
effort: medium         # small | medium | large | x-large
tags: [feature, grafana, observability] # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
created: 2026-11-01
closed:                # YYYY-MM-DD. Set this only when state is closed.
owner: claude          # The person or agent working on the issue. Cleared when the issue returns to open.
approver:              # The person or agent who accepts the issue when it closes.
bookmark: collect-all-telemetry # The jj bookmark of the work on the issue. Set this when work starts.
workspaces: [fable]    # jj workspaces where local work on the issue has happened, for example [fix-login-bug].
metadata: {}           # Optional. Arbitrary key-value notes, for example an AI agent session id to resume work with context: {session-id: "abc123"}.
deferred-from:         # Optional. The issue (as a quoted wikilink) or bookmark that deferred this work.
parent:                # Optional. The parent issue (as a quoted wikilink), if this issue is a sub-issue.
depends-on: []           # Optional. Issues (as quoted wikilinks) that must close before this one can start, for example `["[[faster-startup]]"]`.
remote:                # Optional. A URL: the GitHub issue or Jira ticket that tracks this issue outside the repo.
---

# Collect logs and metrics for all homelab services

## Summary

Collect logs and metrics for all containers on minerva, and for minerva itself. Keep the data across restarts, so that a human or an agent can debug problems from Grafana, Loki and Prometheus.

## Context

The debug work for the Roon "loading slow" errors needed host and container data at the time of each failure. That data was not available. The monitoring stack had these problems:

- Promtail sent logs only for containers with the `logging=promtail` label. Only the grafana, plex and fenrus stacks had this label. Promtail reached end of life on 2026-03-02.
- The Promtail `multiline` stage matched one timestamp format only, so it could merge lines of other formats.
- Prometheus and Loki kept their data in the container, so each recreate lost the data.
- cAdvisor did not have the containerd socket. In the test, its Docker factory failed without the socket, and it gave no metrics for each container.
- No job collected host metrics. The `docker` job scraped `localhost:9323` in the Prometheus container, and nothing listens there.
- The configuration files were in the repo, but the stack read copies on the host.

## Acceptance criteria

- [x] Alloy replaces Promtail, and it reads the logs of all containers with no label on the service.
- [x] Alloy reads the Roon log file.
- [x] node-exporter collects host metrics, and Prometheus scrapes it.
- [x] cAdvisor mounts the containerd socket.
- [x] Prometheus and Loki keep data in the `Fast/Telemetry` dataset, with a retention limit.
- [x] The test stack in the sandbox gives logs and metrics for containers that use sidecar networking, TTY mode, or many ports, with no duplicate log lines.
- [ ] After the deploy on minerva, all checks in the README of the stack pass.
- [ ] The human gives agent access to Grafana, Loki and Prometheus.

## Out of scope

- Application metrics. See [[add-app-metrics-exporters]].
- Grafana dashboards and alert rules.
- The `logging` and `stack` labels in the plex and fenrus stacks. They have no effect now. Remove them when those stacks change next.

## Notes

2026-11-01: The configuration is now inline in the compose file. This is the same method as the `ts-serve` configuration of the Tailscale sidecars, and it needs no copy to the host.

2026-11-01: The scrape interval changes from 5 seconds to 30 seconds for cAdvisor, to decrease the load on minerva. The Roon issue can come from host load.

2026-11-01: Test results from the sandbox, with a copy of the stack:

- Alloy sent logs for sidecar, TTY and many-port containers, and the Roon file. There were no duplicate log lines.
- After a recreate of Alloy, Loki and Prometheus, the data stayed, and Alloy did not send old lines again.
- A wrong containerd socket path stops the deploy with a clear error.

These items were not tested in the sandbox:

- The Grafana container, because the Docker disk was full. Its only change is the removal of two labels.
- ZFS and pressure metrics, because the sandbox has neither.
- The containerd socket path on minerva. The sandbox uses a different path.
- Loki deletion at the end of the retention period.
- The host `/` mount with `rslave` for node-exporter. The test used a plain read-only mount.

2026-11-01: From the human: keep the telemetry data in a separate ZFS dataset. The data is now in `Fast/Telemetry`, so the nightly replication of `Fast/Configuration` does not copy it. The dataset has a 100 GB quota, because Loki has no size limit of its own. The human must create the dataset in the TrueNAS web UI before the deploy, because TrueNAS must manage its datasets. The new paths were not tested in a running stack. The test used the old paths.

2026-11-01: From the human: agents get a Grafana token for Loki and Prometheus, which are both Grafana data sources. Thus the Loki port is removed. This closes the question about Loki exposure. The Prometheus port stays, because the human did not ask to remove it and it holds no logs.

2026-11-01: From the human: Grafana must have a Tailscale name. A sidecar now gives it the name `grafana`, and the LAN port 3001 stays. The grafana stack now needs `TS_AUTHKEY` in Portainer. The sidecar sets `TS_ACCEPT_DNS=false`, because Grafana finds Loki and Prometheus through Docker DNS.

## Resolution
