---
name: memory-unified-bridge
description: Unified personal memory bridge. Use when recalling prior context or when the user asks to remember, record, save, update, or forget information across agents.
---

# Unified personal memory

The canonical personal-memory directory is:

`C:\Users\majq1\.agent-memory`

## Read

- Prefer the installed `memory-*` skills for semantic recall.
- If a relevant item is not already materialised, search Markdown files in the canonical directory.
- Treat the canonical directory as the source of truth; generated `memory-*` skills are read replicas.

## Write

- When the user explicitly asks to remember/save/update information, create or update a Markdown file directly in the canonical directory.
- Use a descriptive `kebab-case.md` filename and YAML frontmatter containing `name`, `description`, and `metadata.type`.
- Never edit generated `memory-*` skill replicas. Never write secrets unless the user explicitly asks to store them.
- If direct access is sandboxed, write to this agent's native memory folder; Skills Manager imports it on the next Memory Sync.

## Delete

- Delete only the canonical file explicitly selected by the user. Skills Manager removes stale replicas during the next sync.
