---
title: "Log in to Jellyfin with tsidp"
state: open            # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: low          # critical | high | medium | low
effort: medium         # small | medium | large | x-large
tags: [feature, jellyfin, tsidp] # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
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

# Log in to Jellyfin with tsidp

## Summary

Let users sign in to Jellyfin's web UI with their Tailscale identity through tsidp, with an SSO plugin.

## Context

Jellyfin has no OIDC login of its own. The stack runs `jellyfin/jellyfin:12.2`. The original `9p4/jellyfin-plugin-sso` is archived. Forks with a Jellyfin 12 build:

- `K0lin/jellyfin-plugin-sso` 5.1.0 targets Jellyfin 12.0.
- `Flowfin/jellyfin-plugin-sso` 5.0.0-JF12 is a beta for Jellyfin 12.

Compare the forks (maintenance, open security issues, the `targetAbi` for 12.2) before you choose one. The plugin adds a separate sign-in page. The normal login form stays.

These clients must keep working, because they do not use the plugin's page:

- The TV apps, the Shield, and Moonfin: password login or Quick Connect.
- movie-night: hosts sign in with a Jellyfin user and password, and the service uses its own API key.
- The enricher and the exporter: API keys.

The redirect URI depends on the fork. The sidecar has `TS_ACCEPT_DNS=true`.

## Acceptance criteria

- [ ] The plugin is installed from a pinned version, and the README tells which fork and why.
- [ ] A user signs in with their Tailscale identity through tsidp, and the account links to the existing user, not a duplicate.
- [ ] A way in stays when tsidp is down (a local admin login), or Notes tells why not.
- [ ] Each new secret is listed in `ENVIRONMENT.md`.
- [ ] The service README tells how to create the tsidp client and where the settings are.
- [ ] The TV apps, Moonfin, Quick Connect, movie-night and the API keys still work.

## Out of scope

- Role or library mapping from Tailscale groups. Do it after basic login works.
- OIDC login in movie-night. That is in the movie-night repo.

## Notes

2026-11-09: From the human: track tsidp login for each homelab service that can use it. Ideally the services get their login from the tailnet identity.

## Resolution

<Complete this section when you close the issue.
- Completed: tell what was done. Link to the changelog version and the decision records, for example `[[0.0.5]]`.
- Abandoned: tell why the work stopped. Link to the issue or decision that replaces it, if one exists.>
