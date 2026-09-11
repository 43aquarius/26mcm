"""绘图公共样式：中文字体、统一风格、PDF 矢量输出。"""
import glob
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

FONT_DIR = os.path.expanduser("~/fonts")
_registered = False


def setup():
    global _registered
    if _registered:
        return
    for f in glob.glob(os.path.join(FONT_DIR, "*.otf")) + glob.glob(os.path.join(FONT_DIR, "*.ttf")):
        try:
            font_manager.fontManager.addfont(f)
        except Exception:
            pass
    plt.rcParams.update({
        "font.family": ["sans-serif"],
        "font.sans-serif": ["Source Han Sans CN", "DejaVu Sans"],
        "axes.unicode_minus": False,
        "font.size": 10.5,
        "axes.titlesize": 11,
        "axes.labelsize": 10.5,
        "legend.fontsize": 9,
        "xtick.labelsize": 9.5,
        "ytick.labelsize": 9.5,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "grid.linestyle": "--",
        "lines.linewidth": 1.6,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.dpi": 150,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.02,
    })
    _registered = True


def save(fig, name):
    from utils import FIG_DIR
    path = os.path.join(FIG_DIR, name)
    fig.savefig(path)
    plt.close(fig)
    print("saved", path)
    return path
