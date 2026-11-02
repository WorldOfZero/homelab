---
title: "Make Homepage a simple list of links"
state: in-progress     # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: medium       # critical | high | medium | low
effort: small          # small | medium | large | x-large
tags: [feature, homepage] # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
created: 2026-11-02
closed:                # YYYY-MM-DD. Set this only when state is closed.
owner: claude          # The person or agent working on the issue. Cleared when the issue returns to open.
approver:              # The person or agent who accepts the issue when it closes.
bookmark: homepage-links # The jj bookmark of the work on the issue. Set this when work starts.
workspaces: [fable]         # jj workspaces where local work on the issue has happened, for example [fix-login-bug].
metadata: {}           # Optional. Arbitrary key-value notes, for example an AI agent session id to resume work with context: {session-id: "abc123"}.
deferred-from:         # Optional. The issue (as a quoted wikilink) or bookmark that deferred this work.
parent:                # Optional. The parent issue (as a quoted wikilink), if this issue is a sub-issue.
depends-on: []           # Optional. Issues (as quoted wikilinks) that must close before this one can start, for example `["[[faster-startup]]"]`.
remote:                # Optional. A URL: the GitHub issue or Jira ticket that tracks this issue outside the repo.
---

# Make Homepage a simple list of links

## Summary

Make Homepage a page where new people on the tailnet quickly find services.

## Context

Most of the page showed errors. The logs showed a stale Tailscale key (401), placeholder Portainer and Grafana URLs, a wrong Kavita port, and hardcoded tailnet addresses. Wallos is stopped.

## Acceptance criteria

- [x] Each service is a link, with no API key.
- [x] Quick search finds a service by its name or description.
- [x] A local build renders as designed on desktop and phone.
- [ ] After the deploy, each link opens on the tailnet.

## Out of scope

- Status marks. Homepage may need new tailnet policy to reach each application, and a false red mark is worse than none.
- Portainer. It is a TrueNAS app, and the repo does not show its address.

## Notes

2026-11-02: From the human: "The goal is for people new to the tailnet to be able to find services quickly." The human named Kometa. It has no web UI and it was a Plex tool, so the page has Kavita. Confirm this with the human.

2026-11-02: A new Homepage container serves the default settings until `/api/revalidate` is called. The healthcheck now calls it each 30 seconds.

## Resolution

<Complete this section when you close the issue.
- Completed: tell what was done. Link to the changelog version and the decision records, for example `[[0.0.5]]`.
- Abandoned: tell why the work stopped. Link to the issue or decision that replaces it, if one exists.>
