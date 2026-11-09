---
title: "Log in to Karakeep with tsidp"
state: open            # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: low          # critical | high | medium | low
effort: small          # small | medium | large | x-large
tags: [feature, karakeep, tsidp] # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
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

# Log in to Karakeep with tsidp

## Summary

Let users sign in to Karakeep with their Tailscale identity through tsidp, instead of a Karakeep password.

## Context

Karakeep 0.34.1 has OAuth login, set with environment variables in `services/karakeep/docker-compose.yaml`. The stack already sets `NEXTAUTH_URL`, and its sidecar has `TS_ACCEPT_DNS=true`, so the backend can reach tsidp by its tailnet name.

The provider guides (Authelia, Pocket ID, authentik) use these variables. Read the Karakeep documentation for 0.34.1 before you start:

| Variable | Value |
|---|---|
| `OAUTH_WELLKNOWN_URL` | `https://idp.comet-stork.ts.net/.well-known/openid-configuration` |
| `OAUTH_CLIENT_ID`, `OAUTH_CLIENT_SECRET` | From the tsidp client. Portainer variables. |
| `OAUTH_PROVIDER_NAME` | `Tailscale` |
| `DISABLE_PASSWORD_AUTH` | Leave unset, so that password login stays as a way in. |

The redirect URI of the tsidp client is `https://karakeep.comet-stork.ts.net/api/auth/callback/custom`.

Existing accounts link to a new OAuth login only with `OAUTH_ALLOW_DANGEROUS_EMAIL_ACCOUNT_LINKING=true`. tsidp sets the `email` claim from the Tailscale login name, and only tailnet users can reach tsidp, so linking by email is acceptable here. Record the decision in Notes.

## Acceptance criteria

- [ ] A user signs in with their Tailscale identity through tsidp, and the account links to the existing user, not a duplicate.
- [ ] A way in stays when tsidp is down (a local admin login), or Notes tells why not.
- [ ] Each new secret is listed in `ENVIRONMENT.md`.
- [ ] The service README tells how to create the tsidp client and where the settings are.

## Out of scope

- Turning off password login. Do it in a later change, after tsidp login works for some weeks.

## Notes

2026-11-09: From the human: track tsidp login for each homelab service that can use it. Ideally the services get their login from the tailnet identity.

## Resolution

<Complete this section when you close the issue.
- Completed: tell what was done. Link to the changelog version and the decision records, for example `[[0.0.5]]`.
- Abandoned: tell why the work stopped. Link to the issue or decision that replaces it, if one exists.>
