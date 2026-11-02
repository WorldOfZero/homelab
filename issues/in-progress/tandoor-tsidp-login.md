---
title: "Configure Tandoor with tsidp login and Ollama"
state: in-progress     # open | in-progress | closed. Must match the directory of the file.
resolution:            # completed | abandoned. Set this only when state is closed.
priority: medium       # critical | high | medium | low
effort: small          # small | medium | large | x-large
tags: [feature, tandoor, tailscale] # Built-in: bug, feature. Add the components the work touches too, for example [bug, scheduler].
created: 2026-11-02
closed:                # YYYY-MM-DD. Set this only when state is closed.
owner: claude          # The person or agent working on the issue. Cleared when the issue returns to open.
approver:              # The person or agent who accepts the issue when it closes.
bookmark: tandoor-tsidp # The jj bookmark of the work on the issue. Set this when work starts.
workspaces: [fable]    # jj workspaces where local work on the issue has happened, for example [fix-login-bug].
metadata: {}           # Optional. Arbitrary key-value notes, for example an AI agent session id to resume work with context: {session-id: "abc123"}.
deferred-from:         # Optional. The issue (as a quoted wikilink) or bookmark that deferred this work.
parent: "[[enable-tsidp-more-services]]" # Optional. The parent issue (as a quoted wikilink), if this issue is a sub-issue.
depends-on: []           # Optional. Issues (as quoted wikilinks) that must close before this one can start, for example `["[[faster-startup]]"]`.
remote:                # Optional. A URL: the GitHub issue or Jira ticket that tracks this issue outside the repo.
---

# Configure Tandoor with tsidp login and Ollama

## Summary

Complete the first configuration of Tandoor, and use tsidp for login. Tandoor is not configured now, and it has no users.

## Context

Tandoor redirects to `/setup/` when it has no users. All clients that can reach Tandoor can use this page to create the first administrator. Thus do this work soon, or stop the stack until it starts.

The compose file sets `SOCIAL_PROVIDERS` for OpenID Connect, but no provider configuration. Tandoor reads this configuration from `SOCIALACCOUNT_PROVIDERS`, or from a file in `SOCIALACCOUNT_PROVIDERS_FILE`. The value contains the client secret. See the Tandoor authentication documentation for the current format.

Use these values:

| Setting | Value |
|---|---|
| Discovery URL | `https://idp.comet-stork.ts.net/.well-known/openid-configuration` |
| Redirect URI | `https://tandoor.comet-stork.ts.net/accounts/oidc/tsidp/login/callback/` |
| PKCE | On |

The sidecar already has `TS_ACCEPT_DNS=true`, so Tandoor can find tsidp by its tailnet name.

### Recipe parsing with Ollama

Tandoor can import recipes from images, PDFs and text through an AI provider. Use the shared Ollama service for this. Tandoor sends AI calls through LiteLLM, and a user configures the provider in the Tandoor web interface. A superuser can configure a global provider for all spaces.

- Use the tailnet name `https://ollama.comet-stork.ts.net`, not an IP address. A Tailscale address can change.
- The compose file now sets `AI_ALLOWED_URLS=https://ollama.comet-stork.ts.net`. Tandoor 2.6.13 compares the URL of the provider with this list by exact match, so the URL in the provider form must be the same, with no trailing slash.
- The Tandoor documentation has no Ollama example. Use the LiteLLM documentation for the provider type and the model name.
- Ollama has no API key, but the provider form needs a value. Enter any text that is not empty.
- Select a model that can read images for image imports. Pull the model in Ollama first.
- Tandoor limits the AI credits of each space. Turn off cost tracking on the provider, or set a high limit, because Ollama has no cost.
- The tailnet policy must allow access from the `tandoor` node to the `ollama` node.

## Acceptance criteria

- [x] The first administrator exists.
- [ ] A client for Tandoor exists in tsidp, and its secret is only in Portainer.
- [ ] A tailnet user can log in through tsidp.
- [ ] `ENABLE_SIGNUP` and `SOCIAL_DEFAULT_ACCESS` have values that the human selected, and Notes records them.
- [ ] The tsidp dashboard shows a Tandoor login, and the Tandoor backups contain the new data.
- [ ] A recipe from text and a recipe from an image import through Ollama.
- [ ] `ENVIRONMENT.md` lists each new variable.

## Out of scope

- Tandoor import of recipes from other systems.

## Notes

2026-11-02: From the human: Tandoor is not configured yet, and it will be a tsidp application.

2026-11-02: From the human: Tandoor must use the shared Ollama service for recipe parsing.

2026-11-02: From the human: Tandoor is configured. The probe now redirects to the login page, not to `/setup/`. The compose file now sets the provider variable and `AI_ALLOWED_URLS`, and this needs a redeploy.

## Resolution
