---
title: "Set Grafana roles from Tailscale groups"
state: in-progress     # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: low          # critical | high | medium | low
effort: small          # small | medium | large | x-large
tags: [feature, grafana, tailscale] # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
created: 2026-11-01
closed:                # YYYY-MM-DD. Set this only when state is closed.
owner: claude          # The person or agent working on the issue. Cleared when the issue returns to open.
approver:              # The person or agent who accepts the issue when it closes.
bookmark: grafana-roles-from-groups # The jj bookmark of the work on the issue. Set this when work starts.
workspaces: [fable]    # jj workspaces where local work on the issue has happened, for example [fix-login-bug].
metadata: {}           # Optional. Arbitrary key-value notes, for example an AI agent session id to resume work with context: {session-id: "abc123"}.
deferred-from: "[[grafana-tsidp-login]]" # Optional. The issue (as a quoted wikilink) or bookmark that deferred this work.
parent:                # Optional. The parent issue (as a quoted wikilink), if this issue is a sub-issue.
depends-on: []           # Optional. Issues (as quoted wikilinks) that must close before this one can start, for example `["[[faster-startup]]"]`.
remote:                # Optional. A URL: the GitHub issue or Jira ticket that tracks this issue outside the repo.
---

# Set Grafana roles from Tailscale groups

## Summary

Set Grafana roles from Tailscale groups, and deny users who are in no group. Now `GRAFANA_ADMIN_EMAIL` gives one user the Admin role, and all other tailnet users can sign up with the Viewer role.

## Context

[[grafana-tsidp-login]] added Grafana login through tsidp. tsidp does not send Tailscale groups by default. It sends the `extraClaims` of the `tailscale.com/cap/tsidp` app capability grant.

Add one grant for each role to the tailnet policy. Replace the `src` and `dst` values with the values for this tailnet:

```jsonc
{
  "src": ["group:grafana-admins"],
  "dst": ["*"],
  "app": {
    "tailscale.com/cap/tsidp": [
      { "extraClaims": { "groups": ["grafana-admins"] }, "includeInUserInfo": true }
    ]
  }
}
```

Then change the Grafana environment in `services/grafana/docker-compose.yaml`:

```yaml
- "GF_AUTH_GENERIC_OAUTH_ROLE_ATTRIBUTE_PATH=contains(groups || `[]`, 'grafana-admins') && 'Admin' || contains(groups || `[]`, 'grafana-editors') && 'Editor' || contains(groups || `[]`, 'grafana-viewers') && 'Viewer'"
- GF_AUTH_GENERIC_OAUTH_ROLE_ATTRIBUTE_STRICT=true
```

Add the grants before the deploy. With strict mode, Grafana denies a user who has no matching group, and this includes the administrator. The local login form stays as a way in. Grafana sets the role at login, so a role change takes effect at the next login of the user.

tsidp warns that its capability schema can change. Read the schema of the deployed tsidp version again before you start. These notes use v0.0.15.

## Acceptance criteria

- [x] The human selects the groups. Proposed: `grafana-admins` and `grafana-viewers`.
- [x] The tailnet policy has a grant for each group.
- [ ] A test with a mock provider gives the correct role for each group, and denies a user with no group.
- [x] `GRAFANA_ADMIN_EMAIL` is removed from the compose file, `services/grafana/README.md`, and `ENVIRONMENT.md`.
- [ ] On minerva, a user in each group gets the correct role, and a user in no group cannot log in.

## Out of scope

- Grafana teams. Team Sync needs Grafana Enterprise or a select Grafana Cloud plan.
- Grafana organizations for each group (`org_attribute_path` and `org_mapping`).

## Notes

2026-11-01: From the human: track this work, and do not implement it yet.

2026-11-08: The human made `group:grafana-admins`, `group:grafana-editors` and `group:grafana-viewers`, and a grant for each, with `dst` `tag:tsidp`. The admin UI and client registration grant is now for `group:homelab-operators` only.

2026-11-08: The tsidp v0.0.18 source (`server/extraclaims.go`) merges the `extraClaims` of all matching grants, and removes duplicates from lists, so `groups` is a list. It refuses only the standard and Tailscale claims, and `groups` is not one of them. Grants with `includeInUserInfo` also go to `/userinfo`.

2026-11-08: The role expression was tested with `github.com/jmespath/go-jmespath` v0.4.0 against the resolved compose file. Admin, editor and viewer give their roles. Two groups give the higher role. Another group, an empty list and no `groups` claim give `false`, which strict mode denies. There was no test with a mock provider in Grafana. Do the minerva test after the deploy.

2026-11-08: Deployed. Tailscale sign-in failed at first: the key of the `idp` node had expired, so tsidp did not connect and did not listen. The human disabled key expiry on `idp`, and sign-in worked. The human confirms the role is correct for their user (Admin). A user in `grafana-editors` or `grafana-viewers`, and a user in no group, are not tested yet: those groups are empty.

## Resolution
