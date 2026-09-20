# Dispatch prompt — Packet locator (Agent 0)

`prompt_id: dispatch-packet-locator` · `version: v1` · dispatched 2026-08-31T23:05Z
`run_ledger: none` (negative finding; no cells to ledger)

The first agent fired, before the packet existed in the workspace. Its job was
to establish whether the orchestrator packet was already in the repo, on a
branch, or in a zip on disk. A negative finding here is what stopped a
fabricated run from the screenshot.

Recorded as dispatched (explore agent, thoroughness: very thorough).

---

Search the repository at /workspace (a project called JEM - Judiciary Entity Map India) thoroughly for any files related to an "agent orchestrator" packet. Specifically look for:

1. A file named `00_PACKET_INDEX.md` or anything matching `*PACKET*`
2. A file named `classification.py`
3. Anything matching `*orchestrator*` (case-insensitive) in filename or content
4. Directories or files mentioning "Cursor tracks", "consensus harness", "prompt registry", "public inspection prompt"
5. Anything referencing names like "Prajna", "Agriya", "DAKSH", "SAT anchor", "diversity-weighted consensus"
6. Any `.claude/prompts/` directory contents and `.claude/decisions/` directory contents
7. Any recently added markdown files that look like multi-step instruction packets (e.g. files with numeric prefixes like `00_`, `01_`, `S_`, `C_`, `K_`, `N_`)
8. Any zip files anywhere in the repo or filesystem

Also list the top-level structure of /workspace/jem and /workspace/jem/scripts so I know what exists.

Report exactly what you find with full paths. If files do not exist, say so clearly.
