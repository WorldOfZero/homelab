---
title: "Enable NVENC hardware acceleration in Jellyfin"
state: in-progress     # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: high         # critical | high | medium | low
effort: small          # small | medium | large | x-large
tags: [jellyfin, performance] # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
created: 2026-10-11
closed:                # YYYY-MM-DD. Set this only when state is closed.
owner: claude          # The person or agent working on the issue. Cleared when the issue returns to open.
approver:              # The person or agent who accepts the issue when it closes.
bookmark: enable-jellyfin-nvenc-transcoding # The jj bookmark of the work on the issue. Set this when work starts.
workspaces: [tailnet-local-network] # jj workspaces where local work on the issue has happened, for example [fix-login-bug].
metadata: {}           # Optional. Arbitrary key-value notes, for example an AI agent session id to resume work with context: {session-id: "abc123"}.
deferred-from:         # Optional. The issue (as a quoted wikilink) or bookmark that deferred this work.
parent:                # Optional. The parent issue (as a quoted wikilink), if this issue is a sub-issue.
depends-on: []           # Optional. Issues (as quoted wikilinks) that must close before this one can start, for example `["[[faster-startup]]"]`.
remote:                # Optional. A URL: the GitHub issue or Jira ticket that tracks this issue outside the repo.
---

# Enable NVENC hardware acceleration in Jellyfin

## Summary

Configure Jellyfin to use the NVIDIA GPU for decode and encode. The compose file gives the GPU to the container, but nothing shows that Jellyfin uses it.

## Context

Commit 8d3031f (2026-09-27) added the NVIDIA device reservation and `NVIDIA_DRIVER_CAPABILITIES=all` to the `application` service in `services/jellyfin/docker-compose.yaml`. Hardware acceleration is a Jellyfin server setting in Dashboard -> Playback -> Transcoding (`encoding.xml` in `/mnt/Fast/Configuration/jellyfin/config/config/`). The repo does not record this setting.

Evidence from the 2026-10-10 server log: every ffmpeg command line has no `-hwaccel` argument. The log shows only trickplay jobs, so the transcode settings are not known. Software transcodes of 4K or HEVC files use a large amount of CPU. They can also make the server slow for other requests.

Steps:

1. Run `sudo docker exec app-jellyfin nvidia-smi` on minerva. Make sure that the GPU is visible in the container.
2. In Dashboard -> Playback -> Transcoding, set Hardware acceleration to NVIDIA NVENC.
3. Enable hardware decoding for the codecs that the GPU supports. Use the NVIDIA support matrix for the GPU model.
4. Enable hardware encoding. Enable HEVC encoding only if the clients can play HEVC.
5. Enable tone mapping if the library has HDR files.

## Acceptance criteria

- [ ] `nvidia-smi` in `app-jellyfin` shows the GPU.
- [ ] A forced transcode (lower the quality in a client) shows `-hwaccel cuda` or `-init_hw_device cuda` in the ffmpeg log under `/config/log/`.
- [ ] `nvidia-smi` shows an `ffmpeg` process during that transcode.
- [ ] The selected settings are recorded in `services/jellyfin/` (a short README section or a comment in the compose file), because `encoding.xml` is not in the repo.

## Out of scope

- Trickplay generation on the GPU. See [[trickplay-gpu-keyframe-extraction]].
- The location of the transcode files. See [[verify-jellyfin-transcode-tmpfs]].

## Notes

2026-10-11: Found during an investigation of Jellyfin stalls. The stalls were a Tailscale relay problem, not CPU load. This issue removes CPU load that is not necessary.

2026-10-11: Input from the human (command output from minerva):

- `nvidia-smi` in `app-jellyfin` shows an NVIDIA T400 4GB (Turing, TU117). The driver is 550.127.05 and the CUDA version is 12.4. The container can use the GPU.
- `encoding.xml` has `HardwareAccelerationType` set to `none`. This is the cause: Jellyfin does not use the GPU.
- `HardwareDecodingCodecs` holds only `h264` and `vc1`. `EnableHardwareEncoding` is `true` but has no effect while the type is `none`. `EnableTonemapping` is `false`.
- The bundled ffmpeg lists the `cuda` hwaccel, `h264_nvenc`, `hevc_nvenc` and `av1_nvenc` encoders, and `*_cuvid` decoders. The T400 has no AV1 decode or AV1 encode hardware, so the AV1 entries do not apply.

Next: the human applies the settings in the `services/jellyfin` README, then runs a test transcode.

## Resolution
