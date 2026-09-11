"""将 figures/*.drawio 渲染为同名 PDF（drawio CLI 不可用时的等价导出通道）。

支持本项目的 mxGraphModel 子集：rounded 方框 / ellipse / text 节点与正交边。
布局坐标与 .drawio 完全一致，保证源文件与论文插图一一对应。
"""
import glob
import html
import os
import re
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use("Agg")
import plot_utils as PU
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Ellipse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(ROOT, "figures")


def parse(fn):
    tree = ET.parse(fn)
    model = tree.find(".//mxGraphModel")
    page_w = float(model.get("pageWidth", 800))
    page_h = float(model.get("pageHeight", 600))
    nodes, edges = {}, []
    for c in tree.iter("mxCell"):
        cid = c.get("id")
        style = c.get("style") or ""
        geo = c.find("mxGeometry")
        if c.get("vertex") == "1" and geo is not None:
            raw = html.unescape(c.get("value") or "")
            nodes[cid] = dict(
                x=float(geo.get("x", 0)), y=float(geo.get("y", 0)),
                w=float(geo.get("width", 100)), h=float(geo.get("height", 40)),
                label=raw,
                fill=re.search(r"fillColor=([#0-9a-f]+)", style),
                stroke=re.search(r"strokeColor=([#0-9a-f]+)", style),
                kind=("ellipse" if "ellipse" in style else
                      "text" if style.startswith("text") else "box"),
            )
        if c.get("edge") == "1":
            src, tgt = c.get("source"), c.get("target")
            dashed = "dashed=1" in style
            lab = html.unescape(c.get("value") or "")
            if src in nodes and tgt in nodes:
                edges.append((src, tgt, dashed, lab))
    return page_w, page_h, nodes, edges


def anchor(a, b):
    """选择两框间最近的边界中点。"""
    cand = [(a["x"] + a["w"] / 2, a["y"] + a["h"], "b"),
            (a["x"] + a["w"] / 2, a["y"], "t"),
            (a["x"] + a["w"], a["y"] + a["h"] / 2, "r"),
            (a["x"], a["y"] + a["h"] / 2, "l")]
    tcx, tcy = b["x"] + b["w"] / 2, b["y"] + b["h"] / 2
    px, py = min(cand, key=lambda p: (p[0] - tcx) ** 2 + (p[1] - tcy) ** 2)[:2]
    cand2 = [(b["x"] + b["w"] / 2, b["y"] + b["h"], "b"),
             (b["x"] + b["w"] / 2, b["y"], "t"),
             (b["x"] + b["w"], b["y"] + b["h"] / 2, "r"),
             (b["x"], b["y"] + b["h"] / 2, "l")]
    qx, qy = min(cand2, key=lambda p: (p[0] - px) ** 2 + (p[1] - py) ** 2)[:2]
    return (px, py), (qx, qy)


def render(fn):
    name = os.path.splitext(os.path.basename(fn))[0]
    pw, ph, nodes, edges = parse(fn)
    fig, ax = plt.subplots(figsize=(pw / 72, ph / 72))
    ax.set_xlim(0, pw)
    ax.set_ylim(ph, 0)  # drawio y 向下
    ax.axis("off")
    for nid, n in nodes.items():
        fc = n["fill"].group(1) if n["fill"] else "none"
        sc = n["stroke"].group(1) if n["stroke"] else "none"
        if n["kind"] == "text":
            ax.text(n["x"], n["y"] + n["h"] / 2, n["label"], fontsize=8.2,
                    va="center", ha="left", fontweight="bold")
            continue
        if n["kind"] == "ellipse":
            ax.add_patch(Ellipse((n["x"] + n["w"] / 2, n["y"] + n["h"] / 2),
                                 n["w"], n["h"], facecolor=fc, edgecolor=sc, lw=1.1,
                                 alpha=0.55))
        else:
            ax.add_patch(FancyBboxPatch((n["x"] + 2, n["y"] + 2), n["w"] - 4, n["h"] - 4,
                                        boxstyle="round,pad=0,rounding_size=6",
                                        facecolor=fc, edgecolor=sc, lw=1.1))
        ax.text(n["x"] + n["w"] / 2, n["y"] + n["h"] / 2, n["label"],
                fontsize=7.6, ha="center", va="center", linespacing=1.35)
    for s, t, dashed, lab in edges:
        (px, py), (qx, qy) = anchor(nodes[s], nodes[t])
        ax.add_patch(FancyArrowPatch((px, py), (qx, qy),
                                     arrowstyle="-|>", mutation_scale=11,
                                     lw=1.1, color="#444444",
                                     linestyle="--" if dashed else "-",
                                     connectionstyle="angle,angleA=90,angleB=0,rad=6"))
        if lab:
            ax.text((px + qx) / 2, (py + qy) / 2 - 3, lab, fontsize=6.8, color="#555555")
    out = os.path.join(FIG, name + ".pdf")
    fig.savefig(out, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)
    print("exported", out)


if __name__ == "__main__":
    PU.setup()
    for fn in sorted(glob.glob(os.path.join(FIG, "*.drawio"))):
        render(fn)
