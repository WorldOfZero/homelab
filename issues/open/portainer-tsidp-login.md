---
title: "Log in to Portainer with tsidp"
state: open            # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: low          # critical | high | medium | low
effort: small          # small | medium | large | x-large
tags: [feature, portainer, tsidp, security] # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
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

# Log in to Portainer with tsidp

## Summary

Let the homelab operators sign in to Portainer with their Tailscale identity through tsidp.

## Context

Portainer deploys every stack, so its login protects the whole homelab. Portainer CE has OAuth login with a custom provider (Settings, Authentication, OAuth, Custom). Automatic team membership from groups is only in Business Edition. Portainer CE 2.45.1 runs on minerva.

| Setting | Value |
|---|---|
| Client ID, Client Secret | From the tsidp client |
| Authorization URL | `https://idp.comet-stork.ts.net/authorize` |
| Access token URL | `https://idp.comet-stork.ts.net/token` |
| Resource URL | `https://idp.comet-stork.ts.net/userinfo` |
| Redirect URL | The Portainer URL |
| User identifier | `email` |
| Scopes | `openid email profile` |
| Automatic user provisioning | Off |

- tsidp PR #117 is about Portainer. Read it before you start, and check if tsidp v0.0.18 has it.
- Portainer must reach tsidp by its tailnet name. Check how Portainer runs on minerva, and if it can resolve `idp.comet-stork.ts.net`.
- The local `admin` login must stay. It is the way in when tsidp is down, and tsidp itself is deployed by Portainer.

## Acceptance criteria

- [ ] A user signs in with their Tailscale identity through tsidp, and the account links to the existing user, not a duplicate.
- [ ] A way in stays when tsidp is down (a local admin login), or Notes tells why not.
- [ ] Each new secret is listed in `ENVIRONMENT.md`.
- [ ] The service README tells how to create the tsidp client and where the settings are.
- [ ] The local admin login still works with OAuth turned on.

## Out of scope

- Portainer Business Edition.

## Notes

2026-11-09: From the human: track tsidp login for each homelab service that can use it. Ideally the services get their login from the tailnet identity.

## Resolution

<Complete this section when you close the issue.
- Completed: tell what was done. Link to the changelog version and the decision records, for example `[[0.0.5]]`.
- Abandoned: tell why the work stopped. Link to the issue or decision that replaces it, if one exists.>
