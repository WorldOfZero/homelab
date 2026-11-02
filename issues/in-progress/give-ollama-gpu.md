---
title: "Give Ollama the GPU and protect Jellyfin transcodes"
state: in-progress     # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: medium       # critical | high | medium | low
effort: small          # small | medium | large | x-large
tags: [feature, ollama, jellyfin] # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
created: 2026-11-02
closed:                # YYYY-MM-DD. Set this only when state is closed.
owner: claude          # The person or agent working on the issue. Cleared when the issue returns to open.
approver:              # The person or agent who accepts the issue when it closes.
bookmark: ollama-gpu   # The jj bookmark of the work on the issue. Set this when work starts.
workspaces: [fable]    # jj workspaces where local work on the issue has happened, for example [fix-login-bug].
metadata: {}           # Optional. Arbitrary key-value notes, for example an AI agent session id to resume work with context: {session-id: "abc123"}.
deferred-from:         # Optional. The issue (as a quoted wikilink) or bookmark that deferred this work.
parent:                # Optional. The parent issue (as a quoted wikilink), if this issue is a sub-issue.
depends-on: []           # Optional. Issues (as quoted wikilinks) that must close before this one can start, for example `["[[faster-startup]]"]`.
remote:                # Optional. A URL: the GitHub issue or Jira ticket that tracks this issue outside the repo.
---

# Give Ollama the GPU and protect Jellyfin transcodes

## Summary

Run Ollama on the NVIDIA T400, so that recipe parsing in Tandoor is faster, and keep enough GPU memory for Jellyfin transcodes.

## Context

minerva has one NVIDIA T400 with 4 GB of memory. Jellyfin uses it for transcodes. See [[enable-jellyfin-nvenc-transcoding]] and [[tandoor-tsidp-login]].

A model in GPU memory can stop a Jellyfin transcode. These settings decrease the risk:

- `OLLAMA_KEEP_ALIVE=5m` removes a model from memory after 5 minutes with no use. The value was `24h`.
- `OLLAMA_GPU_OVERHEAD=1073741824` keeps 1 GB of GPU memory free.
- `OLLAMA_MAX_LOADED_MODELS=1` keeps one model in memory.

Thus Ollama has about 3 GB of GPU memory. A larger model runs partly on the CPU, or on the CPU only.

## Acceptance criteria

- [x] The compose file gives the GPU to Ollama, with the same method as Jellyfin.
- [ ] `nvidia-smi` in `app-ollama` shows the GPU, and `ollama ps` shows that a model uses it.
- [ ] A Jellyfin transcode works while Ollama has a model in memory.
- [ ] A recipe import from Tandoor is faster than on the CPU.

## Out of scope

- A second GPU.

## Notes

2026-11-02: From the human: give the GPU to Ollama.

## Resolution
