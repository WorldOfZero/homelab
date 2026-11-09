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
| Grafana | Done. See [[grafana-tsidp-login]] and [[grafana-roles-from-tailscale]]. |
| AirTrail (Flights) | Done. Set in the AirTrail UI (Settings, OAuth). |
| Tandoor | In progress. See [[tandoor-tsidp-login]]. |
| Karakeep | Native OAuth. See [[karakeep-tsidp-login]]. |
| Kavita | Native OIDC. See [[kavita-tsidp-login]]. |
| Wallos | Native OIDC since 4.0. Pin 4.9.6 or later first. See [[wallos-tsidp-login]]. |
| Portainer | Custom OAuth in CE. See [[portainer-tsidp-login]]. |
| Jellyfin | Needs an SSO plugin fork for Jellyfin 12. See [[jellyfin-tsidp-login]]. |
| Home Assistant | Needs the `hass-oidc-auth` custom integration. See [[home-assistant-tsidp-login]]. |
| Seerr | OIDC only in development builds. Wait for a release. See [[seerr-tsidp-login]]. |
| Sonarr, Radarr, Bazarr, Uptime Kuma | No OIDC. Use the tailnet policy as the login. See [[tailnet-policy-login]]. |
| Prowlarr | Not in this repo. |
| movie-night | Its own repo. Track OIDC login there. |
| GameScores, Homepage, Ollama, Themearr | No user accounts, or only API keys. Nothing to do. |

## Acceptance criteria

- [ ] Each candidate uses tsidp, or Notes tells why not.
- [ ] Each service keeps a way in when tsidp is down, or Notes tells why not.
- [ ] Each new secret is listed in `ENVIRONMENT.md`.
- [ ] The tsidp dashboard shows logins for each service.

## Out of scope

- Grafana roles from Tailscale groups. See [[grafana-roles-from-tailscale]].

## Notes

2026-11-02: From the human: create this issue. Do not start this work yet.

2026-11-09: From the human: create an issue for each service that can use tsidp. Ideally the services get their login from the tailnet identity. One sub-issue for each service is in the table above.

## Resolution
