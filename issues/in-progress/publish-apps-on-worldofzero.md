---
title: "Publish GameScores and movie-night on worldofzero.com"
state: in-progress     # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: medium       # critical | high | medium | low
effort: small          # small | medium | large | x-large
tags: [feature, gamescores, movie-night, cloudflare] # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
created: 2026-11-06
closed:                # YYYY-MM-DD. Set this only when state is closed.
owner: claude          # The person or agent working on the issue. Cleared when the issue returns to open.
approver:              # The person or agent who accepts the issue when it closes.
bookmark: cloudflare-tunnel # The jj bookmark of the work on the issue. Set this when work starts.
workspaces: [fable]    # jj workspaces where local work on the issue has happened, for example [fix-login-bug].
metadata: {}           # Optional. Arbitrary key-value notes, for example an AI agent session id to resume work with context: {session-id: "abc123"}.
deferred-from:         # Optional. The issue (as a quoted wikilink) or bookmark that deferred this work.
parent:                # Optional. The parent issue (as a quoted wikilink), if this issue is a sub-issue.
depends-on: []           # Optional. Issues (as quoted wikilinks) that must close before this one can start, for example `["[[faster-startup]]"]`.
remote:                # Optional. A URL: the GitHub issue or Jira ticket that tracks this issue outside the repo.
---

# Publish GameScores and movie-night on worldofzero.com

## Summary

Publish GameScores as `games.worldofzero.com` and movie-night as `movie-night.worldofzero.com`, so that guests get short names on the domain of the project.

## Context

Guests reach GameScores and movie-night through Tailscale Funnel on comet-stork.ts.net names. Funnel cannot serve a custom domain. A cloudflared container in each stack publishes the application port through a Cloudflare Tunnel as games.worldofzero.com and movie-night.worldofzero.com, with no open router port.

## Acceptance criteria

- [x] `docker compose config` passes for `gamescores`, `movie-night` and `grafana`.
- [x] The human moves the DNS of `worldofzero.com` to Cloudflare, if it is not there.
- [x] The human makes two tunnels with the public hostnames in ENVIRONMENT.md, and sets `GAMESCORES_TUNNEL_TOKEN` and `MOVIE_NIGHT_TUNNEL_TOKEN` in the Portainer stacks.
- [x] Both stacks deploy, and the `cloudflared` logs show four registered tunnel connections.
- [ ] `https://games.worldofzero.com` works from outside the tailnet, and a room syncs live between two devices.
- [ ] `https://movie-night.worldofzero.com/healthz` works from outside the tailnet. The share links and QR codes use the new name.
- [x] `https://movie-night.worldofzero.com` does not serve the host routes, and port 8081 is not reachable through it.
- [x] `curl -N https://movie-night.worldofzero.com/api/rooms/<code>/display/events` prints a state event, then a ping each 15 seconds.
- [ ] The rate limits of movie-night see each guest as a separate address.
- [x] Prometheus shows the two `cloudflared` targets as up, and the blackbox probes of the new URLs succeed.

- [ ] Funnel is off on the two stacks, so each application has only one public path. `https://gamescores.comet-stork.ts.net` and `https://movie-night.comet-stork.ts.net` do not load from outside the tailnet, and still load on the tailnet.
- [ ] The human removes the three `funnel` entries from `nodeAttrs` in the tailnet policy.

## Out of scope

- Making the tailnet policy narrower than allow-all. That is separate work.

## Notes

2026-11-06: Fastly was compared with Cloudflare. Fastly has no tunnel, so it needs an origin that is on the internet: an open router port or the Funnel name. Cloudflare Tunnel needs neither.

2026-11-06: The `cloudflared` container shares the network of the Tailscale sidecar, as the application does, so it reaches the application on `127.0.0.1:8080`. Its metrics are on port 2000. `TRUSTED_PROXIES=127.0.0.1` of movie-night does not change, because `cloudflared` also connects from localhost and sets `X-Forwarded-For`.

2026-11-06: Both tunnels are connected and have the correct ingress rules. Prometheus scrapes both `cloudflared` targets. `1.1.1.1` resolves `games.worldofzero.com` to Cloudflare. The router and MagicDNS still cache the NXDOMAIN from before the records existed, so the probes fail until that expires. With `curl --resolve` to a Cloudflare address, `/healthz` returns `Healthy` for GameScores and `{"status":"ok","version":"0.0.64","database":"ok"}` for movie-night.

2026-11-06: The router cache expired at about 15:45 PST. Both names load in Firefox, and both blackbox probes return 200. The application log shows the tunnel requests on the `public` listener. The log does not include the client address, so the rate-limit check needs a test with two devices.

2026-11-06: From minerva, `/metrics` on the public name returns 404, and port 8081 does not connect (`000`). It is not yet checked that `:8443` on the public name shows the guest page and not the host sign-in.

2026-11-06: `:8443` on the public name shows the guest page, because Cloudflare sends it to port 8080 through the tunnel. The display stream sends the state event through the tunnel, and its `joinUrl` uses the new name. Later the same day, the stream showed the state event and then four pings, so Cloudflare does not buffer it.

2026-11-08: Funnel is off in both stacks. Serve stays on, so the `comet-stork.ts.net` names still work on the tailnet. No blackbox probe uses those names now.

## Resolution

<Complete this section when you close the issue.
- Completed: tell what was done. Link to the changelog version and the decision records, for example `[[0.0.5]]`.
- Abandoned: tell why the work stopped. Link to the issue or decision that replaces it, if one exists.>
