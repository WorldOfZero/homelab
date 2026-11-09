---
title: "Log in to Seerr with tsidp"
state: open            # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: low          # critical | high | medium | low
effort: small          # small | medium | large | x-large
tags: [feature, seerr, tsidp] # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
created: 2026-11-09
closed:                # YYYY-MM-DD. Set this only when state is closed.
owner:                 # The person or agent working on the issue. Cleared when the issue returns to open.
approver:              # The person or agent who accepts the issue when it closes.
bookmark:              # The jj bookmark of the work on the issue. Set this when work starts.
workspaces: []         # jj workspaces where local work on the issue has happened, for example [fix-login-bug].
metadata: {}           # Optional. Arbitrary key-value notes, for example an AI agent session id to resume work with context: {session-id: "abc123"}.
deferred-from:         # Optional. The issue (as a quoted wikilink) or bookmark that deferred this work.
parent: "[[enable-tsidp-more-services]]" # Optional. The parent issue (as a quoted wikilink), if this issue is a sub-issue.
depends-on: []           # Optional. Issues (as quoted wikilinks) that must close before this one can start, for example `["[[faster-startup]]"]`.
remote:                # Optional. A URL: the GitHub issue or Jira ticket that tracks this issue outside the repo.
---

# Log in to Seerr with tsidp

## Summary

Let users sign in to Seerr with their Tailscale identity through tsidp, when Seerr has a stable OIDC login.

## Context

Seerr (`ghcr.io/seerr-team/seerr:latest`) has no OIDC login in a stable release. The Seerr discussions #1529 and #2721 test OIDC in development builds, and the maintainers warn that it can break, and that it may not be compatible with later versions.

Wait for a release that has OIDC. Until then, users sign in with their Jellyfin account. If [[jellyfin-tsidp-login]] is done first, check if Seerr's Jellyfin login still works with password login.

When OIDC is released, the discussions say that the redirect URI is `https://seerr.comet-stork.ts.net/login`. The sidecar has `TS_ACCEPT_DNS=true`. Pin the image tag then, because `latest` can change at any commit (see `services/portainer/README.md`).

## Acceptance criteria

- [ ] A Seerr release with OIDC login exists, and the image is pinned to it.
- [ ] A user signs in with their Tailscale identity through tsidp, and the account links to the existing user, not a duplicate.
- [ ] A way in stays when tsidp is down (a local admin login), or Notes tells why not.
- [ ] Each new secret is listed in `ENVIRONMENT.md`.
- [ ] The service README tells how to create the tsidp client and where the settings are.

## Out of scope

- A development build of Seerr.

## Notes

2026-11-09: From the human: track tsidp login for each homelab service that can use it. Ideally the services get their login from the tailnet identity.

## Resolution

<Complete this section when you close the issue.
- Completed: tell what was done. Link to the changelog version and the decision records, for example `[[0.0.5]]`.
- Abandoned: tell why the work stopped. Link to the issue or decision that replaces it, if one exists.>
