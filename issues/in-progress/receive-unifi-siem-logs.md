---
title: "Receive UniFi SIEM logs in Loki"
state: in-progress     # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: medium       # critical | high | medium | low
effort: small          # small | medium | large | x-large
tags: [feature, grafana, security] # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
created: 2026-11-02
closed:                # YYYY-MM-DD. Set this only when state is closed.
owner: claude          # The person or agent working on the issue. Cleared when the issue returns to open.
approver:              # The person or agent who accepts the issue when it closes.
bookmark: unifi-siem-logs # The jj bookmark of the work on the issue. Set this when work starts.
workspaces: [fable]    # jj workspaces where local work on the issue has happened, for example [fix-login-bug].
metadata: {}           # Optional. Arbitrary key-value notes, for example an AI agent session id to resume work with context: {session-id: "abc123"}.
deferred-from:         # Optional. The issue (as a quoted wikilink) or bookmark that deferred this work.
parent:                # Optional. The parent issue (as a quoted wikilink), if this issue is a sub-issue.
depends-on: []           # Optional. Issues (as quoted wikilinks) that must close before this one can start, for example `["[[faster-startup]]"]`.
remote:                # Optional. A URL: the GitHub issue or Jira ticket that tracks this issue outside the repo.
---

# Receive UniFi SIEM logs in Loki

## Summary

Send UniFi SIEM logs to Loki, so that blocked traffic and gateway events can be searched with the other homelab logs.

## Context

The human blocked addresses from the Plex compromise in UniFi, and wants to see blocked attempts. Alloy now receives syslog on port 1514, on UDP and TCP, and sends the lines to Loki.

Reports say that UniFi sends CEF headers without the full CEF structure, and that its timestamps change between versions. Thus the listener uses the `raw` format, and Loki uses the time that Alloy receives each line. The `raw` format needs `--stability.level=experimental` on Alloy.

## Acceptance criteria

- [x] Alloy receives syslog on UDP and TCP, and adds a `product` label from the CEF header.
- [x] A test with sample lines keeps all lines. In the same test, `rfc3164` dropped a line with no syslog header.
- [ ] After the deploy, `{service="unifi-siem"}` in Loki has real UniFi lines.
- [ ] A rule with logging on gives a line for blocked traffic.

## Out of scope

- A UniFi dashboard.
- Parsing the CEF fields into separate labels. Source and destination addresses have too many values for labels.

## Notes

2026-11-02: From the human: add a syslog receiver for the UniFi SIEM logs.

2026-11-02: The sample lines were written from public descriptions of the format, not from this gateway. Check the real lines after the deploy. The test sent lines to Alloy with `loki.echo`, not to a real Loki.

2026-11-02: Port 1514 has no authentication, so a LAN device can send false lines. Do not forward this port from the internet.

## Resolution
