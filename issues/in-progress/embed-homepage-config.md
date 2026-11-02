---
title: "Build the Homepage config into its image"
state: in-progress     # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: medium       # critical | high | medium | low
effort: small          # small | medium | large | x-large
tags: [feature, homepage] # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
created: 2026-11-02
closed:                # YYYY-MM-DD. Set this only when state is closed.
owner: claude          # The person or agent working on the issue. Cleared when the issue returns to open.
approver:              # The person or agent who accepts the issue when it closes.
bookmark: homepage-config-image # The jj bookmark of the work on the issue. Set this when work starts.
workspaces: [fable]         # jj workspaces where local work on the issue has happened, for example [fix-login-bug].
metadata: {}           # Optional. Arbitrary key-value notes, for example an AI agent session id to resume work with context: {session-id: "abc123"}.
deferred-from:         # Optional. The issue (as a quoted wikilink) or bookmark that deferred this work.
parent:                # Optional. The parent issue (as a quoted wikilink), if this issue is a sub-issue.
depends-on: []           # Optional. Issues (as quoted wikilinks) that must close before this one can start, for example `["[[faster-startup]]"]`.
remote:                # Optional. A URL: the GitHub issue or Jira ticket that tracks this issue outside the repo.
---

# Build the Homepage config into its image

## Summary

Build `services/homepage/config` into the Homepage image, so a Git update delivers a config change.

## Context

Homepage read its config from `/mnt/Fast/Configuration/homepage/config` on the host, so a change in the repo did not reach it. The repo has only `bookmarks.yaml`, `services.yaml` and `widgets.yaml`. The host can have other files, such as `settings.yaml`.

## Acceptance criteria

- [x] A local build of the image starts and serves the services, bookmarks and widgets from the repo.
- [ ] The human compares the host config with the repo, and the repo gets each file that matters.
- [ ] After the deploy, a config change reaches Homepage with no redeploy in the UI.

## Out of scope

- Remove the old directory on the host. Keep it until the deploy is good.

## Notes

2026-11-02: From the human: embed the Homepage config in the container, so it deploys automatically with GitOps.

2026-11-02: `services.yaml` uses `HOMEPAGE_VAR_BAZARR_API` and `widgets.yaml` uses `HOMEPAGE_VAR_UNIFI_API`, but the stack does not supply these variables. This change does not fix that.

2026-11-02: Homepage copies a default `settings.yaml` when the file is missing. The default replaces any settings that are only on the host.

## Resolution

<Complete this section when you close the issue.
- Completed: tell what was done. Link to the changelog version and the decision records, for example `[[0.0.5]]`.
- Abandoned: tell why the work stopped. Link to the issue or decision that replaces it, if one exists.>
