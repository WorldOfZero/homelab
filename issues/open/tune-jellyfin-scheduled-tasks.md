---
title: "Tune the Jellyfin scheduled tasks and library monitoring"
state: open            # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: medium       # critical | high | medium | low
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
depends-on: []           # Optional. Issues (as quoted wikilinks) that must close before this one can start, for example `["[[faster-startup]]"]`.
remote:                # Optional. A URL: the GitHub issue or Jira ticket that tracks this issue outside the repo.
---

# Tune the Jellyfin scheduled tasks and library monitoring

## Summary

Review the Jellyfin scheduled tasks and the library monitoring settings. Run the heavy tasks at night, and disable tasks that duplicate other tasks.

## Context

The 2026-10-10 server log shows the trickplay task during the evening (19:36 to 20:36), at the same time as a playback session. Heavy tasks read full files from the Vault HDDs and use CPU. They compete with playback.

Review these items in Dashboard -> Scheduled Tasks and in the library settings:

- "Generate Trickplay Images": run it in a night window only, for example 01:00 to 07:00.
- "Extract Chapter Images": this task decodes each file again. Trickplay gives seek previews already, so disable chapter image extraction for each library unless a client needs it.
- "Scan Media Library": the interval. With real-time monitoring on, a scan every 12 hours is often more than necessary.
- Real-time monitoring on each library: on ZFS over a large tree, inotify can miss events or use many watches. Keep it on only if new media must appear at once.
- "Extract Media Segments" (intro and credits): run at night if a plugin uses it.

Also check that no Jellyfin task overlaps the nightly ZFS snapshot and replication of `Fast/Configuration`.

## Acceptance criteria

- [ ] Notes has the schedule of each task before and after the change.
- [ ] Trickplay and chapter extraction do not run between 17:00 and 01:00 local time.
- [ ] Chapter image extraction is disabled for each library, or Notes tells why not.
- [ ] The final schedule is recorded in `services/jellyfin/`, because the scheduled task settings are not in the repo.

## Out of scope

- Trickplay speed. See [[trickplay-gpu-keyframe-extraction]].

## Notes

2026-10-20: The server log shows the problem again, this time in the morning: a library scan ("Validating media library") started at 10:13 while a playback session (started 10:09, Snake Eyes, audio transcode) was streaming from the Vault HDDs. The Moonfin scheduled tasks ran at 10:13:23 and the scan followed immediately, so the 12-hour scan interval appears to fire mid-morning. The scan also re-reads game disc images from Vault and throws errors on them — see [[stop-jellyfin-scanning-game-disc-images]].

## Resolution
