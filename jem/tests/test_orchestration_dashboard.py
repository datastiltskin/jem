"""Guardrails for the orchestration dashboard assets.

The GIF must be a real animated GIF (every frame paletted) or downloads look
empty. The GitHub Pages snapshot in docs/ must stay a rewrite of the ledger
dashboard, not a hand-edited fork.
"""

from pathlib import Path

import pytest

JEM = Path(__file__).resolve().parent.parent
REPO = JEM.parent
GIF = JEM / "ledger" / "diagrams" / "orchestration.gif"
DASH = JEM / "ledger" / "dashboard" / "index.html"
PAGES = REPO / "docs" / "index.html"

REQUIRED_LEGEND = (
    ">S</b> schema",
    ">C</b> commercial courts",
    ">K</b> criminal magistracy",
    ">N</b> classification",
    ">W1</b>",
    "Bharatiya Nagarik Suraksha Sanhita",
    "id=\"share\"",
    "id=\"pages\"",
)


def test_dashboard_explains_every_packet_letter():
    html = DASH.read_text(encoding="utf-8")
    for needle in REQUIRED_LEGEND:
        assert needle in html, f"dashboard missing legend fragment {needle!r}"


def test_pages_snapshot_is_rewritten_ledger_copy():
    assert PAGES.is_file(), "run: python3 scripts/harness/publish_dashboard.py"
    src = DASH.read_text(encoding="utf-8")
    pub = PAGES.read_text(encoding="utf-8")
    assert 'src="../diagrams/orchestration.gif"' in src
    assert 'src="diagrams/orchestration.gif"' in pub
    assert "../diagrams/" not in pub
    assert (REPO / "docs" / ".nojekyll").is_file()
    assert (REPO / "docs" / "diagrams" / "orchestration.gif").is_file()


def test_orchestration_gif_is_animated_and_not_empty():
    pytest.importorskip("PIL")
    from PIL import Image

    assert GIF.is_file()
    im = Image.open(GIF)
    assert im.format == "GIF"
    assert im.n_frames >= 6
    # Pillow may report later frames as RGB even when the file is a valid
    # paletted GIF; the regression we care about is a blank frame.
    for i in range(im.n_frames):
        im.seek(i)
        colors = im.convert("RGB").getcolors(maxcolors=1_000_000)
        n = 0 if colors is None else len(colors)
        assert colors is None or n >= 20, f"frame {i} looks empty ({n} colours)"
    im.seek(im.n_frames - 1)
    durations = []
    for i in range(im.n_frames):
        im.seek(i)
        durations.append(im.info.get("duration") or 0)
    assert max(durations) >= 3000, f"final-wave hold missing, durations={durations}"
    assert sum(durations) >= 10_000, f"animation too short, durations={durations}"
