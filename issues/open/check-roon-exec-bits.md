---
title: "Check the Roon config for files that lost the exec bit"
state: open            # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: low          # critical | high | medium | low
effort: small          # small | medium | large | x-large
tags: [roon, storage]  # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
created: 2026-10-21
closed:                # YYYY-MM-DD. Set this only when state is closed.
owner:                 # The person or agent working on the issue. Cleared when the issue returns to open.
approver:              # The person or agent who accepts the issue when it closes.
bookmark:              # The jj bookmark of the work on the issue. Set this when work starts.
workspaces: []         # jj workspaces where local work on the issue has happened, for example [fix-login-bug].
metadata: {}           # Optional. Arbitrary key-value notes, for example an AI agent session id to resume work with context: {session-id: "abc123"}.
deferred-from: "[[diagnose-roon-disconnects]]" # Optional. The issue (as a quoted wikilink) or bookmark that deferred this work.
parent:                # Optional. The parent issue (as a quoted wikilink), if this issue is a sub-issue.
depends-on: []           # Optional. Issues (as quoted wikilinks) that must close before this one can start, for example `["[[faster-startup]]"]`.
remote:                # Optional. A URL: the GitHub issue or Jira ticket that tracks this issue outside the repo.
---

# Check the Roon config for files that lost the exec bit

## Summary

Find and fix files under `/mnt/Fast/Configuration/roon` that lost their exec bit or owner in the Fast pool migration. A file with the wrong mode can stop RoonServer again after an update.

## Context

The 2026-10-20 Roon logs showed `/app/RoonServer/start.sh: Permission denied` many times. The `Vault/Configuration` to `Fast/Configuration` migration lost permissions on some files (see `FAST-CONFIGURATION-MIGRATION.md`). The RoonServer wrapper downloaded the package again, and this fixed the files under `/app/RoonServer`. Other files under `/mnt/Fast/Configuration/roon` can still have the wrong mode.

Check on minerva:

```bash
sudo find /mnt/Fast/Configuration/roon -name "*.sh" ! -perm -u+x
sudo find /mnt/Fast/Configuration/roon ! -user 0 ! -user 1000 | head
```

Compare the result with a fresh RoonServer package if you are not sure which mode a file needs. See [[diagnose-roon-disconnects]].

## Acceptance criteria

- [ ] Notes records the output of the check commands.
- [ ] Each file with a wrong mode or owner is fixed, or Notes tells why it is correct.

## Out of scope

- The network configuration of Roon. See [[diagnose-roon-disconnects]].

## Notes


## Resolution

