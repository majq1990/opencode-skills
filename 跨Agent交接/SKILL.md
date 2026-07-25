# cross-agent-handoff

Use this skill when the user wants Claude and Codex to continue each other's work, search past cross-agent sessions, or take over a previous thread from the other agent.

## What this skill does

1. Rebuild the unified session index from both agents.
2. Search the handoff index by topic, path, or session id.
3. Open the generated session summary and continue from that state.
4. When useful, combine the summary with shared `mem0` search results.

## Commands

Run from `D:\opencode\agent-sync`:

```powershell
npm run handoff:index
npm run handoff:search -- "keyword"
npm run handoff:show -- "session-id"
```

## Sources

- Claude sessions: `C:\Users\majq1\.claude\projects\**\*.jsonl`
- Codex sessions: `C:\Users\majq1\.Codex\sessions\**\*.jsonl`
- Codex archives: `C:\Users\majq1\.Codex\archived_sessions\*.jsonl`
- Shared summaries: `D:\opencode\agent-sync\handoff\summaries\*.md`

## Working style

- Prefer `handoff:search` first, because one topic may map to many sessions.
- Use `handoff:show` on the best match before making changes.
- The search command skips imported duplicate sessions by default; add `--include-imported` only when you need to inspect the Codex-side import copy.
- If the task depends on long-term memory rather than a single session, query `mem0` after opening the handoff summary.
