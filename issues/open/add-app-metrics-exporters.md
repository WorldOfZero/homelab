---
title: "Scrape application metrics from homelab services"
state: open            # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: medium       # critical | high | medium | low
effort: large          # small | medium | large | x-large
tags: [feature, grafana, observability] # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
created: 2026-11-01
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

# Scrape application metrics from homelab services

## Summary

Scrape the metrics of the applications on minerva. [[collect-all-homelab-telemetry]] gives logs, container metrics and host metrics, but not the internal metrics of each application.

## Context

Prometheus must have a network path to each target. Most stacks use a Tailscale sidecar that joins the external `tailnet-local` network, so Prometheus can join that network too. Apps with `network_mode: service:tailscale` are then available at the address of the sidecar.

Candidates. Check each item in the current documentation of the application before you start:

| Service | Method | Needs |
|---|---|---|
| plex | The `plex-prometheus` exporter already runs, and nothing scrapes it | A network path |
| minecraft | The `prometheus-exporter` mod is already installed | A network path, and the port of the mod |
| tailscale | `TS_ENABLE_METRICS` is on, on host networking | The port of the metrics endpoint |
| jellyfin | A built-in metrics endpoint | A setting in Jellyfin |
| caddy | A built-in metrics endpoint | A configuration change |
| tandoor | A built-in metrics endpoint | An environment variable |
| kuma | A built-in metrics endpoint | An API key |
| karakeep | A built-in metrics endpoint | A token |
| vault | A built-in metrics endpoint | A token, and a configuration change |
| sonarr, radarr, bazarr | An `exportarr` sidecar | The API key of each service |
| postgres (tandoor, airtrail) | A `postgres_exporter` sidecar | Database credentials |
| NVIDIA GPU | An exporter container | GPU access |
| Disk health | A SMART exporter container | Disk access |

Roon, ollama, factorio and other services can have no metrics endpoint. For those services, container metrics and logs are the data source.

## Acceptance criteria

- [ ] Each candidate is scraped, or Notes tells why not.
- [ ] Each new secret is listed in `ENVIRONMENT.md`.
- [ ] Each target shows `up` in Prometheus.

## Out of scope

- Grafana dashboards and alert rules.

## Notes

## Resolution
