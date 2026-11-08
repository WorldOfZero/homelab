# Shopping list sync (Tandoor and Home Assistant)

`shopping_sync.py` keeps the Tandoor shopping list and a Home Assistant to-do list
(`todo.shopping_list`) the same, in both directions. It runs in the `tandoor` stack as the
`shopping-sync` service, and checks once a minute.

| Change | On one side | Result on the other side |
|---|---|---|
| New item | Tandoor or Home Assistant | The item is added. |
| Checked or unchecked | Tandoor or Home Assistant | The same. |
| Deleted | Tandoor | Removed in Home Assistant. |
| Removed | Home Assistant, not yet checked | Deleted in Tandoor. |
| Removed | Home Assistant, checked ("Clear completed") | Nothing: the checked entry stays in Tandoor's history. |
| Text changed | Tandoor (food, amount, or unit) | Renamed in Home Assistant. |
| Renamed | Home Assistant | The Tandoor entry is replaced with a new one for the new text. Renaming the food would rename it in every recipe. |

## How it works

- **Text.** A Tandoor entry shows in Home Assistant as `Food (amount unit)`, for example
  `Milk (2 l)`, or `Milk` with no amount. This is the same form as Tandoor's own Home Assistant
  connector. An item from Home Assistant becomes a Tandoor entry for a food of that name, with no
  amount.
- **Pairs, no loops.** At the end of each cycle the script saves which Tandoor entry and which
  Home Assistant item are the same item, and how they were (`/data/pairs.json`). The next cycle
  compares each side with that, so it knows which side changed. An item that the script made is
  already paired, so it is never copied back.
- **The first run** pairs items that have the same text on both sides (spaces and case do not
  count) and copies the rest. Checked items are not copied on the first run.
- **Tandoor's list leaves out old checked entries** (older than the "shopping recent days"
  setting). A paired entry that is not in the list is looked up by its id before the script
  removes anything, so an old entry never looks deleted.
- **A failed read changes nothing.** Both lists are read before anything is written. If Tandoor or
  Home Assistant does not answer, the cycle stops and logs the error.
- **Both sides in the same minute.** A check cannot conflict: if both sides changed it, both
  flipped it the same way. If both sides changed the text, Tandoor's text wins.

## Setup

1. **Tandoor API token.** In Tandoor: Settings, API, new token with the scope `read write`. The
   token's user must be in the household whose shopping list to sync. Set it as
   `TANDOOR_SHOPPING_SYNC_TOKEN` in the Portainer stack.
2. **Home Assistant token.** In Home Assistant: your profile, Security, Long-lived access tokens.
   Set it as `HA_SHOPPING_SYNC_TOKEN`. A user that is not an administrator is enough.
3. **Data folder.** Create `/mnt/Fast/Configuration/tandoor/shopping-sync`, owned by `1000:1000`.
4. **Dry run first.** `SHOPPING_SYNC_DRY_RUN` is `true` if not set: the service logs what it
   would do and writes nothing. Check the log (`docker logs tandoor-shopping-sync`), then set
   `SHOPPING_SYNC_DRY_RUN=false`.
5. **Do not also turn on Tandoor's Home Assistant connector** (Settings, Connectors) for the same
   list. Both would add Tandoor items to Home Assistant.

The service shares the Tandoor sidecar's network (`network_mode: service:tailscale`). It reaches
Tandoor on `127.0.0.1:9001` with the `Host` header `tandoor.comet-stork.ts.net` (Django refuses
other host names), and Home Assistant at `https://homeassistant.comet-stork.ts.net` over the
tailnet, as the Tandoor node. When the tailnet policy loses its allow-all grant, it needs a grant
from the Tandoor node's tag (`tag:cookbook`) to `tag:home-assistant` on 443.

## Settings

| Variable | Default | Meaning |
|---|---|---|
| `TANDOOR_URL` | (set in compose) | Tandoor's address. |
| `TANDOOR_HOST` | (set in compose) | The `Host` header for Tandoor, if the URL is not a name in `ALLOWED_HOSTS`. |
| `TANDOOR_TOKEN` | | Tandoor API token (`read write`). |
| `HA_URL` | (set in compose) | Home Assistant's address. |
| `HA_TOKEN` | | Home Assistant long-lived access token. |
| `HA_TODO_ENTITY` | `todo.shopping_list` | The to-do list to sync. |
| `SYNC_INTERVAL` | `60` | Seconds between checks. |
| `STATE_FILE` | `/data/pairs.json` | The saved pairs. Delete it to start again as a first run. |
| `DRY_RUN` | `true` | `false` to write. |

## Tests

```
python -m unittest -v test_shopping_sync
```

The tests run each rule in the table against in-memory lists, and the HTTP clients against fake
servers. Also tested by hand once, on 2026-11-08, against a throwaway Tandoor 2.7.2 container and a
throwaway Home Assistant with the Shopping list integration: the first-run pairing, adds, checks,
deletes on both sides, "Clear completed", and a quiet cycle with no writes.

## Limits

- Tandoor shopping lists (the named lists in Tandoor 2) are not kept apart: every entry the token's
  user can see goes to the one Home Assistant list, and Home Assistant items go to no named list.
- An item added with the same text on both sides in the same minute becomes one item.
- A change made on a side less than a minute before the other side deletes the item can be lost.
