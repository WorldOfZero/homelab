---
title: "Run the movie-night service in the homelab"
state: in-progress     # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: medium       # critical | high | medium | low
effort: small          # small | medium | large | x-large
tags: [feature, movie-night] # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
created: 2026-11-03
closed:                # YYYY-MM-DD. Set this only when state is closed.
owner: claude          # The person or agent working on the issue. Cleared when the issue returns to open.
approver:              # The person or agent who accepts the issue when it closes.
bookmark: movie-night-stack # The jj bookmark of the work on the issue. Set this when work starts.
workspaces: [fable]    # jj workspaces where local work on the issue has happened, for example [fix-login-bug].
metadata: {}           # Optional. Arbitrary key-value notes, for example an AI agent session id to resume work with context: {session-id: "abc123"}.
deferred-from:         # Optional. The issue (as a quoted wikilink) or bookmark that deferred this work.
parent:                # Optional. The parent issue (as a quoted wikilink), if this issue is a sub-issue.
depends-on: []           # Optional. Issues (as quoted wikilinks) that must close before this one can start, for example `["[[faster-startup]]"]`.
remote:                # Optional. A URL: the GitHub issue or Jira ticket that tracks this issue outside the repo.
---

# Run the movie-night service in the homelab

## Summary

Add a stack for the movie-night voting service, with a public Funnel port for guests and a tailnet port for hosts and the TV.

## Context

Run [WorldOfZero/movie-night](https://github.com/WorldOfZero/movie-night) as the stack `services/movie-night`. It follows the Tandoor pattern: a Tailscale sidecar, Postgres and a daily backup. The design and the application issues are in the movie-night repo.

## Acceptance criteria

- [x] `docker compose config` passes with all variables set.
- [ ] The human pushes the image tag (`0.0.34` or later), and sets the Tailscale policy, the Jellyfin API key, the library ids and the Portainer variables.
- [ ] The tailnet policy lets users and the Shield reach only `movie-night:443` and `:8443`, and lets the Grafana node reach `:443` for the probe. Prometheus reaches `:8081` through the Docker network.
- [ ] The stack starts, all containers are healthy, and the application log shows that the migrations ran.
- [ ] `/healthz` on port 443 works from outside the tailnet.
- [ ] From outside the tailnet, the host sign-in route and port 8443 are not reachable.
- [ ] On port 8443, a Jellyfin user can sign in and create a room, and search finds only movies.
- [ ] `curl -N https://movie-night.comet-stork.ts.net/api/rooms/<code>/display/events` prints a state event, then a ping each 15 seconds.
- [ ] Prometheus shows the `movie-night` target and the sidecar target as up, and the blackbox probe succeeds.
- [ ] A backup file is in the backups directory after the first scheduled run. If the run fails, set the owner of the directory to the UID that the log shows.
- [ ] Vote counts show on phones, and not on the TV page.
- [ ] The rate limits see each guest as a separate address. If they do not, `TRUSTED_PROXIES` is wrong.
- [ ] On the Shield, the `/tv` page loads, the muted trailer plays, and the play buttons start Moonfin or Jellyfin.

## Out of scope

- The application. It is in the movie-night repo.
- A Grafana dashboard and a backup alert for the service. Add them after the first movie night works.

## Notes

2026-11-03: From the human: a spec for this stack, based on `deploy/homelab-stack.patch` in the movie-night repo.

2026-11-03: The patch is not available in the sandbox, because the repo is private and the sandbox has no GitHub credentials. The stack was written from the spec and the Tandoor stack, so compare it with the patch.

2026-11-03: From the movie-night agent: the application does not assume that callers come through Serve. It uses `X-Forwarded-For` only from `TRUSTED_PROXIES`, host routes need a Jellyfin sign-in, and `/metrics` is the only route on port 8081 without authentication, with counters and no room data. A sign-in directly on port 8081 is not encrypted on the Docker network. The container names, the required variables, the homepage text and the library URL match the patch. The compose file has not been compared with the patch line by line.

## Resolution

