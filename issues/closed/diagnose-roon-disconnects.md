---
title: "Diagnose Roon disconnects and playback dropouts"
state: closed          # open | in-progress | closed. Must match the directory of the file.
resolution: completed  # completed | abandoned. Set this only when state is closed.
priority: medium       # critical | high | medium | low
effort: small          # small | medium | large | x-large
tags: [bug, roon, performance] # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
created: 2026-10-20
closed: 2026-10-21     # YYYY-MM-DD. Set this only when state is closed.
owner: claude          # The person or agent working on the issue. Cleared when the issue returns to open.
approver:              # The person or agent who accepts the issue when it closes.
bookmark: roon-macvlan # The jj bookmark of the work on the issue. Set this when work starts.
workspaces: [fable]    # jj workspaces where local work on the issue has happened, for example [fix-login-bug].
metadata: {}           # Optional. Arbitrary key-value notes, for example an AI agent session id to resume work with context: {session-id: "abc123"}.
deferred-from:         # Optional. The issue (as a quoted wikilink) or bookmark that deferred this work.
parent:                # Optional. The parent issue (as a quoted wikilink), if this issue is a sub-issue.
depends-on: []           # Optional. Issues (as quoted wikilinks) that must close before this one can start, for example `["[[faster-startup]]"]`.
remote:                # Optional. A URL: the GitHub issue or Jira ticket that tracks this issue outside the repo.
---

# Diagnose Roon disconnects and playback dropouts

## Summary

Roon struggles and disconnects (reported 2026-10-20). Find out whether the core process is
restarting, the host is under memory or IO pressure, or the Vault HDDs stall playback, then
fix the confirmed cause.

## Context

The deployment in `services/roon/docker-compose.yaml` is sound: `network_mode: host` (so
RAAT and discovery work), the Roon database on `/mnt/Fast/Configuration/roon` (NVMe — the
reason the Fast pool exists), music on `/mnt/Vault/Media/Music` (HDDs). The container has
no memory limit and no healthcheck.

Hypotheses, most likely first:

1. **The core process restarts or gets OOM-killed.** Roon Core on Linux grows its memory
   use over days, and minerva also runs Jellyfin, Ollama and ~40 other containers with no
   limits. A core restart disconnects every remote at once while the container looks fine
   (`restart: unless-stopped` hides it). Check:
   ```bash
   sudo docker inspect roonserver --format '{{.State.StartedAt}} restarts={{.RestartCount}} oom={{.State.OOMKilled}}'
   sudo dmesg -T | grep -i -E 'oom|killed process'
   sudo docker events --since 48h --filter type=container | grep -i roon
   ```
2. **Vault HDD contention or spin-up stalls.** Music streams from the same 12 HDDs that
   the Jellyfin library scans and trickplay hammer, and the scans run at bad times (see
   [[tune-jellyfin-scheduled-tasks]] — the 2026-10-20 scan ran at 10:13 during playback).
   Symptom shape: tracks stutter or stop mid-song, remotes stay connected. Correlate
   dropout times with the Jellyfin task log and `zpool iostat Vault 5`.
3. **Network path of a specific endpoint.** If only one zone or one remote drops while
   others stay up, it is that device or its WiFi, not the core.

Roon's own logs name the reason for most disconnects:
`/mnt/Fast/Configuration/roon/data/RoonServer/Logs/RoonServer_log*.txt` (and
`RAATServer` logs next to it). The Docker log retention was raised to 10 MB x 3 on
2026-10-20 ([[raise-container-log-retention]]) but only applies after the stack is
redeployed.

## Acceptance criteria

- [ ] Notes records container start time, restart count, and OOMKilled at the time of a
      reported disconnect.
- [x] Notes records what the RoonServer log says around at least one disconnect.
- [x] The confirmed cause has a fix applied or a follow-up issue.
- [ ] If the cause is memory pressure, the compose file gets an explicit `mem_limit` (with
      headroom — Roon needs several GB with a large library) or the host gets the memory
      hog constrained, and a week passes without a disconnect.

## Out of scope

- Jellyfin scan scheduling. See [[tune-jellyfin-scheduled-tasks]].

## Notes

2026-10-20: Container logs from the human confirm a **crash loop**, not memory pressure or
HDD contention. Three findings:

