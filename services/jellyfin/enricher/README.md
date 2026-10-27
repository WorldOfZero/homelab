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

Tag names match the `TAG "…"` expressions in `auto-collections.json`. A test checks that every
tag a rule adds is used by at least one collection.

## Auto Collections plugin config (`auto-collections.json`)

Collection definitions for the Auto Collections plugin also live in git, in the **plugin's own
export/import JSON format** (`TitleMatchPairs` + `ExpressionCollections`, every field spelled
out). That means you can:
- **Import it by hand** in the plugin's settings page. This doesn't need the enricher.
- **Edit in the UI, export, and commit** the exported file over `auto-collections.json`.

The enricher also applies it on each run, if the `auto_collections:` block in `config.yaml` is
present:
1. It reads the plugin's configuration (`GET /Plugins/{id}/Configuration`).
2. It replaces `ExpressionCollections` and `TitleMatchPairs` with the file's contents and posts
   the result back. Every other plugin setting is left alone.

The file is **authoritative** for those two keys:
- A collection edited only in the web UI, without exporting and committing it, is overwritten on
  the next run.
- A collection deleted from the file is deleted from the plugin.

`SortBy`/`SortOrder` are the plugin's enum numbers, copied from its UI export. Most collections
use `SortBy: 2`; the decade, James Bond, Babylon 5 and Roger Corman collections use `0`.

After a run that changed the plugin config or any tags (not in dry run), it starts the
plugin's scheduled task (the first task whose name contains `auto_collections.task_name`), so
collections rebuild straight away. If no task matches, it logs a warning and the plugin's own
schedule picks the changes up.

To add a theme collection: add a `rules:` entry in `config.yaml` that produces the tag, then a
`TAG "…"` entry in `auto-collections.json`, and redeploy.

### Collection images (`collection-images/`)

To give a collection its own primary image, add a file named after it to `collection-images/`,
for example `Aviation Collection.jpg`, and redeploy. Collections without a file keep whatever
image Jellyfin gives them. On each run (dry runs only log):

1. If the run started the plugin's task, the enricher waits for it to finish, up to
   `auto_collections.task_wait_minutes` (default 30). That way a collection created by this run
   gets its image now.
2. It uploads each image to the collections with that name (`POST /Items/{id}/Images/Primary`).

An image is uploaded again only when the file changes, or when the collection's image is no
longer the uploaded one. That happens when the plugin recreates the collection, or a refresh
replaces the image. `/data/collection_images.json` records the file hash and Jellyfin's image tag
per collection.

A test checks that every image names a collection in `auto-collections.json`. To stop managing
a collection's image, delete its file; the image it last got stays in Jellyfin.

Environment (set in `../docker-compose.yaml` / Portainer):

| Variable | Default | |
|---|---|---|
| `JELLYFIN_APIKEY` | required | Dashboard → API Keys |
| `JELLYFIN_URL` | `http://127.0.0.1:8096` | Shares the sidecar's network, so localhost is Jellyfin |
| `RUN_AT` | unset (run once and exit) | Daily local time, e.g. `03:00` |
| `RUN_ON_START` | `true` | Also run immediately when the container starts |
| `JELLYFIN_WAIT_MINUTES` | `20` | How long a run waits for Jellyfin to answer `/health` (it is down during a redeploy, longer during a migration) |
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
   `auto-collections.json` and would be deleted, so add any you want to keep first.
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
