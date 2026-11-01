---
title: "Log in to Grafana with Tailscale through tsidp"
state: in-progress     # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: medium       # critical | high | medium | low
effort: small          # small | medium | large | x-large
tags: [feature, grafana, tailscale] # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
created: 2026-11-01
closed:                # YYYY-MM-DD. Set this only when state is closed.
owner: claude          # The person or agent working on the issue. Cleared when the issue returns to open.
approver:              # The person or agent who accepts the issue when it closes.
bookmark: grafana-tsidp # The jj bookmark of the work on the issue. Set this when work starts.
workspaces: [fable]    # jj workspaces where local work on the issue has happened, for example [fix-login-bug].
metadata: {}           # Optional. Arbitrary key-value notes, for example an AI agent session id to resume work with context: {session-id: "abc123"}.
deferred-from:         # Optional. The issue (as a quoted wikilink) or bookmark that deferred this work.
parent:                # Optional. The parent issue (as a quoted wikilink), if this issue is a sub-issue.
depends-on: []           # Optional. Issues (as quoted wikilinks) that must close before this one can start, for example `["[[faster-startup]]"]`.
remote:                # Optional. A URL: the GitHub issue or Jira ticket that tracks this issue outside the repo.
---

# Log in to Grafana with Tailscale through tsidp

## Summary

Use tsidp for Grafana login, so that tailnet users log in with their Tailscale identity.

## Context

The `tailscale-idp` stack runs tsidp at `idp.comet-stork.ts.net`. Airtrail uses it today. The Grafana backend must call the tsidp token endpoint by its tailnet name, so the Grafana sidecar needs `TS_ACCEPT_DNS=true`. See [[collect-all-homelab-telemetry]].

## Acceptance criteria

- [x] Grafana uses tsidp through generic OAuth, with PKCE.
- [x] A test with a mock provider gives Admin to the configured email and Viewer to other users.
- [x] The local login form stays as a way in when tsidp is down.
- [ ] On minerva, the human logs in through `https://grafana.comet-stork.ts.net` and gets the Admin role.

## Out of scope

- Roles from tsidp `extraClaims` groups.
- Turning off the local login form.

## Notes

2026-11-01: From the human: use tsidp for Grafana auth, and Airtrail uses tsidp today.

2026-11-01: tsidp v0.0.15 sends no groups claim by default. Thus `GRAFANA_ADMIN_EMAIL` selects the Admin user, and other tailnet users get Viewer. The value must be the `email` claim that tsidp sends for the user.

2026-11-01: The test used Grafana 13.1.1 and a mock provider with the claims in the tsidp source. It did not use real tsidp, because that needs the tailnet. `/authorize` uses WhoIs, so the browser must be on the tailnet.

## Resolution
