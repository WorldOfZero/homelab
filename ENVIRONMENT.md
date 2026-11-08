# Environment Variables

Every `${VAR}` referenced across `services/**/docker-compose.yaml`, in one place. This exists
because these values are currently supplied entirely through Portainer's per-stack "Environment
variables" UI, which is not visible in git — see [Improvements.md](Improvements.md) §12. **No
real values live here** — this is a catalog of what each stack needs and where it should come
from, not a place to paste actual secrets. Update this file whenever a compose file starts
referencing a new variable, or stops referencing one.

## How to read the "Where" column

- **Portainer (secret)** — set only in that stack's Portainer "Environment variables" field.
  Never commit a real value for these.
- **Portainer (shared, if supported)** — same value reused across many stacks; a candidate for
  Portainer environment/endpoint-level shared variables instead of re-entering it per stack, if
  your Portainer edition supports that scope.
- **Env file candidate** — not secret; a reasonable candidate for a committed, non-secret
  `stack.env`-style file per service (see the `services/factorio/stack.env` precedent), so it's
  documented in git instead of only in Portainer. Not yet split out for these — see
  Improvements.md §12.
- **Auto (not user-set)** — supplied automatically by the tool itself at runtime, not something
  to configure in Portainer at all.
- **Dead / template leftover** — not meaningfully used; candidate for removal.

## Tailscale

| Variable | Used by | Secret? | Where |
|---|---|---|---|
| `TS_AUTHKEY` | Sidecar in nearly every service: `airtrail`, `arr/bazarr`, `arr/radarr`, `arr/seerr`, `arr/sonarr`, `arr/themearr`, `gamescores`, `grafana`, `homepage`, `jellyfin`, `karakeep`, `kavita`, `kuma`, `movie-night`, `ollama`, `tailscale-idp` (sidecar + `tsidp` app), `tandoor`, `wallos` | Yes | Portainer (shared, if supported) |
| `TAILSCALE_AUTH_TOKEN` | `tailscale` (the main tailnet node) — same purpose as `TS_AUTHKEY` above, different name; see Improvements.md §8 | Yes | Portainer (shared, if supported) |
| `TS_CERT_DOMAIN` | Every sidecar's `ts-serve` config (`services/*/docker-compose.yaml`, the `configs:` block) | No | Auto (not user-set) — supplied by Tailscale itself; the `$$` escaping in those files is deliberate, don't "fix" it into a Portainer variable |

`TS_AUTHKEY` is, as far as this repo shows, the same value pasted into ~14 separate stacks. See
Improvements.md §12 for reducing that to a short-lived, tag-scoped OAuth-issued key instead of one
long-lived reusable secret.

### Host prerequisite: the `tailnet-local` network

Every sidecar listed above also joins an external Docker network called `tailnet-local`, which
must exist on the host before any of those stacks will deploy:

```bash
sudo docker network create tailnet-local
```

Without it, each sidecar sits alone on its stack's default bridge behind Docker's NAT, and two
sidecars on the same host can't reach each other directly — the router doesn't hairpin and offers
no port mapping — so tailscaled falls back to relaying through DERP (observed: Kuma → Jellyfin via
`DERP(sfo)`, "direct connection not established"). On the shared network each sidecar has an
address the others can reach, and tailscaled uses it as a direct endpoint. Check with
`sudo docker exec tailscale-kuma tailscale ping jellyfin` — it should say `via 172.x.x.x:…`, not
`via DERP`.

## Per-service secrets

