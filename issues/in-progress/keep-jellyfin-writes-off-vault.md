---
title: "Keep Jellyfin metadata and trickplay writes off the Vault pool"
state: in-progress     # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: medium       # critical | high | medium | low
effort: small          # small | medium | large | x-large
tags: [jellyfin, performance, storage] # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
created: 2026-10-11
closed:                # YYYY-MM-DD. Set this only when state is closed.
owner: claude          # The person or agent working on the issue. Cleared when the issue returns to open.
approver:              # The person or agent who accepts the issue when it closes.
bookmark: jellyfin-reliability # The jj bookmark of the work on the issue. Set this when work starts.
workspaces: [fable]    # jj workspaces where local work on the issue has happened, for example [fix-login-bug].
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

- [x] Each library has the three settings recorded in Notes.
- [x] The settings are off, or Notes tells why a library must keep files next to the media. For example, another tool reads the NFO files.
- [ ] If no setting needs write access, the `/media` mount is changed to `read_only: true`, and a test scan still works.

## Out of scope

- Moving the trickplay images that exist now. Jellyfin does not move them by itself. Create a new issue if they use a large amount of space.

## Notes

2026-10-21: The compose file now mounts `/media` with `read_only: true`, in the `jellyfin-reliability` change. This change comes before the settings check of the first two criteria, so do the check before the redeploy. Two more settings write next to the media, so the check now covers five settings, not three: `SaveSubtitlesWithMedia` (on by default) and `SaveLyricsWithMedia`. `services/jellyfin/README.md` lists the five `options.xml` keys and gives one command that shows them for all libraries.

If a setting is on, Jellyfin does not stop. The write fails, and the log shows an error such as `Read-only file system` or `UnauthorizedAccessException`. Turn the setting off, or record in Notes why the library needs write access.

To do on minerva:

1. Before the redeploy, run the check command from the README. Record the output here.
2. After the redeploy, run a library scan. Check the log for `Read-only file system` errors.
3. Check that the Moonfin game library still shows its box art. The Moonbase plugin reconciles artwork after each scan. Its documentation does not tell where it writes. If it writes next to the ROMs, it fails now.

Existing trickplay images and artwork next to the media stay readable. Only new writes are blocked.

2026-10-21: The check command output from minerva. A key that is not in the file has its default value, which is off.

| Library | `SaveLocalMetadata` | `MetadataSavers` | `SaveTrickplayWithMedia` | `SaveSubtitlesWithMedia` |
|---|---|---|---|---|
| Movies | true | not empty | true | true |
| Shows | false | not empty | true | true |
| Books | true | empty | off (default) | true |
| Games | false | empty | off (default) | true |
| Music | false | empty | off (default) | true |
| Collections | true | (no key) | off (default) | true |

`SaveLyricsWithMedia` is off (default) for each library. The Collections library is under `/config/data/collections`, not under `/media`, so its settings do not write to Vault.

Do not deploy the read-only mount until these settings are off. With these values, a read-only mount blocks new artwork (Movies, Erotica, Books), NFO files (Movies, Shows), trickplay images (Movies, Shows), and downloaded subtitles (all libraries).

Trickplay needs a decision before you turn off `SaveTrickplayWithMedia`. Jellyfin finds trickplay images in the location that the current setting gives. When the setting is off, it can ignore the existing images next to the media, and the trickplay task can generate them again under `/config` on the Fast pool. That reads the full Movies and Shows libraries from Vault, and the images use space on the Fast NVMe. Measure the existing images first:

```bash
sudo find /mnt/Vault/Media/Movies /mnt/Vault/Media/Shows -type d -name '*.trickplay' -prune -exec du -sch {} + | tail -1
```

2026-10-21 (second check): The human changed the settings. `SaveLocalMetadata` is now false for each media library. `SaveTrickplayWithMedia` is not in the file for Movies or Shows, so it is off. Two settings still write next to the media:

- `MetadataSavers` is not empty for Movies and Shows. The check command shows only the first line of the element, so it does not show which savers are on.
- `SaveSubtitlesWithMedia` is true for each library. It has an effect only if a subtitle download plugin is installed.

Trickplay is now off for Movies and Shows. Run the next "Generate Trickplay Images" task before the read-only redeploy, at night. If Jellyfin moves the existing images, the move needs write access to `/media`. If it generates them again, the task reads the full libraries from Vault.

2026-10-21 (third check): `MetadataSavers` is now empty for each library, so Jellyfin writes no NFO files. `SaveSubtitlesWithMedia` is still true for each library. Before you tick the second criterion, check Dashboard -> Plugins for a subtitle download plugin. If there is none, the setting has no effect, so record that here. If there is one, turn the setting off for each library.

2026-10-21: The library settings do not show "Save subtitles into media folders". The web UI shows that option only in the "Subtitle Downloads" section, and it hides that section when no subtitle download plugin is installed. Thus no plugin is installed, and `SaveSubtitlesWithMedia` has no effect. The value `true` is the default. Subtitles that Jellyfin extracts from media files go to its cache under `/config`, not to `/media`. If a subtitle download plugin is installed later, turn this option off for each library first.

2026-10-21: The human turned trickplay off. No trickplay task runs, so no task moves or generates trickplay images, and the trickplay run before the redeploy is not necessary now. The read-only redeploy can go ahead. Seek previews are not available while trickplay is off.

When trickplay is turned on again, `/media` is read-only and `SaveTrickplayWithMedia` is off. Jellyfin then writes new images under `/config` on the Fast pool, and it can generate them again for the full Movies and Shows libraries. It cannot move or delete the existing images next to the media. Before you turn trickplay on, measure the existing images with the `du` command above, and check the free space on the Fast pool. See [[trickplay-gpu-keyframe-extraction]].

## Resolution
