# Metadata services

## themearr

Movie-only theme song (`theme.mp3`) downloader — no Sonarr/TV integration exists upstream, just
Plex and Radarr as library sources. After first boot (`https://themearr.<tailnet>`, token from the
`THEMEARR_AUTH_TOKEN` secret):

1. Pick Radarr as the library source (URL + Radarr's own API key, entered in Themearr's own
   Settings — not a compose env var) unless you'd rather sign in with Plex.
2. **Settings → RapidAPI**: add a [youtube-mp36](https://rapidapi.com/ytjar/api/youtube-mp36) key
   + username — downloads silently no-op without this, even though browsing/syncing works fine.
3. **Settings → Library Paths**: the compose file mounts the whole `/mnt/Vault/Media` tree at
   `/data` (matching every other `arr/` service here) — add `/data` as a Local Library Path, then
   add a Path Mapping translating whatever path Radarr/Plex report for movies into wherever they
   actually live under `/data`. Getting this wrong is the most common setup mistake (shows up as
   `Skipping <title> — unresolved path` in the sync log) — see Themearr's own README for the full
   explanation if sync is skipping titles.
4. **Radarr → Settings → Connect → Add → Webhook**: trigger **On Import** (and **On Upgrade** if
   wanted), URL `http://themearr:8080/api/webhook/radarr`, method `POST`, header `X-Api-Key` set to
   the key from Themearr's own **Settings → API key** — fetches the theme the moment Radarr imports
   a movie instead of waiting for the next scheduled sync. Press **Test** in Radarr's webhook form
   to confirm the URL/key before relying on it.