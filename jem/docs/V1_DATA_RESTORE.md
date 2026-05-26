# v1.0 data restore — unblock the graph

Use this when repo-root `graph.json` shows **~13 entities** (or any count far below ~150+ for “backbone + TN+PY” / ~390+ after MH+DL+KA).

## 1. Do not clobber the symlink target

- `jem/web/public/graph.json` → `../../../graph.json` (repo root).
- **Default** `python scripts/build.py` **without** `--output` writes that file.
- Until the full YAML corpus is back, use:

```bash
cd jem
./scripts/build_safe.sh
# or:
python scripts/build.py --output "$(pwd)/build/graph.staging.json"
```

Compare staging file `meta.entity_count` before replacing anything.

## 2. Restore sources (pick one path that applies)

1. **Another machine / Time Machine / zip export** — copy in:
   - Full `graph.json`
   - Entire `jem/data/entities/` tree
   - Entire `jem/data/relationships/` tree  
2. **Git remote** — if an older commit or branch still has the large tree:  
   `git log --oneline -- graph.json` then `git show <commit>:graph.json` (only if history contains the blob).  
3. **Live site** — if a known-good build is deployed on your host: download **`graph.json`** from `public/graph.json` on that URL **only if** you trust that build and licence. Canonical demo: https://friedso.com/apps/jem/

## 3. Verify after copy

```bash
cd jem
python3 scripts/validate.py --strict
python3 scripts/derive.py
# Optional full rebuild once YAML is complete:
# python3 scripts/build.py
```

**Duplicate `id`:** `validate.py` does not check global uniqueness across files. After restore, run:

```bash
rg '^id:' jem/data/entities --no-filename | sort | uniq -d
```

(empty output = no duplicate ids at entity root keys).

## 4. Relationship placeholders

`build.py` can invent `_placeholder` entities for missing relationship endpoints. After restore, search `graph.json` for `"_placeholder": true` — ideally **zero** for v1.0.0.

## 5. Only then — resume MASTER_CHECKLIST Part 3

Author MH → DL → KA YAML + relationship files per checklist; re-run validate/derive/build when ready to **replace** repo-root `graph.json` intentionally.
