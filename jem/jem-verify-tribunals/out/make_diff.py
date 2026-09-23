"""Create a review diff without modifying Git state or including source binaries."""
import difflib
from pathlib import Path

root = Path(__file__).resolve().parent
repository_path = "jem/jem-verify-tribunals/"
suffixes = {".md", ".json", ".py", ".swift", ".csv"}
parts = []
for path in sorted(root.iterdir()):
    if path.is_file() and path.suffix in suffixes:
        text = path.read_text().splitlines(keepends=True)
        parts.extend(difflib.unified_diff([], text, fromfile="/dev/null", tofile="b/" + repository_path + "out/" + path.name))
for path in [root.parent / "README.md", root / ".gitignore"]:
    if path.exists():
        text = path.read_text().splitlines(keepends=True)
        name = "out/.gitignore" if path.parent == root else path.name
        parts.extend(difflib.unified_diff([], text, fromfile="/dev/null", tofile="b/" + repository_path + name))
(root / "changes.diff").write_text("".join(parts))
print("Wrote " + repository_path + "out/changes.diff for text handoff artifacts")
