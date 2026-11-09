---
title: "Use the tailnet policy as the login for apps without OIDC"
state: open            # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: low          # critical | high | medium | low
effort: small          # small | medium | large | x-large
tags: [feature, tailscale, security, arr, kuma] # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
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

# Use the tailnet policy as the login for apps without OIDC

## Summary

For services with no OIDC login, use the tailnet identity as the login: the tailnet policy lets only the right users reach them, and the service's own login is turned off.

## Context

These services have no OIDC login, so tsidp cannot sign users in:

| Service | Login now | Change |
|---|---|---|
| Sonarr, Radarr | Forms login. Since Sonarr v4, a login is required. | `AuthenticationMethod` `External` in `config.xml`. The service then trusts every request that reaches it. |
| Bazarr | Its own login | Authentication none |
| Uptime Kuma 2 | One local user | Turn off authentication in the settings. Uptime Kuma has no native SSO. |

Each service is reachable only through its Tailscale sidecar, so the tailnet policy decides who reaches it. This is safe only after the policy stops allowing everything (`"src": ["*"]`, `"dst": ["*"]`). The policy is in homelab-private.

1. Give the sidecars tags (for example `tag:arr-stack`, which is in `tagOwners`, and a tag for Uptime Kuma), with `--advertise-tags` and in the admin console.
2. Add grants: `group:arr-users` to the arr tags on 443, `group:homelab-operators` to Uptime Kuma on 443. Keep the grants that Prometheus, the exporters, Seerr and Homepage need, for example the Docker network paths and the tagged nodes.
3. Add `tests` to the policy: a user outside the group is denied, and the group is accepted.
4. Then turn off the logins, one service at a time.

The exporters use API keys, which do not change. Do not use Tailscale Funnel or a Cloudflare tunnel for these services.

## Acceptance criteria

- [ ] The tailnet policy allows the arr services only for `group:arr-users`, and Uptime Kuma only for `group:homelab-operators`, and its tests show it.
- [ ] Sonarr, Radarr, Bazarr and Uptime Kuma have no login of their own, and a tailnet device outside the groups cannot reach them.
- [ ] The exporters, Seerr and the Prometheus probes still work.
- [ ] The README of each service tells that the tailnet policy is its login.

## Out of scope

- Narrowing the policy for the other services. Track it separately.

## Notes

2026-11-09: From the human: track tsidp login for each homelab service that can use it. Ideally the services get their login from the tailnet identity.

## Resolution

<Complete this section when you close the issue.
- Completed: tell what was done. Link to the changelog version and the decision records, for example `[[0.0.5]]`.
- Abandoned: tell why the work stopped. Link to the issue or decision that replaces it, if one exists.>