1. **The crash:** `Unhandled exception. System.ArgumentException: An invalid IP address was
   specified` in `LinuxNetworkInterface.GetLinuxNetworkInterfaces()`, fired from
   `NetworkChange.OnAvailabilityTimerFired`. This is dotnet/runtime#49515: .NET's interface
   enumeration can read a garbage/zero address (the linked fix, PR #130093 "Handle
   if_nametoindex failure in EnumerateInterfaceAddresses", only landed July 2026), and the
   unhandled exception kills the whole process. Roon ships its own (older) .NET runtime, so
   the fix cannot be applied server-side. With `network_mode: host` on a box running ~40
   containers, Roon's runtime enumerates every Docker veth, and interfaces vanishing
   mid-enumeration (container restarts) trigger the race. Each crash = all remotes
   disconnect, `restart: unless-stopped` brings it back, repeat.
2. **`/app/RoonServer/start.sh: Permission denied`** (repeated), after which the wrapper
   re-downloaded the 108 MB RoonServer package. This is the exec-bit loss from the
   `Vault/Configuration` -> `Fast/Configuration` migration (predicted in
   FAST-CONFIGURATION-MIGRATION.md) surfacing in `/app`. The re-download restores correct
   permissions for the downloaded tree, but check `/mnt/Fast/Configuration/roon` for other
   files that lost exec bits.
3. **`ps: command not found`** in the RoonServer wrapper script: the `debian-12-slim` image
   lacks `procps`, so Roon's own process supervision ("Not responding" handling) cannot
   inspect or kill stale processes.

Candidate fixes for (1), strongest first:

- **macvlan network** instead of `network_mode: host`: give Roon its own LAN IP on a
  macvlan network (`docker network create -d macvlan --subnet=<LAN> --gateway=<gw>
  -o parent=<nic> roon-lan`). Multicast discovery and RAAT still work (macvlan is L2 on
  the LAN) and the container sees only its own eth0 + lo — no veth churn, no race.
  Caveat: the host itself cannot reach a macvlan container directly; irrelevant for Roon
  since clients are other LAN devices and music arrives via bind mount.
- Reduce veth churn (find and fix whatever container restarts frequently) — treats the
  symptom only.

For (3): switch to a non-slim image tag or derive an image that adds `procps`.

2026-10-20 (later): Macvlan fix implemented in `services/roon/docker-compose.yaml`: the
service now joins a compose-managed `roon-lan` macvlan network with a static IP instead of
`network_mode: host`. The four network values come from `services/roon/stack.env`; the
compose file fails the deploy with a named error while `ROON_MACVLAN_PARENT` (minerva's LAN
NIC) or `ROON_MACVLAN_IP` (a free LAN address outside DHCP) is unset, so it cannot deploy
with silently wrong values. Subnet/gateway pre-filled as 192.168.1.0/24 / 192.168.1.1
(inferred from the Prometheus scrape target — verify). `services/roon/README.md` documents
the why, the deploy steps, and the host-cannot-reach-macvlan caveat. Validated with
`docker compose config` both with and without values. Not yet deployed; Roon remotes must
reconnect to the new IP once after the switch.

2026-10-21: `ip route get 192.168.1.1` on minerva gives `dev eno1 src 192.168.1.43`.
`ROON_MACVLAN_PARENT` is now `eno1` in `stack.env`. The output confirms the subnet
192.168.1.0/24. `ROON_MACVLAN_IP` is still empty: select a free address outside the DHCP
range of the router.

2026-10-21: `ROON_MACVLAN_IP` is now `192.168.1.212`. The compose file pins the MAC of the
container to `02:52:4f:4f:4e:01`, so UniFi tracks one client across container recreates. The
MAC does not depend on the IP address. `services/roon/README.md` gives the UniFi steps. Before
the deploy, make sure that the UniFi DHCP range does not include `.212`, and that no device
uses it. After the deploy, set a Fixed IP Address for the client. A MAC address per network
needs Docker Engine 25 or later on minerva.

2026-10-21: The first deploy from Portainer failed: `required variable ROON_MACVLAN_IP is
missing a value`. Portainer does not read `services/roon/stack.env`. Each stack gets its
variables from the "Environment variables" field of Portainer (see `ENVIRONMENT.md`), and
Docker Compose does not read a file with that name. The four network values are not secret,
so the compose file now contains them, and `stack.env` is removed. Portainer needs no
variables for this stack.

2026-10-21: The macvlan stack is deployed. UniFi shows the container at `192.168.1.212` with
MAC `02:52:4f:4f:4e:01`. The human reports that Roon is much more stable.

The first criterion is not recorded. The container log showed the crash and its stack trace
directly, so the start time and restart count were not necessary to find the cause. The fourth
criterion does not apply, because the cause was not memory pressure.

## Resolution

Completed. RoonServer crashed in a loop with `An invalid IP address was specified`
(dotnet/runtime#49515). Its bundled .NET runtime failed while it read the host network
interfaces, which Docker veth interfaces change all the time. Each crash disconnected all Roon
remotes.

Roon now runs on a macvlan network on `eno1` at `192.168.1.212`, with a fixed MAC, so it sees
only its own interface. The values are in `services/roon/docker-compose.yaml`, and
`services/roon/README.md` gives the UniFi steps. After the deploy, the human reports that Roon
is much more stable.

Two smaller findings from the same logs have their own issues: [[check-roon-exec-bits]] and
[[use-roon-image-with-ps]].
