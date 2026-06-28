# Maintainer scripts (local only)

These shell helpers are **not** in the public GitHub repository.

**Off-repo backup (recommended):** `~/Documents/jem-maintainer-scripts/` (full path: `/Users/user/Documents/jem-maintainer-scripts/`)  
Copy from there into `jem/scripts/` on any machine:

```bash
cp /Users/user/Documents/jem-maintainer-scripts/build_friedso_deploy_bundle.sh jem/scripts/
cp /Users/user/Documents/jem-maintainer-scripts/publish_github.sh jem/scripts/
chmod +x jem/scripts/build_friedso_deploy_bundle.sh jem/scripts/publish_github.sh
```

| Script | Purpose |
|--------|---------|
| `build_friedso_deploy_bundle.sh` | Validate, build `graph.json`, write `_deploy_bundle/jem-web-*` |
| `publish_github.sh` | Validate, stage, commit, optional push to `dso6060/jem` |

They are listed in `.gitignore` under the repo clone. Refresh the backup folder when you change either script.

**Production bundle (local):**

```bash
./jem/scripts/build_friedso_deploy_bundle.sh
```

**Public GitHub:**

```bash
./jem/scripts/publish_github.sh -m "data(scope): …" --branch your/branch --push
```

Public repo workflow without these scripts: `deploy_prep.sh`, `safe_pipeline.sh`, and manual `git add` / `git commit` / `git push` per [`SESSION_WORKFLOW.md`](../docs/SESSION_WORKFLOW.md).
