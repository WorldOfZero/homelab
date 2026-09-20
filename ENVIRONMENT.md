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
| `TS_AUTHKEY` | Sidecar in nearly every service: `airtrail`, `arr/bazarr`, `arr/radarr`, `arr/seerr`, `arr/sonarr`, `homepage`, `jellyfin`, `karakeep`, `kavita`, `kuma`, `ollama`, `tailscale-idp` (sidecar + `tsidp` app), `tandoor`, `wallos` | Yes | Portainer (shared, if supported) |
| `TAILSCALE_AUTH_TOKEN` | `tailscale` (the main tailnet node) — same purpose as `TS_AUTHKEY` above, different name; see Improvements.md §8 | Yes | Portainer (shared, if supported) |
| `TS_CERT_DOMAIN` | Every sidecar's `ts-serve` config (`services/*/docker-compose.yaml`, the `configs:` block) | No | Auto (not user-set) — supplied by Tailscale itself; the `$$` escaping in those files is deliberate, don't "fix" it into a Portainer variable |

`TS_AUTHKEY` is, as far as this repo shows, the same value pasted into ~14 separate stacks. See
Improvements.md §12 for reducing that to a short-lived, tag-scoped OAuth-issued key instead of one
long-lived reusable secret.

## Per-service secrets

| Variable | Used by | Secret? | Where |
|---|---|---|---|
| `PLEX_CLAIM_TOKEN` | `plex` | Yes (one-time claim token from plex.tv/claim) | Portainer (secret) |
| `PLEX_TOKEN` | `plex` (the `plex-prometheus` exporter) | Yes | Portainer (secret) |
| `NEXTAUTH_SECRET` | `karakeep` | Yes | Portainer (secret) |
| `MEILI_MASTER_KEY` | `karakeep` (both the `web` app and `meilisearch`) | Yes | Portainer (secret) |
| `NEXTAUTH_URL` | `karakeep` | No — just a URL | Env file candidate |
| `SECRET_KEY` | `tandoor` (Django secret key) | Yes | Portainer (secret) |
| `POSTGRES_PASSWORD` | `tandoor` (`application`, `db`, `backup`), `airtrail` (as `DB_PASSWORD` there — `db`, `backup`) | Yes | Portainer (secret) |
| `POSTGRES_USER` | `tandoor` (`application`, `db`, `backup`), `airtrail` (as `DB_USERNAME` there — `db`, `backup`) | Borderline — a username alone, low sensitivity | Env file candidate |
| `POSTGRES_DB` | `tandoor` (`application`, `db`, `backup`), `airtrail` (as `DB_DATABASE_NAME` there — `db`, `backup`) | No — just a database name | Env file candidate |
| `DB_USERNAME` | `airtrail` (`db`, `backup`) | Borderline, same as `POSTGRES_USER` above | Env file candidate |
| `DB_DATABASE_NAME` | `airtrail` (`db`, `backup`) | No | Env file candidate |
| `DB_URL` | `airtrail` (app connection string) | Depends on format — confirm it doesn't embed the password inline before treating as non-secret; `DB_PASSWORD` is already passed separately, so it likely doesn't | Portainer (secret) until confirmed otherwise |
| `CURSEFORGE_API_KEY` | `minecraft` | Yes | Portainer (secret) |
| `OLLAMA_API_KEY` | `ollama` (currently commented out / optional) | Yes, if enabled | Portainer (secret) |

`tandoor`'s `POSTGRES_HOST`/`POSTGRES_PORT` used to be Portainer-set variables pointing at an
external supabase database; as of 9/20/2026 they're now hardcoded to `db`/`5432` in the compose file instead, since
`tandoor` owns its own postgres container now (see the Backups section below) and that value can
never meaningfully be anything else. One less thing to configure.

## Postgres backups

Both self-hosted postgres instances (`tandoor`, `airtrail`) now have a `backup` sidecar
(`prodrigestivill/postgres-backup-local`) doing daily `pg_dump` snapshots into a `backups/`
subdirectory next to each database's data directory, with 7 daily / 4 weekly / 6 monthly
retention (the image's own defaults). See Improvements.md §14.

## Grafana alerting

| Variable | Used by | Secret? | Where |
|---|---|---|---|
| `DISCORD_WEBHOOK_URL` | `grafana` — expanded into `services/grafana/grafana/provisioning/alerting/discord.yaml` | Yes — anyone with the URL can post to the channel | Portainer (secret) |

## Homepage dashboard API keys

`homepage` pulls read-only status/API keys from six other services to populate its dashboard.
Each is still a live credential for that service, even though its blast radius is smaller
(typically read-only):

| Variable | Feeds | Secret? | Where |
|---|---|---|---|
| `JELLYFIN_APIKEY` | Jellyfin API key | Yes | Portainer (secret) |
| `KAVITA_APIKEY` | Kavita API key | Yes | Portainer (secret) |
| `RADARR_APIKEY` | Radarr API key | Yes | Portainer (secret) |
| `SEERR_APIKEY` | Seerr API key | Yes | Portainer (secret) |
| `SONARR_APIKEY` | Sonarr API key | Yes | Portainer (secret) |
| `WALLOS_APIKEY` | Wallos API key | Yes | Portainer (secret) |
| `TS_APIKEY` | Tailscale API key (for `homepage`'s Tailscale widget) | Yes | Portainer (secret) |

## Dead / template leftovers

| Variable | Found in | Notes |
|---|---|---|
| `SERVICE` | `services/factorio/stack.env` only now (elsewhere fixed by `fix/undefined-service-var` in this stack) | Was silently undefined everywhere except `factorio`; no longer relied on anywhere else. See Improvements.md §4. |
| `SERVICEPORT` | Commented-out `#ports:` lines in most sidecars | Dead — the line it's part of is commented out in every file. Candidate for deleting the whole commented block rather than documenting the variable. |
| `DNS_SERVER` | Commented-out `#dns:` lines in most sidecars | Same as `SERVICEPORT` — dead, commented-out template leftover. |
