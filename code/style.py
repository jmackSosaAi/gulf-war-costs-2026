"""Shared visual style for the report figures. Import in every figure script."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

INK = "#1a1f24"; INK2 = "#52514e"; MUTED = "#8a939c"; GRID = "#e3e6ea"; SURFACE = "#ffffff"
NEUTRAL = "#b8c0c8"; NEUTRAL_LIGHT = "#dde2e7"
BLUE = "#2a78d6"; ORANGE = "#eb6834"; AQUA = "#1baf7a"
ACCENT = ORANGE   # the highlight colour

_fonts = {f.name for f in font_manager.fontManager.ttflist}
FONT = next((f for f in ["Helvetica Neue", "Helvetica", "Arial"] if f in _fonts), "DejaVu Sans")

def setup():
    plt.rcParams.update({
        "font.family": FONT, "font.size": 9, "text.color": INK,
        "axes.edgecolor": MUTED, "axes.labelcolor": INK2, "axes.linewidth": 0.6,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
        "xtick.color": INK2, "ytick.color": INK2, "xtick.labelsize": 8, "ytick.labelsize": 8,
        "legend.frameon": False, "legend.fontsize": 8,
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
        "svg.fonttype": "none", "savefig.bbox": "tight", "savefig.pad_inches": 0.05,
        "lines.linewidth": 2,
    })

def save(fig, path_no_ext):
    fig.savefig(path_no_ext + ".svg")
    fig.savefig(path_no_ext + ".png", dpi=220)
    plt.close(fig)
