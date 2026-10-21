---
title: "Stop Jellyfin from parsing game disc images as video ISOs"
state: open            # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: low          # critical | high | medium | low
effort: small          # small | medium | large | x-large
tags: [jellyfin, bug, storage] # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
created: 2026-10-20
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

# Stop Jellyfin from parsing game disc images as video ISOs

## Summary

Every library scan tries to open `.IMG` and `.iso` files under `/media/Games` as DVD/Blu-ray
UDF images and throws `InvalidDataException: Stream is not a recognized UDF format` for each
one. Exclude the disc images from the scan so the errors and the wasted Vault HDD reads stop.

## Context

The 2026-10-20 server log shows `MovieResolver: Error opening UDF/ISO image` for files like
`/media/Games/DOS/DOSBOX_ARENA/TITLE.IMG` and
`/media/Games/Xbox/JSRF - Jet Set Radio Future (Europe).iso` during the 10:13 library scan.
Each file was opened twice within seconds. These are DOS floppy images and Xbox game ISOs,
not video discs, so the UDF reader can never parse them.

`/media/Games` is a Moonfin game library. Per the
[Moonfin Retro Games wiki](https://github.com/Moonfin-Client/Moonfin-Core/wiki/Retro-Games),
a game library is a Jellyfin **Mixed Content** library that the Moonbase plugin flags (or
auto-detects by a name containing "game"/"rom"/"emulat"). A Mixed Content library runs the
core movie/video resolvers, so every `.img`/`.iso` gets probed as a potential DVD/Blu-ray
rip. Each probe opens the file on the Vault HDDs, which wakes the disks and adds scan time,
and the failures spam the log at ERR level on every scan. This is inherent to how Moonfin
piggybacks on Jellyfin libraries, not a misconfiguration.

The wiki documents only `.zip` and `.7z` ROM archives as supported formats — the plugin
unpacks the archive and sends the raw ROM to the client. Raw disc images (`.iso`, `.img`)
are not in the documented pipeline, so the Xbox ISO and the loose DOS floppy images are
probably not playable through Moonfin as they sit today anyway.

Options, roughly in order of preference:

- A: Repackage the DOS games as `.zip` archives (the format Moonfin documents). Files inside
  an archive are not probed by the video resolvers, so the errors stop and the games may
  actually become playable in Moonfin.
- B: For images Moonfin cannot play anyway (for example Xbox ISOs — no in-client Xbox
  emulator exists), move them out of `/media/Games` or into a subfolder with an empty
  `.ignore` file. Verify first that an `.ignore` file does not also hide sibling content
  from Moonfin's scan hook — the plugin picks up ROMs during the Jellyfin library refresh,
  and it is unconfirmed whether it walks ignored directories.
- C: Report upstream to Moonfin (Moonbase plugin): game libraries should suppress the core
  disc-image probing, or document the expected layout for disc-based systems.

## Acceptance criteria

- [ ] A full library scan completes with no `Error opening UDF/ISO image` entries in the log.
- [ ] The DOS games and the Xbox ISO are still visible in Moonfin, or Notes tells why they
      were removed from the library.
- [ ] The chosen option is recorded in Notes.

## Out of scope

- Scan scheduling and library monitoring. See [[tune-jellyfin-scheduled-tasks]].

## Notes

2026-10-20: The human confirmed `/media/Games` is a Moonfin game library. Context updated to
match; the earlier "find out which library" step is resolved.

2026-10-20: Fix applied by the human: the unzipped DOS games were removed from the library,
and `/media/Games/Xbox` got an empty `.ignore` file (option B — the Xbox ISO is not playable
through Moonfin anyway, so hiding it from the scan is acceptable). Remaining verification:
run a full library scan and confirm the log has no `Error opening UDF/ISO image` entries,
and confirm the DOS games that stayed (zipped ones, if any) still appear in Moonfin.

## Resolution
