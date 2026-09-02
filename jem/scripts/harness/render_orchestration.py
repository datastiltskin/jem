#!/usr/bin/env python3
"""
Render the orchestration run as a static diagram, an animated GIF, and a video.

One wave structure drives every output, so the picture cannot drift from the
narrative in ledger/ORCHESTRATION_RUN.md the way two hand-drawn diagrams would.

The GIF is written with a *single shared palette* and every frame in mode P.
A mixed-mode GIF (frame 0 paletted, later frames RGB) is what made downloads
and copy-paste look empty: many viewers only honour the first frame's palette.

Usage:
    python3 scripts/harness/render_orchestration.py
    python3 scripts/harness/render_orchestration.py --outdir ledger/diagrams
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
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

DURATIONS_MS = [1500, 1500, 1500, 1500, 1500, 3800]

# Printed on every frame so a downloaded GIF is self-explanatory.
LEGEND = (
    "S schema  ·  C commercial courts (TN)  ·  K criminal magistracy (TN)  ·  "
    "N classification + counting  ·  W1–W6 = waves  ·  ∥ = parallel"
)


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
    ax.set_ylim(-0.92, 6.6)
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
        ax.axvline(x, ymin=0.12, ymax=0.80, color=RULE, lw=1,
                   ls=(0, (2, 3)), zorder=0)
        _txt(ax, x, 5.86, tag, size=8, weight="bold", ha="center",
             color=INK if on else "#c9c4bb")
        _txt(ax, x, 5.62, name, size=8.2, ha="center",
             color=INK if on else "#c9c4bb")
        _txt(ax, x, 0.18, detail, size=6.6, ha="center", va="top",
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

    # Colour key + letter legend (must travel with the downloaded asset)
    key = [
        (ORCH, "Orchestrator"),
        (GEN, "C ∥ K generation"),
        (VERIFY, "N recount (other family)"),
        (META, "Report-publication"),
        (GATE, "Gate / refusal"),
    ]
    xk = 0.35
    for colour, label in key:
        ax.add_patch(mpatches.FancyBboxPatch(
            (xk, -0.72), 0.22, 0.18,
            boxstyle="round,pad=0.008,rounding_size=0.04",
            facecolor=colour, edgecolor="none", zorder=6))
        _txt(ax, xk + 0.30, -0.63, label, size=6.4, color=MUTED, va="center")
        xk += 2.35
    _txt(ax, 0.35, -0.88, LEGEND, size=6.6, color=INK, va="center")


def _savefig(fig, path: Path):
    fig.savefig(path, facecolor=PAPER, bbox_inches="tight")
    plt.close(fig)


def render_static(outdir: Path) -> Path:
    fig, ax = plt.subplots(figsize=(13.2, 7.6), dpi=170)
    fig.patch.set_facecolor(PAPER)
    draw(ax, upto_wave=None)
    out = outdir / "orchestration.png"
    _savefig(fig, out)
    return out


def _write_frames(tmpdir: Path, dpi: int = 140) -> list[Path]:
    paths = []
    for w in range(len(WAVES)):
        fig, ax = plt.subplots(figsize=(13.2, 7.6), dpi=dpi)
        fig.patch.set_facecolor(PAPER)
        draw(ax, upto_wave=w)
        p = tmpdir / f"f{w:02d}.png"
        _savefig(fig, p)
        paths.append(p)
    return paths


def _paletted_frames(pngs: list[Path]):
    """Quantize every frame against the last frame's palette.

    The last wave is the fullest picture, so its 256 colours cover the earlier
    (sparser) frames. Sharing one palette is what keeps the GIF animated in
    browsers, Slack, and 'Save image' downloads.
    """
    from PIL import Image

    rgb = [Image.open(p).convert("RGB") for p in pngs]
    # Same size required for GIF; crop/pad if matplotlib bbox_inches drifted.
    w = max(im.width for im in rgb)
    h = max(im.height for im in rgb)
    padded = []
    for im in rgb:
        if im.size != (w, h):
            canvas = Image.new("RGB", (w, h), PAPER)
            canvas.paste(im, (0, 0))
            padded.append(canvas)
        else:
            padded.append(im)
    palette_src = padded[-1].quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    return [
        im.quantize(palette=palette_src, dither=Image.Dither.NONE)
        for im in padded
    ]


def _write_concat(outdir: Path, pngs: list[Path]) -> Path:
    concat = outdir / "_concat.txt"
    lines = []
    for p, ms in zip(pngs, DURATIONS_MS):
        lines.append(f"file '{p.resolve()}'")
        lines.append(f"duration {ms / 1000:.3f}")
    # concat demuxer needs the last file repeated with no duration
    lines.append(f"file '{pngs[-1].resolve()}'")
    concat.write_text("\n".join(lines) + "\n")
    return concat


def _gif_via_ffmpeg(outdir: Path, concat: Path) -> Path | None:
    """Global-palette GIF. Survives Save-image and more viewers than Pillow."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return None
    out = outdir / "orchestration.gif"
    cmd = [
        ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(concat),
        "-filter_complex",
        "[0:v]split[a][b];"
        "[a]palettegen=reserve_transparent=0:stats_mode=full[p];"
        "[b][p]paletteuse=dither=none",
        "-loop", "0",
        str(out),
    ]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        return None
    return out if out.is_file() and out.stat().st_size > 0 else None


