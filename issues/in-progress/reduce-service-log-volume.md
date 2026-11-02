---
title: "Reduce the log volume of Loki and Karakeep"
state: in-progress     # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: medium       # critical | high | medium | low
effort: small          # small | medium | large | x-large
tags: [bug, grafana, karakeep] # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
created: 2026-11-02
closed:                # YYYY-MM-DD. Set this only when state is closed.
owner: claude          # The person or agent working on the issue. Cleared when the issue returns to open.
approver:              # The person or agent who accepts the issue when it closes.
bookmark: reduce-log-volume # The jj bookmark of the work on the issue. Set this when work starts.
workspaces: [fable]    # jj workspaces where local work on the issue has happened, for example [fix-login-bug].
metadata: {}           # Optional. Arbitrary key-value notes, for example an AI agent session id to resume work with context: {session-id: "abc123"}.
deferred-from:         # Optional. The issue (as a quoted wikilink) or bookmark that deferred this work.
parent:                # Optional. The parent issue (as a quoted wikilink), if this issue is a sub-issue.
depends-on: []           # Optional. Issues (as quoted wikilinks) that must close before this one can start, for example `["[[faster-startup]]"]`.
remote:                # Optional. A URL: the GitHub issue or Jira ticket that tracks this issue outside the repo.
---

# Reduce the log volume of Loki and Karakeep

## Summary

Stop two sources of log noise. Loki logs each query, and Karakeep writes trace spans to its log.

## Context

On 2026-11-02, Loki received about 1.4 GB of logs in 24 hours. The Loki container wrote about 1.2 GB (87%), and about 940 MB of this came from the `metrics.go` query lines. Karakeep wrote about 3.3 million lines, which is more than half of all lines, but only 104 MB. The cause in Karakeep is `OTEL_TRACING_ENABLED: true`. No OTLP collector receives these spans, so they go to the log. No dashboard or alert uses the Loki container logs or the Karakeep spans.

[[monitor-apps-and-tsidp]] records about 313,000 Karakeep lines in 7 days. The 24 hour count above shows that this value is too low.

## Acceptance criteria

- [x] Loki uses `log_level: warn`.
- [x] Karakeep does not set `OTEL_TRACING_ENABLED`.
- [ ] After the deploy, the Loki container writes less than 100 MB of logs in 24 hours.
- [ ] After the deploy, the Karakeep container writes less than 100,000 lines in 24 hours.
- [ ] The Karakeep dashboard still shows its metrics.

## Out of scope

- Other log sources.
- Log retention. See [[raise-container-log-retention]].

## Notes

2026-11-02: From the human: disable the tracing in Karakeep, and raise the log level of Loki.

## Resolution
