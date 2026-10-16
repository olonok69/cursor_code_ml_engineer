---
name: atlassian
description: >-
  Read Jira issues, links, comments and the issue XML, and read Confluence pages (search, body, diff a local
  file against a page), via the Atlassian REST token. Read-only. Use when a ticket's live status, links or
  comments are needed, to export a ticket's XML into its data/changes/<ticket>/ folder, or to compare a local
  doc with its Confluence page.
---

# atlassian: read-only Jira + Confluence

## When to use
- The user names a ticket (`PROJ-123`) and you need its live status, assignee, links or recent comments.
- A new ticket folder needs its XML: `data/changes/<ticket-lowercase>/<TICKET>.xml`.
- Before editing a doc that also lives on Confluence: diff it first.

## Tool
`data/changes/tools/atlassian/atl.py` in the project repo (course copy: `ejemplos/metodologia/tools/atlassian/`).
Python 3.10+, **standard library only** (no pip install). Run from the repo root. Use `python3` on macOS,
Linux or WSL; `py` or `python` on Windows.

```bash
python3 data/changes/tools/atlassian/atl.py jira issue PROJ-123          # type, status, summary, assignee, links
python3 data/changes/tools/atlassian/atl.py jira search 'project = PROJ AND assignee = currentUser() AND statusCategory != Done'
python3 data/changes/tools/atlassian/atl.py jira links PROJ-123
python3 data/changes/tools/atlassian/atl.py jira comments PROJ-123 --last 3
python3 data/changes/tools/atlassian/atl.py jira xml PROJ-123 --out data/changes/proj-123/
python3 data/changes/tools/atlassian/atl.py confluence search 'title ~ "authoring" AND type = page'
python3 data/changes/tools/atlassian/atl.py confluence page <PAGE_ID> --body
python3 data/changes/tools/atlassian/atl.py confluence diff <local .md/.html> <PAGE_ID>
```

**Exit codes:**

| Code | Meaning |
|---|---|
| 0 | ok |
| 2 | credentials missing or invalid (see Setup) |
| 3 | HTTP error |
| 4 | not found |

`--json` returns raw JSON. Use it only inside a script; in chat, the compact default saves context.

## Setup (once per machine, by the person)
Create `~/.config/<org>/jira.env` (Windows: `%USERPROFILE%\.config\<org>\jira.env`; `ATLASSIAN_ENV_FILE`
overrides the path) with three lines:

```
JIRA_BASE_URL=https://<your-site>.atlassian.net
JIRA_EMAIL=<your Atlassian login email>
JIRA_API_TOKEN=<token from id.atlassian.com → Security → API tokens>
```

Restrict it to your user (`chmod 600` on macOS/Linux). Write it in your own terminal — never paste the token
into a chat or a file under `data/`. The same token reads Confluence. Check it with
`… atl.py jira issue PROJ-123`: exit 0 means it works, exit 2 means the file is missing or wrong.

## Hard rules
1. **Read-only.** `atl.py` sends GET only (one network function; a test asserts it).
   - Creating, editing, transitioning or commenting on Jira issues is the **user's** job. Draft the text, and the user
     posts it.
   - Updating an existing Confluence page uses `confluence_write.py`: `pull` → `plan` (backup + visible-text diff +
     confirmation token) → the user reads the diff and confirms **that page** → `apply --confirm <token>`. Run it only
     when the user explicitly asks for that page to be updated. Apply refuses if the token, the body file or the live
     page version changed since the plan, and reads the page back.
2. **Never print, paste or log the token**, nor the contents of `jira.env`.
3. **Cite tickets by key.** Outward text cites case tags and ticket keys, never local file paths.
