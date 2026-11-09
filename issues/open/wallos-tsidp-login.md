---
title: "Log in to Wallos with tsidp"
state: open            # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: low          # critical | high | medium | low
effort: small          # small | medium | large | x-large
tags: [feature, wallos, tsidp, security] # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
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

# Log in to Wallos with tsidp

## Summary

Let users sign in to Wallos with their Tailscale identity through tsidp, after the image is on a version with the OIDC security fixes.

## Context

Wallos has OIDC login since version 4.0, in the admin page (`/admin.php`, OIDC settings). The stack uses `bellamy/wallos` with no tag, so the version is not known. Its sidecar has `TS_ACCEPT_DNS=true`.

Three advisories affect the OIDC login. Pin the image to 4.9.6 or later first:

- CVE-2026-61641 (4.0.0 to before 4.9.6): OIDC login linked to a local account by email alone, without `email_verified`.
- CVE-2026-54599 (before 4.9.4): the OIDC `state` was not checked on the callback.
- CVE-2026-61640 (before 4.9.6): the token and userinfo URLs were not filtered against SSRF.

| Setting | Value |
|---|---|
| Client ID, Client Secret | From the tsidp client |
| Auth URL | `https://idp.comet-stork.ts.net/authorize` |
| Token URL | `https://idp.comet-stork.ts.net/token` |
| User Info URL | `https://idp.comet-stork.ts.net/userinfo` |
| Redirect URL | `https://wallos.comet-stork.ts.net/index.php` |
| Create user automatically | Off. Link the existing accounts. |

Check the paths against `https://idp.comet-stork.ts.net/.well-known/openid-configuration`.

## Acceptance criteria

- [ ] The Wallos image is pinned to 4.9.6 or later.
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
