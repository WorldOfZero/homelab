---
title: "Make Jellyfin transcodes use the tmpfs mount"
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

# Make Jellyfin transcodes use the tmpfs mount

## Summary

Make sure that Jellyfin writes transcode segments to the 4 GB tmpfs. The tmpfs is mounted at a path that is probably not the transcode path, so it is possibly not used.

## Context

`services/jellyfin/docker-compose.yaml` mounts `tmpfs: /config/data/transcodes:size=4G`. Commit b0ffa38 added it to stop HDD thrashing when `/config` was on the Vault pool.

In the official Jellyfin Docker image, the default transcode path is `/cache/transcodes` (forum reports and the Jellyfin TrueNAS guide; not confirmed for 10.11.11). `/cache` is a bind mount of `/mnt/Fast/Configuration/jellyfin/cache` on the Fast NVMe pool. If the default applies, transcodes go to the NVMe, and the tmpfs is not used.

The Fast pool is one NVMe disk with no redundancy. Transcode writes cause wear on it, and they go into the nightly ZFS snapshot of `Fast/Configuration`.

Check on minerva:

```bash
sudo docker exec app-jellyfin sh -c 'grep -i TranscodingTempPath /config/config/encoding.xml; df -h /config/data/transcodes /cache'
```

Then start a transcode and look in which directory the `.ts` or `.mp4` segments appear.

Options:

- A: Set the transcode path to `/config/data/transcodes` in Dashboard -> Playback -> Transcoding.
- B: Move the tmpfs mount to `/cache/transcodes` in the compose file. This keeps the Jellyfin default.

Option B keeps the setting in the repo. 4 GB is enough for about two 4K transcodes. Jellyfin deletes old segments when "Throttle transcodes" and "Delete segments" are enabled. Enable both.

## Acceptance criteria

- [x] The real transcode path is recorded in Notes.
- [ ] Transcode segments appear in the tmpfs during a test transcode (`df` shows usage).
- [ ] "Throttle transcodes" and "Delete segments" are enabled, or Notes tells why not.
- [x] If option B is used, `services/jellyfin/docker-compose.yaml` mounts the tmpfs at `/cache/transcodes`.

## Out of scope

- Hardware transcoding. See [[enable-jellyfin-nvenc-transcoding]].

## Notes

2026-10-11: `encoding.xml` (from the human, during [[enable-jellyfin-nvenc-transcoding]]) has `EnableThrottling` and `EnableSegmentDeletion` set to `false`. With both off, a transcode keeps all of its segments until playback stops. A long 4K transcode can then fill a 4 GB tmpfs. The file has no `TranscodingTempPath` entry, so Jellyfin uses its default path.

2026-10-20: Confirmed from the server log. A playback session's ffmpeg command writes segments to `/cache/transcodes/...` (`-hls_segment_filename "/cache/transcodes/56eb0ef290e21f613069314a405eda9b%d.mp4"`). The tmpfs at `/config/data/transcodes` is not used; transcode writes go to the Fast NVMe via the `/cache` bind mount. This completes the first acceptance criterion: the real transcode path is `/cache/transcodes`.

2026-10-21: Option B is used. The compose file now mounts the tmpfs at `/cache/transcodes` with `size=4G,uid=1000,gid=1000,mode=0755`. The `uid` and `gid` options are necessary: Docker creates a tmpfs owned by root, and Jellyfin runs as `1000:1000`. Without them, every transcode fails. `services/jellyfin/README.md` records the tmpfs and tells not to set a custom transcode path.

To do on minerva after the redeploy:

1. Start a transcode, then run `sudo docker exec app-jellyfin df -h /cache/transcodes`. Usage must rise.
2. Check that `EnableThrottling` and `EnableSegmentDeletion` are `true` in `encoding.xml`. The README records both as on, but the 2026-10-11 note found both off.
3. Delete the old segments on the NVMe. The tmpfs hides them, but they still use space: `sudo rm -rf /mnt/Fast/Configuration/jellyfin/cache/transcodes/*`. Do this while the container is stopped, because the tmpfs hides the directory while it runs.

## Resolution
