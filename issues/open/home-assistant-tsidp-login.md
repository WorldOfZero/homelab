---
title: "Log in to Home Assistant with tsidp"
state: open            # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: low          # critical | high | medium | low
effort: medium         # small | medium | large | x-large
tags: [feature, home-assistant, tsidp] # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
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

# Log in to Home Assistant with tsidp

## Summary

Let users sign in to Home Assistant with their Tailscale identity through tsidp.

## Context

Home Assistant has no OIDC login of its own. The custom integration `christiaangoossens/hass-oidc-auth` adds it (install with HACS). Version 1.0 and later have UI configuration and redirect to the provider automatically. The redirect URI is `/auth/oidc/callback`. An alternative is `cavefire/hass-openid`.

- The Home Assistant configuration is in homelab-private (see `services/home-assistant/README.md`). The `auth_oidc` YAML goes there.
- A Home Assistant user must exist before it can sign in with OIDC.
- The mobile app and the CI sync (`tag:ci`, long-lived token) must keep working. Version 1.1.1 fixed login for apps that use the OAuth2 integration.

## Acceptance criteria

- [ ] A user signs in with their Tailscale identity through tsidp, and the account links to the existing user, not a duplicate.
- [ ] A way in stays when tsidp is down (a local admin login), or Notes tells why not.
- [ ] Each new secret is listed in `ENVIRONMENT.md`.
- [ ] The service README tells how to create the tsidp client and where the settings are.
- [ ] The mobile app, the long-lived tokens and the shopping sync still work.

## Out of scope

- Home Assistant Cloud login.

## Notes

2026-11-09: From the human: track tsidp login for each homelab service that can use it. Ideally the services get their login from the tailnet identity.

## Resolution

<Complete this section when you close the issue.
- Completed: tell what was done. Link to the changelog version and the decision records, for example `[[0.0.5]]`.
- Abandoned: tell why the work stopped. Link to the issue or decision that replaces it, if one exists.>
