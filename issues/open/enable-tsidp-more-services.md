---
title: "Use tsidp for login in more services"
state: open            # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: low          # critical | high | medium | low
effort: medium         # small | medium | large | x-large
tags: [feature, tailscale, security] # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
created: 2026-11-02
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

# Use tsidp for login in more services

## Summary

Use tsidp for login in more homelab services, so that users log in with their Tailscale identity. Grafana and Flights use it now.

## Context

[[grafana-tsidp-login]] shows the method: create a client in the tsidp UI, then configure the service with the client ID, the client secret, and the tsidp endpoints at `https://idp.comet-stork.ts.net`. Each service backend must reach tsidp by its tailnet name, so its sidecar needs `TS_ACCEPT_DNS=true`.

Check the current documentation of each candidate before you start:

| Service | Status |
|---|---|
| Karakeep | Its settings include OAuth login. Check the variables for version 0.33.2. |
| Kavita | Check if version 0.9.0 has OIDC login. |
| Tandoor | The compose file has `SOCIAL_PROVIDERS` for OpenID Connect. Check if it uses tsidp now. |
| Jellyfin | Needs a plugin. |
| Seerr, Sonarr, Radarr, Bazarr, Prowlarr | Check support. Some of them may have no OIDC login. |
| GameScores | The human owns this application. Check if it can use OIDC. |

## Acceptance criteria

- [ ] Each candidate uses tsidp, or Notes tells why not.
- [ ] Each service keeps a way in when tsidp is down, or Notes tells why not.
- [ ] Each new secret is listed in `ENVIRONMENT.md`.
- [ ] The tsidp dashboard shows logins for each service.

## Out of scope

- Grafana roles from Tailscale groups. See [[grafana-roles-from-tailscale]].

## Notes

2026-11-02: From the human: create this issue. Do not start this work yet.

## Resolution
