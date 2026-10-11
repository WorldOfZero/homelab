# jellyfin-enricher

Adds metadata to Jellyfin items from sources Jellyfin doesn't use itself. It never removes
anything. Right now it does one thing: it looks up each movie's and series' **IMDb keywords**
and appends tags (or genres) according to `config.yaml`.

Why: Jellyfin's tags come only from TMDb keywords, which are sparse. The Auto Collections plugin's
`TAG "heist"` rule misses most heist films because TMDb never tagged them. On Plex, Kometa's
`imdb_keyword` filter matched against IMDb's crowd-sourced keywords instead. This brings that
back by writing the tags, so any tag-based collection tool (Auto Collections, SmartLists) picks
them up.

## How it works

1. It lists every `Movie`/`Series` in Jellyfin that has an IMDb id.
2. It gets each title's IMDb keywords, with the vote counts ("N of M found this relevant").
   Sources are tried in order:
   - `kometa`: Kometa's public IMDb keyword service (`utilities.kometa.wiki/imdb-service`), the
     same backend Kometa's `imdb_keyword` filter uses.
   - `imdb`: a fallback that parses the `__NEXT_DATA__` JSON on
     `imdb.com/title/<id>/keywords/`. The page layout isn't a stable API, so this is best effort.

   Results are cached in `/data/imdb_keywords.json` for `cache_days` (default 30). After the
   first run, only new titles are looked up. Lookups run at ~1/s and at most
   `max_lookups_per_run` per run, so a big library fills in over a few nights.
3. For each rule whose `imdb_keywords` match, it appends the rule's `add.tags` /
   `add.genres` to the item. Matching ignores case and treats `-` and space the same. It skips
   values the item already has, and sends the full item back so nothing else changes.

## Config

`config.yaml` (baked into the image; redeploy the stack to pick up changes):

```yaml
rules:
  - match: {imdb_keywords: [heist, bank heist, bank robbery]}
    add: {tags: [heist]}
  - match: {imdb_keywords: [vampire], min_votes: 3}   # optional vote thresholds
    add: {tags: [vampire], genres: [Horror]}
```

Tag names match the `TAG "…"` expressions in `auto-collections.yaml`. A test checks that every
tag a rule adds is used by at least one collection.

## Auto Collections plugin config (`auto-collections.yaml`)

Collection definitions for the Auto Collections plugin also live in git. Each run starts by
reading the plugin's configuration (`GET /Plugins/{id}/Configuration`). It replaces
`ExpressionCollections` and `TitleMatchPairs` with the file's contents and posts the result back.
Every other plugin setting is left alone. The file is **authoritative** for those two keys:
- A collection edited in the plugin's web UI is overwritten on the next run.
- A collection deleted from the file is deleted from the plugin.

`expression_defaults` fills in `CaseSensitive`/`SortBy`/`SortOrder` for entries that don't set
them. `SortBy`/`SortOrder` are the plugin's enum numbers, copied from its UI export.

After a run that changed the plugin config or any tags (not in dry run), it starts the
plugin's scheduled task (the first task whose name contains `plugin.task_name`), so collections
rebuild straight away. If no task matches, it logs a warning and the plugin's own schedule picks
the changes up.

To add a theme collection: add a `rules:` entry in `config.yaml` that produces the tag, then a
`TAG "…"` entry in `auto-collections.yaml`, and redeploy.

Environment (set in `../docker-compose.yaml` / Portainer):

| Variable | Default | |
|---|---|---|
| `JELLYFIN_APIKEY` | required | Dashboard → API Keys |
| `JELLYFIN_URL` | `http://127.0.0.1:8096` | Shares the sidecar's network, so localhost is Jellyfin |
| `RUN_AT` | unset (run once and exit) | Daily local time, e.g. `03:00` |
| `RUN_ON_START` | `true` | Also run immediately when the container starts |
| `DRY_RUN` | `true` | Logs `would update …` without writing; compose maps `ENRICHER_DRY_RUN` |
| `TZ`, `LOG_LEVEL`, `DATA_DIR` | `UTC`, `INFO`, `/data` | |

## First deploy

```bash
sudo install -d -o 1000 -g 1000 /mnt/Fast/Configuration/jellyfin/enricher
```

1. Create an API key in Jellyfin. Set `JELLYFIN_APIKEY` on the jellyfin stack in Portainer.
2. Deploy with the default `DRY_RUN=true`, then read `sudo docker logs -f jellyfin-enricher` and
   check the `would update` lines look right. That includes the `auto collections: would update
   plugin config: +[…] -[…] ~[…]` line. `-[…]` lists collections in the plugin that aren't in
   `auto-collections.yaml` and would be deleted, so add any you want to keep first.
3. Set `ENRICHER_DRY_RUN=false` and redeploy. Collections fill in on Auto Collections' next run.

Run it by hand: `sudo docker exec jellyfin-enricher python /app/enricher.py --once [--dry-run]`.

## Caveats

- Added tags aren't locked. A "Replace all metadata" refresh in Jellyfin resets an item's tags to
  TMDb's, and the next nightly run adds them back.
- Removing a rule doesn't remove tags it already added.
- Both keyword sources are unofficial. If both fail for a title, it isn't cached and is retried
  the next night. A broken source shows up as `keyword source … failed` warnings in the log.

## Tests

```bash
cd services/jellyfin/enricher && python3 -m unittest -v test_enricher
```

The tests use an in-process fake of Jellyfin, the Kometa service and the IMDb page. Needs
`pyyaml`.