| Variable | Used by | Secret? | Where |
|---|---|---|---|
| `PLEX_CLAIM_TOKEN` | `plex` | Yes (one-time claim token from plex.tv/claim) | Portainer (secret) |
| `PLEX_TOKEN` | `plex` (the `plex-prometheus` exporter) | Yes | Portainer (secret) |
| `NEXTAUTH_SECRET` | `karakeep` | Yes | Portainer (secret) |
| `MEILI_MASTER_KEY` | `karakeep` (both the `web` app and `meilisearch`) | Yes | Portainer (secret) |
| `NEXTAUTH_URL` | `karakeep` | No — just a URL | Env file candidate |
| `SECRET_KEY` | `tandoor` (Django secret key) | Yes | Portainer (secret) |
| `POSTGRES_PASSWORD` | `tandoor` (`application`, `db`, `backup`), `movie-night` (`application`, `db`, `backup` — use only URL-safe characters, because it goes into `DATABASE_URL`), `airtrail` (as `DB_PASSWORD` there — `db`, `backup`) | Yes | Portainer (secret) |
| `POSTGRES_USER` | `tandoor` (`application`, `db`, `backup`), `movie-night` (`application`, `db`, `backup`), `airtrail` (as `DB_USERNAME` there — `db`, `backup`) | Borderline — a username alone, low sensitivity | Env file candidate |
| `POSTGRES_DB` | `tandoor` (`application`, `db`, `backup`), `movie-night` (`application`, `db`, `backup`), `airtrail` (as `DB_DATABASE_NAME` there — `db`, `backup`) | No — just a database name | Env file candidate |
| `DB_USERNAME` | `airtrail` (`db`, `backup`) | Borderline, same as `POSTGRES_USER` above | Env file candidate |
| `DB_DATABASE_NAME` | `airtrail` (`db`, `backup`) | No | Env file candidate |
| `DB_URL` | `airtrail` (app connection string) | Depends on format — confirm it doesn't embed the password inline before treating as non-secret; `DB_PASSWORD` is already passed separately, so it likely doesn't | Portainer (secret) until confirmed otherwise |
| `CURSEFORGE_API_KEY` | `minecraft` | Yes | Portainer (secret) |
| `OLLAMA_API_KEY` | `ollama` (currently commented out / optional) | Yes, if enabled | Portainer (secret) |
| `THEMEARR_AUTH_TOKEN` | `arr/themearr` | Yes — the API refuses to start without it; generate with `openssl rand -hex 32` | Portainer (secret) |
| `JELLYFIN_APIKEY` | `jellyfin` (the `enricher` service) | Yes | Portainer (secret) |
| `ENRICHER_DRY_RUN` | `jellyfin` (`enricher`) — defaults to `true` (log only); set `false` once the dry-run log looks right. See `services/jellyfin/enricher/README.md` | No | Portainer |

`tandoor`'s `POSTGRES_HOST`/`POSTGRES_PORT` used to be Portainer-set variables pointing at an
external supabase database; as of 9/20/2026 they're now hardcoded to `db`/`5432` in the compose file instead, since
`tandoor` owns its own postgres container now (see the Backups section below) and that value can
never meaningfully be anything else. One less thing to configure.

## Postgres backups

