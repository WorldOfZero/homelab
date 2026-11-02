---
title: "Deploy helper containers with Portainer Git updates"
state: in-progress     # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: high         # critical | high | medium | low
effort: small          # small | medium | large | x-large
tags: [feature, portainer] # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
created: 2026-11-02
closed:                # YYYY-MM-DD. Set this only when state is closed.
owner: claude          # The person or agent working on the issue. Cleared when the issue returns to open.
approver:              # The person or agent who accepts the issue when it closes.
bookmark: gitops-helper-configs # The jj bookmark of the work on the issue. Set this when work starts.
workspaces: [fable]         # jj workspaces where local work on the issue has happened, for example [fix-login-bug].
metadata: {}           # Optional. Arbitrary key-value notes, for example an AI agent session id to resume work with context: {session-id: "abc123"}.
deferred-from:         # Optional. The issue (as a quoted wikilink) or bookmark that deferred this work.
parent:                # Optional. The parent issue (as a quoted wikilink), if this issue is a sub-issue.
depends-on: []           # Optional. Issues (as quoted wikilinks) that must close before this one can start, for example `["[[faster-startup]]"]`.
remote:                # Optional. A URL: the GitHub issue or Jira ticket that tracks this issue outside the repo.
---

# Deploy helper containers with Portainer Git updates

## Summary

Make a push to `main` update helper containers through Portainer, with no redeploy in the Portainer UI.

## Context

Most helpers run a script or config from an inline `configs` block. A Portainer Git update uses `docker compose up` without a forced recreate, and Compose does not recreate a container when only the config content changes. A test on Portainer CE 2.45.1 showed this: the stack moved to the new commit, but the container kept the old config. The manual **Pull and redeploy** recreates all containers, which is why it worked.

## Acceptance criteria

- [x] A change to the inline config of a helper changes only the hash of that service.
- [x] The README tells how to turn on polling.
- [ ] The human turns on polling for the stacks.
- [ ] A pushed config change reaches a helper on minerva with no redeploy in the UI.

## Out of scope

- The `ts-serve` configs. A label there restarts each application once, and these configs seldom change.
- Limit updates to the stacks with changed paths. Portainer has no such setting.

## Notes

2026-11-02: From the human: "They need to detect and deploy their updates via portainer git ops if possible."

2026-11-02: The test used a Git repo on a local server. Polling on a 1 minute interval found each commit in about 80 seconds. In 2.45.1 the poll interval is on the Git source, and a stack with only `AutoUpdate.Interval` from the API did not poll.

## Resolution

<Complete this section when you close the issue.
- Completed: tell what was done. Link to the changelog version and the decision records, for example `[[0.0.5]]`.
- Abandoned: tell why the work stopped. Link to the issue or decision that replaces it, if one exists.>
