---
title: "Sync the Tandoor and Home Assistant shopping lists"
state: in-progress     # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: medium       # critical | high | medium | low
effort: small          # small | medium | large | x-large
tags: [feature, tandoor, home-assistant]
created: 2026-11-08
closed:                # YYYY-MM-DD. Set this only when state is closed.
owner: claude          # The person or agent working on the issue. Cleared when the issue returns to open.
approver:              # The person or agent who accepts the issue when it closes.
bookmark: claude/tandoor-shopping-sync
workspaces: []
metadata: {}
deferred-from:
parent:
depends-on: []
remote:
---

# Sync the Tandoor and Home Assistant shopping lists

## Summary

Keep the Tandoor shopping list and Home Assistant's `todo.shopping_list` the same, in both
directions: adds, check-offs, deletes, and renames.

## Context

Tandoor's own Home Assistant connector (beta) only pushes new Tandoor items to Home Assistant, and
removes them when they are removed in Tandoor. Nothing goes from Home Assistant to Tandoor, and no
Home Assistant integration for Tandoor exists. The Home Assistant side could call the Tandoor API
with `rest_command`, but that needs `configuration.yaml`, which the Home Assistant sync in
homelab-private does not manage, and loops and check-offs are hard to get right in automations.

## Plan

A small service in the `tandoor` stack, `services/tandoor/shopping-sync/`: every minute it reads
both lists, compares them with the pairs it saved last time, and copies the changes. Standard
library Python, tests in `test_shopping_sync.py`. See its README.

## Notes

- 2026-11-08, from the human: chose the sync service over the connector plus a Home Assistant
  automation.
- 2026-11-08: built and tested (unit tests, and one run against a throwaway Tandoor 2.7.2 and Home
  Assistant). To do: create the two tokens and the data folder, deploy with
  `SHOPPING_SYNC_DRY_RUN` unset, read the log, then set it to `false`. Before the tailnet policy
  loses its allow-all grant, add a grant from `tag:cookbook` to `tag:home-assistant` on 443
  (homelab-private, `services/tailscale/policy.hujson`).