All self-hosted postgres instances (`tandoor`, `airtrail`, `movie-night`) now have a `backup` sidecar
(`prodrigestivill/postgres-backup-local`) doing daily `pg_dump` snapshots into a `backups/`
subdirectory next to each database's data directory, with 7 daily / 4 weekly / 6 monthly
retention (the image's own defaults). See Improvements.md §14.

## Grafana alerting

| Variable | Used by | Secret? | Where |
|---|---|---|---|
| `DISCORD_WEBHOOK_URL` | `grafana` — expanded into `services/grafana/grafana/provisioning/alerting/discord.yaml` | Yes — anyone with the URL can post to the channel | Portainer (secret) |

## Grafana login

| Variable | Used by | Secret? | Where |
|---|---|---|---|
| `GRAFANA_OIDC_CLIENT_ID` | `grafana` — the tsidp client | No | Portainer |
| `GRAFANA_OIDC_CLIENT_SECRET` | `grafana` — the tsidp client | Yes | Portainer (secret) |

## Media metrics exporters

Each exportarr sidecar needs the API key of its application, set on the stack of that application.
See `services/grafana/README.md` for `SONARR_APIKEY` and `RADARR_APIKEY`.

| Variable | Used by | Secret? | Where |
|---|---|---|---|
| `SONARR_APIKEY` | `arr/sonarr` (`exporter`) | Yes | Portainer (secret) |
| `RADARR_APIKEY` | `arr/radarr` (`exporter`) | Yes | Portainer (secret) |
| `BAZARR_APIKEY` | `arr/bazarr` (`exporter`) | Yes | Portainer (secret) |

`jellyfin` (`exporter`) uses the existing `JELLYFIN_APIKEY`.

## Karakeep metrics

| Variable | Used by | Secret? | Where |
|---|---|---|---|
| `KARAKEEP_PROMETHEUS_TOKEN` | `karakeep` and `grafana` — must have the same value in both stacks. Generate it with `openssl rand -hex 32`. | Yes | Portainer (secret) |

## last.fm

Optional. Without these, the last.fm panels stay empty, and the rest of the stack works.

| Variable | Used by | Secret? | Where |
|---|---|---|---|
| `LASTFM_API_KEY` | `grafana` (`lastfm-exporter`) | Yes | Portainer (secret) |
| `LASTFM_USER` | `grafana` (`lastfm-exporter`) | No | Portainer |

## Tandoor login

| Variable | Used by | Secret? | Where |
|---|---|---|---|
| `TANDOOR_SOCIALACCOUNT_PROVIDERS` | `tandoor` — the tsidp client, as JSON on one line. It contains the client secret. | Yes | Portainer (secret) |

## Movie Night

| Variable | Used by | Secret? | Where |
|---|---|---|---|
| `MOVIE_NIGHT_VERSION` | `movie-night` — the image tag, without the `v`. Use `0.0.34` or later. | No | Portainer |
| `MOVIE_NIGHT_JELLYFIN_APIKEY` | `movie-night` — its own Jellyfin API key. Do not share it with other services. | Yes | Portainer (secret) |
| `MOVIE_NIGHT_JELLYFIN_LIBRARIES` | `movie-night` — the ItemIds of the movie libraries, separated by commas | No | Portainer |

Jellyfin 12 does not accept `X-Emby-Token` or `api_key`. To list the library ids, use this command:

```bash
curl -s -H 'Authorization: MediaBrowser Token="<key>"' https://jellyfin.comet-stork.ts.net/Library/VirtualFolders
```

## Cloudflare Tunnel

Each published stack has its own tunnel and token. Do not use one token for two stacks.

| Variable | Used by | Secret? | Where |
|---|---|---|---|
| `GAMESCORES_TUNNEL_TOKEN` | `gamescores` (`cloudflared`) — the tunnel for `games.worldofzero.com` | Yes | Portainer (secret) |
| `MOVIE_NIGHT_TUNNEL_TOKEN` | `movie-night` (`cloudflared`) — the tunnel for `movie-night.worldofzero.com` | Yes | Portainer (secret) |

To make a tunnel, go to Cloudflare Zero Trust, then Networks, then Tunnels, and select Create a tunnel (Cloudflared).
Copy the token from the `docker run` command that the dashboard shows. Then add a public hostname:

| Tunnel | Hostname | Service |
|---|---|---|
| gamescores | `games.worldofzero.com` | `http://127.0.0.1:8080` |
| movie-night | `movie-night.worldofzero.com` | `http://127.0.0.1:8080` |

Never route `127.0.0.1:8081` of movie-night through a tunnel. Host sign-in and the metrics are on that port.

## Homepage dashboard API keys

`homepage` has only links, so it needs no API keys. You can remove these variables from its Portainer
stack: `JELLYFIN_APIKEY`, `KAVITA_APIKEY`, `RADARR_APIKEY`, `SEERR_APIKEY`, `SONARR_APIKEY`,
`WALLOS_APIKEY` and `TS_APIKEY`.

## Dead / template leftovers

| Variable | Found in | Notes |
|---|---|---|
| `SERVICE` | `services/factorio/stack.env` only now (elsewhere fixed by `fix/undefined-service-var` in this stack) | Was silently undefined everywhere except `factorio`; no longer relied on anywhere else. See Improvements.md §4. |
| `SERVICEPORT` | Commented-out `#ports:` lines in most sidecars | Dead — the line it's part of is commented out in every file. Candidate for deleting the whole commented block rather than documenting the variable. |
| `DNS_SERVER` | Commented-out `#dns:` lines in most sidecars | Same as `SERVICEPORT` — dead, commented-out template leftover. |
