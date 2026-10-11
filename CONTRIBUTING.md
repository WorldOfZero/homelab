# Contributing to sisyphus

This guide is for humans and AI agents. AI agents must also follow [[AGENTS]] (`AGENTS.md`), which adds rules that apply only to agents.

This file, [[AGENTS]], the changelog, and `VERSION` came from a separate project-scaffolding template, not from `sisyphus init`: `sisyphus init` only sets up `issues/` (see [[#Issues]]). Change this guide to fit this repo, and record each change as a decision (see [[#Decisions]]).

## The design log

The design log is the record of why the repo is the way it is. It has four parts:

- **Decision records** in `design/decisions/<component>/`. Each one records one decision, its context, and the alternatives (see [[#Decisions]]).
- **Issues** in `issues/`. The `Notes` section of an issue records progress and the input of humans, with the date (see [[#Issues]]).
- **The changelog** in `changelog/` and `CHANGELOG.md`. Each version records what changed and links to its decisions and issues (see [[#Changelog]]).
- **Design documents** in `design/`. They describe the current design, and link to the decisions.

### How to do design work

1. Create an issue for the design question, and start it.
2. When the answer is not clear, write two or more drafts that each optimize for one goal, for example simplicity, correctness, or cost. Compare them in one document, with a table and a recommendation. Keep the drafts for comparison, and do later work in one working draft.
3. Keep all open questions in one list, with an id for each question, the place where it was asked, and a proposed answer. A human closes a question by a reply such as "B1 yes".
4. Record the input of a human in the `Notes` of the issue: the date, "from the human", the input, and what it means for the design.
5. Record each answer as a decision record in the same change that puts it into effect.
6. Move questions that do not block the issue to new issues, with `deferred-from` set to the issue.

## Decisions

Every design or implementation decision is recorded as its own file under the component it affects:

```
design/decisions/<component>/<NNNN>-<short-title>.md
```

- `<component>` is the name of the part of the repo that the decision is about. Use `repo` for tools and processes that apply to the whole repo. If the decision is about a new component, create its directory.
- `<NNNN>` is the next free four-digit number in that component's directory, starting at `0001`.
- Record the decision in the same change that puts it into effect.
- Do not rewrite a past decision. To change one, add a new decision that supersedes it, and set the old one's status to `Superseded by [[<NNNN>-<short-title>]]`.

Use this structure:

```markdown
# <NNNN>: <Title>

- Status: Accepted | Proposed | Superseded by [[<NNNN>-<short-title>]]
- Date: YYYY-MM-DD
- Version: <the changelog version that introduced it>

## Context
What problem or question forced a decision, and what constraints apply.

## Decision
What was decided, stated plainly.

## Alternatives considered
Other options and why each was rejected.

## Consequences
What this makes easier or harder, and any follow-up work it creates.
```

## Versioning

The repo uses [Pride Versioning](https://pridever.org/), with versions in the form `PROUD.DEFAULT.SHAME`:

- **PROUD**: bumped for a release the maintainers are proud of.
- **DEFAULT**: bumped for an ordinary release.
- **SHAME**: bumped for fixes, or for releases too small or too embarrassing to count as anything more.

Bumping one part resets the parts to its right to `0`. A normal change bumps SHAME: if the latest version is `0.3.4`, the change is `0.3.5`. The maintainers decide when to bump PROUD or DEFAULT.

The `VERSION` file pins the latest version. It holds a single line, for example `0.0.1`, with nothing else. Each version bump updates `VERSION` in the same change that adds the new changelog entry.

## Changelog

Each change that adds or changes a feature, component, design, or decision gets a new version, recorded in two places:

1. **`changelog/<version>.md`**: a new file, for example `changelog/0.0.5.md`. It holds the verbose record, with more detail than a change description can hold:

   ```markdown
   # <version>

   - Date: YYYY-MM-DD
   - Bookmark: <the jj bookmark of the work>
   - Components: <affected components>

   ## Summary
   One or two sentences on what changed.

   ## Changes
   What was added, changed, or removed, and where.

   ## Decisions
   Wikilinks to the decision records made in this version.

   ## Issues
   Wikilinks to the issues that this version created, started, closed,
   or abandoned.

   ## Notes
   Open questions, follow-up work, and anything a reviewer should know.
   ```

2. **`CHANGELOG.md`**: a short entry for the version, newest at the top, linking to its file:

   ```markdown
   ## [[0.0.5]] - YYYY-MM-DD
   - One-line summary of each notable change.
   ```

Never edit an existing `changelog/<version>.md` to describe new work. Add a new version instead.

**Concurrent work:** two lines of work can pick the same next version at the same time. When you rebase onto `main`, check whether `main` already has your version. If it does, renumber your changelog file, your `CHANGELOG.md` entry, `VERSION`, and any `Version:` lines in your decision records to the next free SHAME version.

A change that only creates an issue or moves an issue to `in-progress` does not need a new version. A cleanup that does not change behavior does not need one either.

## Links between documents

The repo is also an [Obsidian](https://obsidian.md/) vault. In every Markdown file, refer to other Markdown files in the repo with **wikilinks**, not with Markdown links or plain paths.

- Link to a document by its file name without `.md`: `[[CONTRIBUTING]]`, `[[0.0.5]]`.
- Obsidian finds the file by name in any directory. So a link to an issue still works after the issue moves between `open/`, `in-progress/`, and `closed/`.
- If two files have the same name, include the path from the repo root: `[[design/example/README]]`.
- Link to a section with `#`, for example `[[CONTRIBUTING#Issues]]`. Link to a section of the same file with `[[#Heading]]`.
- Show different text with `|`: `[[0.0.5|the first release]]`.
- In YAML frontmatter, put a wikilink in quotes: `parent: "[[large-issue]]"`.
- Do not write `#<name>` in a Markdown file to refer to an issue. Obsidian reads `#word` as a tag.
- Use normal Markdown links only for files that are not Markdown and for external URLs.

Before you finish a change, run `sisyphus links` on each Markdown file that you edited. Fix each link with the status `missing`, `ambiguous`, or `missing-heading`.

## Issues

All issue tracking happens in the `issues/` directory of this repo. An issue describes future work, or work that someone deferred. Each issue is one Markdown file with YAML frontmatter.

```
issues/
  TEMPLATE.md       The structure of an issue
  open/             Work that nobody has started
  in-progress/      Work that someone has started
  closed/           Work that is complete or abandoned
```

### Issue names

- The file name without `.md` is the **issue name**, for example `issues/open/faster-startup.md` has the name `faster-startup`.
- Use 2–6 words in kebab-case. The name must be unique across all Markdown files in the repo. Do not use the name `cleanup`.
- Do not rename an issue. The name is the permanent id of the issue.
- Refer to an issue by its name, not by its path: `[[<issue-name>]]` in Markdown files, and `#<issue-name>` in change descriptions and code comments.

### Frontmatter

`issues/TEMPLATE.md` defines the fields:

| Field | Values | Notes |
|---|---|---|
| `title` | Short imperative text | |
| `state` | `open`, `in-progress`, `closed` | Must always match the directory that holds the file. |
| `resolution` | `completed`, `abandoned` | Empty until the issue is closed. Defaults to `completed` when closing. |
| `priority` | `critical`, `high`, `medium`, `low` | `critical`: blocks other work. `high`: do next. `medium`: the default. `low`: do when there is time. |
| `effort` | `small`, `medium`, `large`, `x-large` | `x-large`: split it into sub-issues before you start. |
| `tags` | List of tags | Free-form. Built-in: `bug` and `feature`. Add the components the work touches too, for example `[bug, scheduler]`. |
| `created`, `closed` | `YYYY-MM-DD` | |
| `owner` | A person or an agent | Who is working on the issue. Cleared when work stops (state returns to `open`). |
| `approver` | A person or an agent | Who accepts the issue when it closes. Not cleared when work stops. |
| `bookmark` | A jj bookmark | The bookmark of the work on the issue. Set it when work starts. Cleared when work stops. |
| `workspaces` | List of jj workspace names | Every jj workspace that has done local work on the issue. Entries accumulate; never cleared. |
| `metadata` | `{key: value, ...}` | Optional. Arbitrary notes, for example `{session-id: "abc123"}` so an agent can resume work with context. Never cleared automatically. |
| `deferred-from` | `"[[<issue-name>]]"` or a bookmark | Optional. The work that deferred this issue. |
| `parent` | `"[[<issue-name>]]"` | Optional. The issue that this sub-issue is part of. |
| `depends-on` | List of `"[[<issue-name>]]"` | Optional. Issues that must close before this one can start. |
| `remote` | A URL | Optional. The GitHub issue or Jira ticket that tracks this issue outside the repo. |

### The sisyphus command

Use `sisyphus` to create issues and to change their state. It keeps the `state` field and the directory the same, sets the dates, and applies the rules below. Run it from any directory in the repo or in a jj workspace.

```bash
sisyphus new <issue-name> --title "<title>" --priority high --effort small --tags "<component>"
sisyphus update <issue-name> in-progress --bookmark <bookmark> --owner <owner> --workspace <workspace>
sisyphus update <issue-name> in-progress --metadata "session-id=<id>"   # optional, if you have one
sisyphus update <issue-name> closed                           # resolution defaults to completed
sisyphus update <issue-name> closed --resolution abandoned
sisyphus update <issue-name> open                            # stop work without closing
sisyphus update <issue-name> in-progress --priority high --effort small --tags "<component>"  # reprioritize
sisyphus new <sub-issue-name> --parent <issue-name>
sisyphus parent <issue-name> <parent-issue-name>
name="$(sisyphus slug "<arbitrary text, for example a GitHub issue title>")"
sisyphus new "$name" --remote <url> --context "<background text>"
sisyphus remote <issue-name> <url>                   # pin it to a GitHub issue or Jira ticket
sisyphus depends-on <issue-name> <blocking-issue-name>   # cannot start until that issue closes
sisyphus list --blocked                               # issues with an open dependency
sisyphus graph <issue-name> [--full]                  # it, all below it, and the path above it
sisyphus list --state open,in-progress --priority critical,high
sisyphus search "timeout" --section summary          # search (and return) just the Summary
sisyphus resolve "[[CONTRIBUTING#Issues]]"
sisyphus links "[[<issue-name>]]"
```

Install it with `go install github.com/runewake2/sisyphus/cmd/sisyphus@latest`. Run `sisyphus <command> --help` for all options. `cmd/sisyphus-mcp` gives an agent every command above as an MCP tool over stdio; see the README's "MCP server" section.

sisyphus itself must not know about any particular repo or issue, including this one. Its code, its embedded `issues/TEMPLATE.md`, its help text, and its tests use only generic examples (for example `fix-login-bug`, `alice`, `ai/work`), and its tests run against the embedded template, never against this repo's own files. In the same way, sisyphus never talks to GitHub, Jira, GitLab, or any other tracker itself: each integration is a configured plugin that sisyphus runs as a separate child process, and the plugin translates between a sisyphus issue and the platform's (see [[integration-plugins]]).

### Issue lifecycle

1. **Create** an issue in `issues/open/` when you find work that you will not do now. Create it in the same change that defers the work. Do not leave untracked `TODO` comments: write `TODO(#<issue-name>)`.
2. **Start** the issue in the first change of the work: move it to `issues/in-progress/`, and set `bookmark`, `owner`, and `workspace`. Add `metadata` (for example a session id) if it would help resume the work later. Make sure first that nobody else has started it.
3. **Work**: add the trailer `Updates #<issue-name>` to each change, and record progress in `Notes`.
4. **Close** the issue in the change that completes the work: move it to `issues/closed/` with `resolution: completed`, complete `Resolution`, and add the trailer `Fixes #<issue-name>`.
5. **Abandon** an issue by moving it to `issues/closed/` with `resolution: abandoned`, and tell why in `Resolution`.
6. **Stop** work without closing by moving the issue back to `issues/open/`, and record what remains in `Notes`.

Do not reopen a closed issue. Create a new issue that links to it. Split a large issue into sub-issues with `parent`, and close the parent when all of its sub-issues are closed.

### External trackers

Once a repo is initialized, **sisyphus is always the source of truth for issues.** A GitHub, Jira,
or GitLab issue is a mirror and an intake point, never an independent record: content flows from
`issues/` to the tracker, and back only through an explicit pull.

- **Plugins**: sisyphus talks to a tracker only through a plugin that the repo configures. sisyphus
  runs each plugin as a separate child process and speaks its own plugin protocol to it; the
  plugin translates between a sisyphus issue and the tracker's. A plugin can come from anywhere;
  some, starting with GitHub, are written in this repo. See [[integration-plugins]].
- **Pinning**: `remote` (see [[#Frontmatter]]) holds the URL of the tracker issue a sisyphus issue
  corresponds to. Set it with `sisyphus new --remote` or `sisyphus remote`. The URL selects the
  plugin that handles the issue.
- **Automation**: this repo has no tracker workflows for now. Intake of new GitHub issues and
  mirroring to GitHub come back on top of the GitHub plugin ([[github-intake-workflow]],
  [[github-sync-workflow]]).

## Writing style

Write in Simplified Technical English (STE, based on ASD-STE100) for change descriptions, changelog entries, decision records, issues, and comments.

- **Keep sentences short.** Use 20 words or fewer for an instruction and 25 words or fewer for a description.
- **Write one idea per sentence.** Use six sentences or fewer in a paragraph.
- **Use the active voice and simple tenses.** Do not use `-ing` verb forms.
- **Write instructions as commands.** Write "Run the tests", not "You should run the tests".
- **Use simple, common words, and no phrasal verbs.** Write "use", not "utilize". Write "configure", not "set up".
- **Use one word for one meaning.** Do not change between synonyms for the same thing.
- **Do not leave out words to make text shorter.** Keep articles and verbs.
- **Be specific, and do not use idioms, slang, or jokes.**

For code comments, write a comment only when the reason for the code is not clear from the code. Keep it to one short line.

## Version control

The repo uses [Jujutsu (jj)](https://jj-vcs.github.io/jj/) colocated with git. **Use `jj` commands, not raw `git` commands** that change the repo. Read-only git commands are fine.

Base your work on `main`. If `main` moves ahead while you work, rebase your work onto it, and resolve any conflicts before you continue:

```bash
jj rebase -b <bookmark> -d main
```

Do not run jj in a checkout that another jj process uses at the same time, for example an editor of a human. Work in your own workspace (see [[AGENTS]]).

### Change descriptions

A jj change description becomes the git commit message. Descriptions follow the [Tailscale commit message style](https://github.com/tailscale/tailscale/blob/main/docs/commit-messages.md), and use Simplified Technical English.

```
design/decisions: record explicit step dependencies

Steps now declare the steps that they depend on in a needs list.
The scheduler uses this list to find the steps that are ready to run.

Fixes #explicit-step-dependencies
```

- **Subject:** the primary directory that the change affects, a colon, a space, and a lowercase imperative verb. No trailing period. Ideally under 76 characters.
- **Body:** a blank line after the subject. Explain what changed and why. Wrap lines at about 76 characters. Use plain text.
- **Trailers:** `Fixes #<issue-name>` for the change that closes an issue, `Updates #<issue-name>` for other changes on an issue, and `Updates #cleanup` for a cleanup that does not change behavior.
- Every change must leave the tree in a clean, working state. Squash fixup changes into the change that they fix.

### When work is complete

Work is complete only once its changes are part of `main`'s history:

```bash
jj log -r 'main..<bookmark>'
```

If this prints nothing, the work is complete.

## Checklist for every change

- [ ] Using `jj`, not mutating `git` commands
- [ ] The work is based on `main`
- [ ] Every change has a description in the Tailscale style
- [ ] Descriptions, changelog entries, decision records, issues, and comments use Simplified Technical English
- [ ] New decisions recorded in `design/decisions/<component>/`
- [ ] The issue moved to `issues/in-progress/` in the first change, and to `issues/closed/` in the change that completes the work
- [ ] Deferred work recorded as new issues
- [ ] Markdown files link with `[[wikilinks]]`, and `sisyphus links` reports only `ok` links
- [ ] The tests of the repo pass
- [ ] SHAME version bumped, with a new `changelog/<version>.md`, a `CHANGELOG.md` entry, and `VERSION` updated
