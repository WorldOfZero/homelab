---
title: "Turn off IPv6 in the Roon container so Qobuz streams work"
state: in-progress     # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: high         # critical | high | medium | low
effort: small          # small | medium | large | x-large
tags: [bug, roon]      # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
created: 2026-10-22
closed:                # YYYY-MM-DD. Set this only when state is closed.
owner: claude          # The person or agent working on the issue. Cleared when the issue returns to open.
approver:              # The person or agent who accepts the issue when it closes.
bookmark: roon-disable-ipv6 # The jj bookmark of the work on the issue. Set this when work starts.
workspaces: [fable]    # jj workspaces where local work on the issue has happened, for example [fix-login-bug].
metadata: {}           # Optional. Arbitrary key-value notes, for example an AI agent session id to resume work with context: {session-id: "abc123"}.
deferred-from:         # Optional. The issue (as a quoted wikilink) or bookmark that deferred this work.
parent:                # Optional. The parent issue (as a quoted wikilink), if this issue is a sub-issue.
depends-on: []           # Optional. Issues (as quoted wikilinks) that must close before this one can start, for example `["[[faster-startup]]"]`.
remote:                # Optional. A URL: the GitHub issue or Jira ticket that tracks this issue outside the repo.
---

# Turn off IPv6 in the Roon container so Qobuz streams work

## Summary

Turn off IPv6 in the Roon container. The macvlan network has only IPv4, and Roon fails on IPv6 addresses instead of using IPv4, so Qobuz streams stop.

## Context

Since the move to a macvlan network (see [[diagnose-roon-disconnects]]), Qobuz tracks stop with `qobuz_media_slow`. The RoonServer log shows the cause:

```
Warn: [easyhttp] GET https://streaming-qobuz-std.akamaized.net/... socketerr (NetworkUnreachable): Network is unreachable ([2600:1406:2e00:1c::1743:2155]:443)
```

The macvlan network `roon-lan` has only an IPv4 subnet. Roon gets IPv6 addresses for Qobuz, tries them, fails at once, and retries the same address. It does not try IPv4. The fix turns IPv6 off in the container with `sysctls`, so Roon gets and uses only IPv4 addresses.

## Acceptance criteria

- [x] `services/roon/docker-compose.yaml` sets `net.ipv6.conf.all.disable_ipv6` and `net.ipv6.conf.default.disable_ipv6` to `1`.
- [ ] After the deploy, `sudo docker exec roonserver cat /proc/sys/net/ipv6/conf/all/disable_ipv6` prints `1`.
- [ ] Qobuz tracks play, and the Roon log shows no new `NetworkUnreachable` errors.

## Out of scope

- IPv6 on the macvlan network. That needs an IPv6 subnet from the ISP prefix.
- Dropouts on the DAC zone. Those came from the network driver of HESTIA, not from the Roon container.

## Notes


## Resolution

