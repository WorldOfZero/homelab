---
title: "Log in to Kavita with tsidp"
state: open            # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: low          # critical | high | medium | low
effort: small          # small | medium | large | x-large
tags: [feature, kavita, tsidp] # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
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

# Log in to Kavita with tsidp

## Summary

Let users sign in to Kavita with their Tailscale identity through tsidp.

## Context

Kavita has OpenID Connect login (Settings, Server, OpenID Connect in the web UI; see the Kavita wiki). The stack runs `linuxserver/kavita:0.9.1`, and its sidecar has `TS_ACCEPT_DNS=true`.

| Setting | Value |
|---|---|
| Authority | `https://idp.comet-stork.ts.net` (no trailing slash) |
| Client ID, Client Secret | From the tsidp client |

The redirect URI of the tsidp client is `https://kavita.comet-stork.ts.net/signin-oidc`, and the logout callback is `/signout-callback-oidc`. Kavita needs a restart after a change to the Authority, the client ID or the secret.

- The `aud` claim must be the client ID. tsidp sets it so, but check it.
- Kavita links an OIDC login to an existing account by email. The Kavita account emails must be the Tailscale login names, as tsidp sends them.
- The settings live in the Kavita database, not in compose. Write them in the README so that a rebuild can repeat them. See [[fix-kavita-data-loss]].

## Acceptance criteria

- [ ] A user signs in with their Tailscale identity through tsidp, and the account links to the existing user, not a duplicate.
- [ ] A way in stays when tsidp is down (a local admin login), or Notes tells why not.
- [ ] Each new secret is listed in `ENVIRONMENT.md`.
- [ ] The service README tells how to create the tsidp client and where the settings are.

## Out of scope

- Grafana-style roles from Tailscale groups. Do it after login works.

## Notes

2026-11-09: From the human: track tsidp login for each homelab service that can use it. Ideally the services get their login from the tailnet identity.

## Resolution

<Complete this section when you close the issue.
- Completed: tell what was done. Link to the changelog version and the decision records, for example `[[0.0.5]]`.
- Abandoned: tell why the work stopped. Link to the issue or decision that replaces it, if one exists.>
