---
title: "Generate Jellyfin trickplay images on the GPU from keyframes"
state: open            # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: high         # critical | high | medium | low
effort: small          # small | medium | large | x-large
tags: [jellyfin, performance] # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
created: 2026-10-11
closed:                # YYYY-MM-DD. Set this only when state is closed.
owner:                 # The person or agent working on the issue. Cleared when the issue returns to open.
approver:              # The person or agent who accepts the issue when it closes.
bookmark:              # The jj bookmark of the work on the issue. Set this when work starts.
workspaces: []         # jj workspaces where local work on the issue has happened, for example [fix-login-bug].
metadata: {}           # Optional. Arbitrary key-value notes, for example an AI agent session id to resume work with context: {session-id: "abc123"}.
deferred-from:         # Optional. The issue (as a quoted wikilink) or bookmark that deferred this work.
parent:                # Optional. The parent issue (as a quoted wikilink), if this issue is a sub-issue.
depends-on: ["[[enable-jellyfin-nvenc-transcoding]]"] # Optional. Issues (as quoted wikilinks) that must close before this one can start, for example `["[[faster-startup]]"]`.
remote:                # Optional. A URL: the GitHub issue or Jira ticket that tracks this issue outside the repo.
---

# Generate Jellyfin trickplay images on the GPU from keyframes

## Summary

Make trickplay generation use the GPU and keyframe-only extraction. Now each film takes 4 to 28 minutes of CPU time, and the task runs for days.

## Context

The 2026-10-10 server log shows the "Generate Trickplay Images" task. It works through the Movies library one file at a time. The ffmpeg command has no hardware acceleration:

```
/usr/lib/jellyfin-ffmpeg/ffmpeg -loglevel error -i file:"/media/Movies/..." -an -sn
  -vf "fps=0.1...,scale=...,format=yuv420p" -threads 1 -c:v mjpeg ...
```

Measured times from the log: 5 min 42 s (Alien Outpost), 3 min 51 s (Alien Resurrection t09), 27 min 46 s (Alienoid), 4 min 9 s (Aliens). ffmpeg decodes each full Blu-ray remux in software to keep one frame in every 10 seconds.

Jellyfin 10.10 and later have two options in Dashboard -> Playback -> Trickplay:

- "Enable hardware decoding". This option needs [[enable-jellyfin-nvenc-transcoding]] first.
- "Only generate images from key frames". ffmpeg then reads only the keyframes. Forum reports say that this is much faster, with a small loss of timing accuracy.

"Enable hardware accelerated MJPEG encoding" is a third option. It depends on GPU support.

## Acceptance criteria

- [ ] Hardware decoding and keyframe-only extraction are enabled for trickplay.
- [ ] The trickplay ffmpeg command in the log shows hardware decode arguments.
- [ ] The time for one film is measured before and after the change, and recorded in Notes.
- [ ] The trickplay task runs in a night window. See [[tune-jellyfin-scheduled-tasks]].

## Out of scope

- The location where trickplay images are saved. See [[keep-jellyfin-writes-off-vault]].

## Notes

2026-10-11: Times above are from the log that the human gave on 2026-10-10.

## Resolution
