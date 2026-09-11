"""问题3：判据 max_r C(r,t) < 0.15 kg/kg，确定烘干时长。

模型同问题2（附录3物性、两阶段风况），求解外推至判停。
输出：result3.xlsx、表5、字段 npz、图。
"""
import time

import numpy as np

import utils as U
from utils import Props, fmt4, save_json, simulate

T_MAX = 259200.0  # 72 h 上限


def run(N=20, dt=1.0, n_iter=2):
    t0 = time.time()
    s = simulate(t_max=T_MAX, dt=dt, N=N, props=Props(mode="att3"),
                 out_every=60.0, n_iter=n_iter, threshold=U.THRESHOLD)
    s.stats["runtime_s"] = time.time() - t0
    return s


def tables(s):
    """表5：行 6,12,18,...h + 烘干结束时间；列 r=0,0.5,1,1.5,2 cm。"""
    t_end = s.t_end_s
    rows_t, rows_lbl = [], []
    tv = 6 * 3600.0
    while tv < t_end - 1:
        rows_t.append(tv)
        rows_lbl.append(f"{tv/3600:.0f}")
        tv += 6 * 3600.0
    rows_t.append(t_end)
    rows_lbl.append(f"{t_end/3600:.4f} (结束)")
    table, table_idx = [], []
    tt = s.tout
    for tv in rows_t:
        i = int(np.argmin(np.abs(tt - tv)))
        table_idx.append(i)
        table.append([fmt4(s.C[i, j]) for j in [0, 5, 10, 15, 20]])
    return {"rows_h": rows_lbl, "radii_cm": [0.0, 0.5, 1.0, 1.5, 2.0],
            "table_C": table, "row_idx": table_idx,
            "t_end_s": fmt4(t_end), "t_end_h": fmt4(t_end / 3600.0)}


def write_result_xlsx(s, path):
    """行 60..(每60s) 至 t_end（含），列 0,0.1,...,2.0 cm。"""
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws.append(["时间\\到药材中心的距离"] + [fmt4(r) for r in s.r_cm])
    tt = s.tout
    for i, tv in enumerate(tt):
        if tv <= 0 or tv > s.t_end_s + 1e-9:
            continue
        is60 = abs(tv - round(tv / 60.0) * 60.0) < 1e-6
        is_last = i == len(tt) - 1
        if is60 or is_last:
            ws.append([fmt4(tv)] + [fmt4(v) for v in s.C[i]])
    wb.save(path)


def figures(s):
    import matplotlib.pyplot as plt
    import plot_utils as PU
    PU.setup()
    tt_h = s.tout / 3600.0
    # 图：各时刻剖面族
    fig, ax = plt.subplots(figsize=(6.0, 4.2))
    kmax = len(tt_h) - 1
    for hv in [3, 6, 9, 12, 15, 18]:
        i = int(np.searchsorted(tt_h, hv))
        if i <= kmax:
            ax.plot(s.r_cm, s.C[i], label=f"{hv} h")
    ax.plot(s.r_cm, s.C[kmax], "k:", lw=1.4, label=f"{tt_h[kmax]:.1f} h (结束)")
    ax.axhline(U.THRESHOLD, color="red", lw=1.0, ls="--", label="判停线 0.15")
    ax.set_xlabel("到中心距离 r / cm")
    ax.set_ylabel("水分浓度 C / (kg·kg$^{-1}$)")
    ax.legend(fontsize=8, ncols=2)
    fig.tight_layout()
    PU.save(fig, "fig_q3_profiles.pdf")
    # 图：max/avg/center C 随时间 + 判停
    fig, ax = plt.subplots(figsize=(5.8, 4.0))
    ax.plot(tt_h, np.max(s.C, axis=1), label="max C（中心）")
    ax.plot(tt_h, s.C[:, 0], label="中心 C")
    ax.plot(tt_h, s.C[:, -1], label="表面 C")
    ax.axhline(U.THRESHOLD, color="red", lw=1.0, ls="--", label="0.15 判停")
    ax.axvline(s.t_end_s / 3600.0, color="green", lw=1.0,
               label=f"t_end = {s.t_end_s/3600:.2f} h")
    ax.set_xlabel("时间 t / h"); ax.set_ylabel("C / (kg·kg$^{-1}$)")
    ax.set_yscale("log")
    ax.legend(fontsize=8.5)
    fig.tight_layout()
    PU.save(fig, "fig_q3_drycurves.pdf")
    # 图：C(r,t) 热力图
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    im = ax.pcolormesh(tt_h, s.r_cm, s.C.T, shading="auto", cmap="viridis")
    ax.set_xlabel("时间 t / h"); ax.set_ylabel("r / cm")
    cb = fig.colorbar(im, ax=ax, fraction=0.046)
    cb.set_label("C / (kg·kg$^{-1}$)")
    fig.tight_layout()
    PU.save(fig, "fig_q3_heatmap.pdf")


def main():
    s = run()
    tab = tables(s)
    res = dict(s.stats)
    res.update(tab)
    res["mass_err"] = s.mass_err
    write_result_xlsx(s, U.os.path.join(U.RESULTS_DIR, "result3.xlsx"))
    np.savez_compressed(U.os.path.join(U.OUT_DIR, "problem3_fields.npz"),
                        tout=s.tout, r=s.r_cm, T=s.T, C=s.C, R=s.R_cm,
                        t_end=s.t_end_s)
    save_json(res, "problem3.json")
    figures(s)
    print("P3 done %.1fs t_end=%.4f h" % (s.stats["runtime_s"], tab["t_end_h"]))
    print("表5:", tab["rows_h"], tab["table_C"])


if __name__ == "__main__":
    main()