def _gif_via_pillow(outdir: Path, pngs: list[Path]) -> Path:
    frames = _paletted_frames(pngs)
    out = outdir / "orchestration.gif"
    # optimize=False keeps the shared palette intact — optimize=True was
    # the setting that produced a file some viewers render blank.
    frames[0].save(
        out,
        save_all=True,
        append_images=frames[1:],
        duration=DURATIONS_MS,
        loop=0,
        optimize=False,
        disposal=2,
    )
    return out


def _assert_gif_has_ink(path: Path, min_colors: int = 20) -> None:
    from PIL import Image
    im = Image.open(path)
    n = getattr(im, "n_frames", 1)
    if n < len(WAVES):
        raise RuntimeError(f"{path} has {n} frames, want at least {len(WAVES)}")
    for i in range(n):
        im.seek(i)
        colors = im.convert("RGB").getcolors(maxcolors=1_000_000)
        count = 0 if colors is None else len(colors)
        # None means "too many colours to list" — definitely not empty.
        if colors is not None and count < min_colors:
            raise RuntimeError(f"{path} frame {i} looks empty ({count} colours)")


def render_gif(outdir: Path, pngs: list[Path] | None = None) -> Path:
    own_tmp = None
    if pngs is None:
        own_tmp = Path(tempfile.mkdtemp(prefix="jem-orch-"))
        pngs = _write_frames(own_tmp)

    concat = _write_concat(outdir, pngs)
    try:
        out = _gif_via_ffmpeg(outdir, concat) or _gif_via_pillow(outdir, pngs)
    finally:
        concat.unlink(missing_ok=True)

    _assert_gif_has_ink(out)

    if own_tmp is not None:
        shutil.rmtree(own_tmp, ignore_errors=True)
    return out


def render_video(outdir: Path, pngs: list[Path], stem: str = "orchestration") -> list[Path]:
    """H.264 MP4 (and WebM if the encoder exists). Copy-paste-safe for chat apps."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return []

    concat = _write_concat(outdir, pngs)

    written = []
    mp4 = outdir / f"{stem}.mp4"
    cmd = [
        ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(concat),
        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(mp4),
    ]
    try:
        subprocess.run(cmd, check=True)
        written.append(mp4)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    webm = outdir / f"{stem}.webm"
    cmd_webm = [
        ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(concat),
        "-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "32",
        "-pix_fmt", "yuv420p",
        str(webm),
    ]
    try:
        subprocess.run(cmd_webm, check=True)
        written.append(webm)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    concat.unlink(missing_ok=True)
    return written


def main():
    ap = argparse.ArgumentParser(description="Render the orchestration diagram")
    ap.add_argument("--outdir", default=None)
    args = ap.parse_args()

    repo = Path(__file__).resolve().parent.parent.parent
    outdir = Path(args.outdir) if args.outdir else repo / "ledger" / "diagrams"
    outdir.mkdir(parents=True, exist_ok=True)

    png = render_static(outdir)
    tmp = Path(tempfile.mkdtemp(prefix="jem-orch-"))
    try:
        frames = _write_frames(tmp)
        gif = render_gif(outdir, frames)
        videos = render_video(outdir, frames)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    for p in (png, gif, *videos):
        print(f"  wrote {p}  ({p.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
