---
title: "Renew the GitHub token for image pulls by 2027-01-31"
state: open            # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: medium       # critical | high | medium | low
effort: small          # small | medium | large | x-large
tags: [portainer]      # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
created: 2026-11-02
closed:                # YYYY-MM-DD. Set this only when state is closed.
owner:                 # The person or agent working on the issue. Cleared when the issue returns to open.
approver:              # The person or agent who accepts the issue when it closes.
bookmark:              # The jj bookmark of the work on the issue. Set this when work starts.
workspaces: []         # jj workspaces where local work on the issue has happened, for example [fix-login-bug].
metadata: {}           # Optional. Arbitrary key-value notes, for example an AI agent session id to resume work with context: {session-id: "abc123"}.
deferred-from:         # Optional. The issue (as a quoted wikilink) or bookmark that deferred this work.
parent:                # Optional. The parent issue (as a quoted wikilink), if this issue is a sub-issue.
depends-on: []           # Optional. Issues (as quoted wikilinks) that must close before this one can start, for example `["[[faster-startup]]"]`.
remote:                # Optional. A URL: the GitHub issue or Jira ticket that tracks this issue outside the repo.
---

# Renew the GitHub token for image pulls by 2027-01-31

## Summary

Replace the GitHub token that minerva uses to pull images from `ghcr.io` before about 2027-01-31.

## Context

The token has a 90 day expiry. The last token expired, and all `ghcr.io` pulls failed since at least 2026-10-31. Portainer Git updates stopped for each stack with such an image, and nobody saw it until a GameScores release could not deploy. See `services/portainer/README.md` for the steps.

## Acceptance criteria

- [ ] A new token is in Portainer before the old one expires.
- [ ] The Portainer logs show no new `denied` lines after the next poll.
- [ ] The README and this issue have the next expiry date, or this issue closes because the login is no longer necessary.

## Out of scope

- Changes to the images.

## Notes

2026-11-02: From the human: "the gh token will expire again in 90 days. we should have a note for this." The date is 90 days after 2026-11-02. Check the real expiry date in GitHub.

2026-11-02: The login is necessary only for private images. All other images that failed are public. If the GameScores package becomes public, the login can go, and this issue can close.

## Resolution

<Complete this section when you close the issue.
- Completed: tell what was done. Link to the changelog version and the decision records, for example `[[0.0.5]]`.
- Abandoned: tell why the work stopped. Link to the issue or decision that replaces it, if one exists.>
