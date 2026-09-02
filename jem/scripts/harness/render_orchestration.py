#!/usr/bin/env python3
"""
Render the orchestration run as a static diagram and an animated GIF.

One wave structure drives both outputs, so the picture cannot drift from the
narrative in ledger/ORCHESTRATION_RUN.md the way two hand-drawn diagrams would.

Usage:
    python3 scripts/harness/render_orchestration.py
    python3 scripts/harness/render_orchestration.py --outdir ledger/diagrams
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.patheffects import withStroke

INK = "#1a1a1a"
MUTED = "#6b6b6b"
RULE = "#d8d4cc"
PAPER = "#faf8f5"

ORCH = "#2c5f7c"      # orchestrator
GEN = "#8b5a2b"       # generation agents
VERIFY = "#6a4c93"    # independent verifier (different model family)
META = "#1b7a5a"      # meta-provenance
GATE = "#b03a2e"      # gates and refusals

# (id, label, sublabel, model, colour, lane, start_wave, end_wave)
AGENTS = [
    ("orch", "Orchestrator", "S · N · harness · promotion", "Claude Opus 5", ORCH, 0, 0, 6),
    ("k",    "Track K",      "TN criminal magistracy",      "Opus 5 (inherited)", GEN, 1, 2, 4),
    ("c",    "Track C",      "TN commercial courts",        "Opus 5 (inherited)", GEN, 2, 2, 4),
    ("n",    "Recount verifier", "independent recount",     "GPT-5.6 Sol", VERIFY, 3, 3, 4),
    ("rep",  "Report-publication", "12 tribunals/regulators", "Sonnet 5", META, 4, 4, 5),
]

WAVES = [
    ("W1", "Apply S", "schema foundation\nvalidate --strict = 0"),
    ("W2", "Liveness gate", "0/12 registry URLs pass\nIndia Code migration found"),
    ("W3", "Dispatch C ∥ K", "disjoint file scopes\ngeneration in parallel"),
    ("W4", "N + recount", "counts artifact\nPASS on 6 buckets"),
    ("W5", "Verify + promote", "6/6 claims confirmed\nin source PDFs"),
    ("W6", "Merge + PR", "report blocks merged\nCI green"),
]

# Wave in which each agent hands back to the orchestrator.
HANDOVERS = {"k": 5, "c": 5, "n": 4, "rep": 6}


def _txt(ax, x, y, s, size=9, color=INK, weight="normal", ha="left", va="center",
         style="normal", family="DejaVu Sans"):
    return ax.text(x, y, s, fontsize=size, color=color, fontweight=weight,
                   ha=ha, va=va, style=style, family=family, zorder=6)


def _lane_y(lane):
    return 5.4 - lane * 1.02


def _wave_x(w):
    return 1.9 + w * 1.72


def draw(ax, upto_wave=None, title=True):
    """Draw the orchestration. upto_wave=None draws everything (static)."""
    ax.set_xlim(0, 12.6)
    ax.set_ylim(-0.55, 6.6)
    ax.axis("off")
    ax.set_facecolor(PAPER)

    active = 10 ** 6 if upto_wave is None else upto_wave

    if title:
        _txt(ax, 0.35, 6.32, "JEM data-integrity packet — orchestration",
             size=13, weight="bold")
        _txt(ax, 0.35, 5.98,
             "6 agents · 3 model families · 2026-09-01",
             size=8.5, color=MUTED)

    # Wave columns
    for i, (tag, name, detail) in enumerate(WAVES):
        x = _wave_x(i)
        on = i <= active
        ax.axvline(x, ymin=0.04, ymax=0.80, color=RULE, lw=1,
                   ls=(0, (2, 3)), zorder=0)
        _txt(ax, x, 5.86, tag, size=8, weight="bold", ha="center",
             color=INK if on else "#c9c4bb")
        _txt(ax, x, 5.62, name, size=8.2, ha="center",
             color=INK if on else "#c9c4bb")
        _txt(ax, x, 0.12, detail, size=6.6, ha="center", va="top",
             color=MUTED if on else "#d3cec6")

    # Agent lanes
    for aid, label, sub, model, colour, lane, w0, w1 in AGENTS:
        y = _lane_y(lane)
        ax.plot([0.35, 12.3], [y, y], color=RULE, lw=0.8, zorder=0)
        _txt(ax, 0.35, y + 0.30, label, size=9, weight="bold",
             color=colour if w0 <= active else "#c9c4bb")
        _txt(ax, 0.35, y + 0.06, sub, size=6.8, color=MUTED)
        _txt(ax, 0.35, y - 0.16, model, size=6.4, color=MUTED, style="italic")

        # Activity bar across the waves this agent is live for
        x0, x1 = _wave_x(w0 - 1), _wave_x(min(w1, len(WAVES)) - 1)
        started = w0 - 1 <= active
        if started:
            xe = min(x1, _wave_x(min(active, len(WAVES) - 1)))
            if xe > x0:
                ax.add_patch(mpatches.FancyBboxPatch(
                    (x0, y - 0.17), xe - x0, 0.34,
                    boxstyle="round,pad=0.008,rounding_size=0.16",
                    facecolor=colour, edgecolor="none", alpha=0.88, zorder=3))

        # Handover marker back to the orchestrator
        hw = HANDOVERS.get(aid)
        if hw is not None and hw - 1 <= active:
            hx = _wave_x(hw - 1)
            ax.annotate("", xy=(hx, _lane_y(0) - 0.20), xytext=(hx, y + 0.17),
                        arrowprops=dict(arrowstyle="-|>", color=colour, lw=1.3,
                                        alpha=0.85,
                                        connectionstyle="arc3,rad=0.16"),
                        zorder=5)

        # Dispatch marker from the orchestrator
        if w0 >= 2 and w0 - 1 <= active:
            dx = _wave_x(w0 - 1)
            ax.annotate("", xy=(dx, y + 0.17), xytext=(dx, _lane_y(0) - 0.20),
                        arrowprops=dict(arrowstyle="-|>", color=colour, lw=1.1,
                                        alpha=0.45, ls="--",
                                        connectionstyle="arc3,rad=-0.16"),
                        zorder=4)

    # The parallel bracket over C and K
    if active >= 2:
        yk, yc = _lane_y(1), _lane_y(2)
        bx = _wave_x(2) + 0.42
        ax.plot([bx, bx + 0.16, bx + 0.16, bx],
                [yk + 0.17, yk + 0.17, yc - 0.17, yc - 0.17],
                color=GEN, lw=1.1, alpha=0.7, zorder=4)
        _txt(ax, bx + 0.26, (yk + yc) / 2, "parallel\n(disjoint\nscopes)",
             size=6.3, color=GEN)

    # Gate callouts
    notes = [
        (0, "gate: 0 errors on\nthe untouched corpus", GATE, 1),
        (1, "soft-404 shell\nrejected", GATE, 2),
        (4, "6/6 verified in\nsource PDFs", GATE, 5),
    ]
    for wi, text, colour, need in notes:
        if active >= need - 1:
            x = _wave_x(wi)
            t = _txt(ax, x + 0.10, 4.95, text, size=6.4, color=colour, weight="bold")
            t.set_path_effects([withStroke(linewidth=2.4, foreground=PAPER)])


def render_static(outdir: Path):
    fig, ax = plt.subplots(figsize=(13.2, 7.0), dpi=170)
    fig.patch.set_facecolor(PAPER)
    draw(ax, upto_wave=None)
    out = outdir / "orchestration.png"
    fig.savefig(out, facecolor=PAPER, bbox_inches="tight")
    plt.close(fig)
    return out


def render_gif(outdir: Path):
    from PIL import Image
    frames, tmp = [], outdir / "_frames"
    tmp.mkdir(parents=True, exist_ok=True)
    for w in range(len(WAVES)):
        fig, ax = plt.subplots(figsize=(13.2, 7.0), dpi=140)
        fig.patch.set_facecolor(PAPER)
        draw(ax, upto_wave=w)
        p = tmp / f"f{w:02d}.png"
        fig.savefig(p, facecolor=PAPER, bbox_inches="tight")
        plt.close(fig)
        frames.append(Image.open(p).convert("P", palette=Image.ADAPTIVE))

    out = outdir / "orchestration.gif"
    # Hold the final frame so the completed picture is readable on loop.
    durations = [1500] * (len(frames) - 1) + [3800]
    frames[0].save(out, save_all=True, append_images=frames[1:],
                   duration=durations, loop=0, optimize=True)
    for p in tmp.glob("*.png"):
        p.unlink()
    tmp.rmdir()
    return out


def main():
    ap = argparse.ArgumentParser(description="Render the orchestration diagram")
    ap.add_argument("--outdir", default=None)
    args = ap.parse_args()

    repo = Path(__file__).resolve().parent.parent.parent
    outdir = Path(args.outdir) if args.outdir else repo / "ledger" / "diagrams"
    outdir.mkdir(parents=True, exist_ok=True)

    png = render_static(outdir)
    gif = render_gif(outdir)
    for p in (png, gif):
        print(f"  wrote {p}  ({p.stat().st_size/1024:.0f} KB)")


if __name__ == "__main__":
    main()
