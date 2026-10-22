---
title: "Upgrade Jellyfin from 10.11.11 to 12.x"
state: in-progress     # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: medium       # critical | high | medium | low
effort: medium         # small | medium | large | x-large
tags: [jellyfin, feature] # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
created: 2026-10-20
closed:                # YYYY-MM-DD. Set this only when state is closed.
owner: claude          # The person or agent working on the issue. Cleared when the issue returns to open.
approver:              # The person or agent who accepts the issue when it closes.
bookmark: jellyfin-12  # The jj bookmark of the work on the issue. Set this when work starts.
workspaces: [fable]    # jj workspaces where local work on the issue has happened, for example [fix-login-bug].
metadata: {}           # Optional. Arbitrary key-value notes, for example an AI agent session id to resume work with context: {session-id: "abc123"}.
deferred-from:         # Optional. The issue (as a quoted wikilink) or bookmark that deferred this work.
parent:                # Optional. The parent issue (as a quoted wikilink), if this issue is a sub-issue.
depends-on: []           # Optional. Issues (as quoted wikilinks) that must close before this one can start, for example `["[[faster-startup]]"]`.
remote:                # Optional. A URL: the GitHub issue or Jira ticket that tracks this issue outside the repo.
---

# Upgrade Jellyfin from 10.11.11 to 12.x

## Summary

Move the `application` service in `services/jellyfin/docker-compose.yaml` from
`jellyfin/jellyfin:10.11.11` to the latest 12.x image. Jellyfin 12.0 (September 2026)
rewrites the database with no rollback, moves to .NET 10 (every plugin needs a 12 build),
removes the legacy `/emby`/`/mediabrowser` routes, and disables legacy authentication.

## Context

10.11.11 satisfies the upgrade floor (10.10.7+ or any 10.11.x), so the path is direct.
Target the latest 12.x, not 12.0 — 12.1 alone carried 47 server fixes; 12.2 is current as
of 2026-10-05.

Plugin compatibility, validated 2026-10-20:

- **Playback Reporting**: Version 19 targets Jellyfin 12 (`build.yaml` at tag v19:
  `targetAbi: 12.0.0.0`, `framework: net10.0`). Version 18 is the last 10.11 build.
- **Auto Collections** (KeksBombe fork — confirmed by the `TitleMatchPairs` +
  `ExpressionCollections` config fields the enricher manages): releases 0.0.8.0+ target
  Jellyfin 12, 0.0.7.0 is the last 10.11 build. The plugin catalog serves the matching
  release per server version.
- **Moonbase (Moonfin)**: 2.x supports Jellyfin 12 (2.0.0 switched auth for 12's
  legacy-auth removal; scheduled tasks fixed for both 10.11 and 12; 2.3.0 delegates
  recommendation scoring to 12's native similar-items system).

Repo-side exposure, checked 2026-10-20:

- No config references the removed `/emby`/`/mediabrowser` routes; the Tailscale serve
  config proxies the root path.
- The enricher authenticates with the `Authorization: MediaBrowser Token=...` header,
  which Jellyfin 12 keeps. The disabled legacy methods are `X-Emby-Token`,
  `X-MediaBrowser-Token` and the `api_key` query parameter.

## Acceptance criteria

- [ ] The server runs Moonbase 2.x before the upgrade (1.x predates the 12 auth change).
- [ ] Dashboard -> Plugins is checked for plugins beyond the three above; each extra one
      has a 12 build, or Notes tells why it can be dropped.
- [ ] No two user accounts differ only by capitalization (the 12 migration fails on this).
- [ ] A manual ZFS snapshot of `Fast/Configuration` is taken immediately before the image
      tag changes. This snapshot is the only rollback — the migration rewrites the
      database irreversibly.
- [ ] The upgrade runs in an overnight window: the forced full library scan after the
      migration is long and hammers the Vault HDDs. The server is not stopped during the
      migration.
- [x] `services/jellyfin/docker-compose.yaml` pins the new 12.x tag.
- [ ] After the upgrade: all three plugins load, Moonfin clients still see the game
      library, the enricher's auto-collections sync still works, and the Homepage widget
      still authenticates.
- [ ] After the upgrade: Seerr can sign in to Jellyfin, and each Sonarr and Radarr
      connection to Jellyfin (Settings -> Connect), if one exists, passes its test. If one
      fails, Notes tells what was done (see "API clients" in `services/jellyfin/README.md`).

## Out of scope

- The scan schedule and transcode path work. See [[tune-jellyfin-scheduled-tasks]] and
  [[verify-jellyfin-transcode-tmpfs]] — ideally close both before upgrading, so the
  post-upgrade full scan runs against a tuned configuration.

## Notes

2026-10-22: The change on bookmark `jellyfin-12` prepares the upgrade. Do not deploy it until
the acceptance criteria before the upgrade are complete.

- The image tag is `jellyfin/jellyfin:12.2` (released 2026-10-05). Jellyfin 12 uses version
  numbers `12.x` with no third part. The Docker Hub tag `12.2` is that release, and `12` and
  `latest` point to the same image.
- The healthcheck still works: the 12 image installs `curl` and serves `/health`. Its own
  Dockerfile uses the same URL for its `HEALTHCHECK`. The pull for a test in the sandbox
  failed (no disk space), so this comes from the `jellyfin-packaging` Dockerfile, not from a
  running container.
- The healthcheck `start_period` is now 15 minutes, not 2. The migration rewrites the
  database, and the first start can take several minutes on a large library. With 2 minutes,
  the container shows as unhealthy during the migration, and a person can restart it.
- The Homepage widget already has `version: 2`, which the Homepage documentation requires
  for Jellyfin 12. By the same documentation, Jellyfin 10.11 needs `version: 1`, so the widget
  can show errors until the upgrade.
- Seerr: a Jellyfin bug report shows a Seerr login failure when legacy authentication is
  off. The linked Seerr issue (seerr-team/seerr#1925) is closed with no fix. Seerr uses the
  `latest` image, so a fix can already be in it, but this is not confirmed.
- `services/jellyfin/README.md` now lists each client of the Jellyfin API, and tells how to
  turn legacy authentication on again for a short time if a client fails.

## Resolution
