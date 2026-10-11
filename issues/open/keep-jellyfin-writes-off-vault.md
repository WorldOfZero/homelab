---
title: "Keep Jellyfin metadata and trickplay writes off the Vault pool"
state: open            # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: medium       # critical | high | medium | low
effort: small          # small | medium | large | x-large
tags: [jellyfin, performance, storage] # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
created: 2026-10-11
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

# Keep Jellyfin metadata and trickplay writes off the Vault pool

## Summary

Make sure that Jellyfin saves artwork, NFO files and trickplay images under `/config` on the Fast pool, not next to the media on Vault. Writes to Vault wake the HDDs and are slow.

## Context

The `application` service mounts `/mnt/Vault/Media` at `/media` with `read_only: false` (commit d6f3dc2). Vault is 12 HDDs in RAIDZ2 behind a PERC H710 controller. Each write to Vault touches a wide vdev.

Three Jellyfin settings can write next to the media:

- Library -> Manage library -> "Save artwork into media folders".
- Library -> Manage library -> metadata savers (NFO).
- Library -> Manage library -> "Save trickplay images next to media".

When these settings are off, Jellyfin keeps the data under `/config/metadata` and `/config/data`, on the Fast NVMe pool. The nightly replication task copies them to `Vault/Backups/Fast-Configuration` in one sequential stream.

Do the check for each library (Movies, Shows, Music, Audiobooks).

## Acceptance criteria

- [ ] Each library has the three settings recorded in Notes.
- [ ] The settings are off, or Notes tells why a library must keep files next to the media. For example, another tool reads the NFO files.
- [ ] If no setting needs write access, the `/media` mount is changed to `read_only: true`, and a test scan still works.

## Out of scope

- Moving the trickplay images that exist now. Jellyfin does not move them by itself. Create a new issue if they use a large amount of space.

## Notes

## Resolution
