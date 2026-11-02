---
title: "Add disk health, ZFS scrub and replication metrics"
state: open            # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: medium       # critical | high | medium | low
effort: medium         # small | medium | large | x-large
tags: [feature, grafana, storage] # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
created: 2026-11-02
closed:                # YYYY-MM-DD. Set this only when state is closed.
owner:                 # The person or agent working on the issue. Cleared when the issue returns to open.
approver:              # The person or agent who accepts the issue when it closes.
bookmark:              # The jj bookmark of the work on the issue. Set this when work starts.
workspaces: []         # jj workspaces where local work on the issue has happened, for example [fix-login-bug].
metadata: {}           # Optional. Arbitrary key-value notes, for example an AI agent session id to resume work with context: {session-id: "abc123"}.
deferred-from: "[[add-operations-dashboards]]" # Optional. The issue (as a quoted wikilink) or bookmark that deferred this work.
parent:                # Optional. The parent issue (as a quoted wikilink), if this issue is a sub-issue.
depends-on: []           # Optional. Issues (as quoted wikilinks) that must close before this one can start, for example `["[[faster-startup]]"]`.
remote:                # Optional. A URL: the GitHub issue or Jira ticket that tracks this issue outside the repo.
---

# Add disk health, ZFS scrub and replication metrics

## Summary

Show disk health, ZFS scrub results and nightly replication on the storage dashboard.

## Context

node-exporter shows if a pool is online, but it does not show SMART data, ZFS checksum errors, scrub results, or the state of the replication to `Vault/Backups/Fast-Configuration`.

The Vault disks are single-disk RAID0 volumes behind a PERC H710, so `smartctl` must use its `megaraid` device type. A wrong setup can report nothing and look healthy. Check that the exporter reports each disk.

See [[add-operations-dashboards]].

## Acceptance criteria

- [ ] The dashboard shows SMART health and temperature for each disk, including the Vault disks.
- [ ] The dashboard shows the last scrub and ZFS errors for each pool.
- [ ] The dashboard shows the last successful replication, or Notes tells why this is not possible.

## Out of scope

- Alert rules.

## Notes

## Resolution
