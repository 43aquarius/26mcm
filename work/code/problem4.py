"""问题4：考虑尺寸收缩（附件2 R(t)）的烘干过程，附录4 经验公式。

随体坐标 ξ=r/R(t) 动边界求解；输出 result4.xlsx、表6、字段 npz、图。
result4 列约定：0,0.1,…,1.1 cm（固定，均在内点，因 min R=1.198>1.1），
最后一列为“药材表面”（r=R(t) 处）。表6 列：0,0.5,1.0,药材表面。
"""
import time

import numpy as np

import utils as U
from utils import Props, fmt4, radius_schedule_cm, save_json, simulate

T_MAX = 302400.0  # 84 h 上限
R_FIXED = np.arange(0, 12) * 0.1  # 0..1.1 cm
R_SURF_NAME = "药材表面"


def run(N=40, dt=1.0, n_iter=2, out_every=60.0, mode="att4", shrink=True,
        threshold=U.THRESHOLD):
    t0 = time.time()
    Rf = (lambda t: float(np.interp(t, *_U_att2))) if shrink else None
    s = simulate(t_max=T_MAX, dt=dt, N=N, props=Props(mode=mode),
                 out_every=out_every, n_iter=n_iter, threshold=threshold,
                 R_of_t_cm=Rf)
    s.stats["runtime_s"] = time.time() - t0
    return s


_U_att2 = None


def main():
    global _U_att2
    _U_att2 = U.load_att2()
    s = run()
    # 插值到固定 0.1 cm 距离列 + 表面列
    C_tab = s.C
    r_moving = (np.arange(s.r_cm.shape[1]) / s.r_cm.shape[1]) * s.R_cm[:, None]
    nt = len(s.tout)
    fixed = np.zeros((nt, len(R_FIXED)))
    surf = np.zeros(nt)
    for i in range(nt):
        fixed[i] = np.interp(R_FIXED, r_moving[i], C_tab[i])
        surf[i] = C_tab[i, -1]
    t_end = s.t_end_s
    # 表6：每6h + 结束行；列 0,0.5,1.0,表面
    rows_t, rows_lbl = [], []
    tv = 6 * 3600.0
    while tv < t_end - 1:
        rows_t.append(tv)
        rows_lbl.append(f"{tv/3600:.0f}")
        tv += 6 * 3600.0
    rows_t.append(t_end)
    rows_lbl.append(f"{t_end/3600:.4f} (结束)")
    table = []
    for tv in rows_t:
        i = int(np.argmin(np.abs(s.tout - tv)))
        row = [fmt4(np.interp(rr, r_moving[i], s.C[i])) for rr in [0.0, 0.5, 1.0]]
        row.append(fmt4(s.C[i, -1]))
        table.append(row)
    # 写 result4.xlsx
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws.append(["时间\\到药材中心的距离"] + [fmt4(r) for r in R_FIXED] + [R_SURF_NAME])
    for i, tv in enumerate(s.tout):
        if tv <= 0 or tv > t_end + 1e-9:
            continue
        if abs(tv - round(tv / 60.0) * 60.0) < 1e-6 or i == nt - 1:
            ws.append([fmt4(tv)] + [fmt4(v) for v in fixed[i]] + [fmt4(surf[i])])
    wb.save(U.os.path.join(U.RESULTS_DIR, "result4.xlsx"))
    # 无收缩对照（同物性附录4，R=2恒定）
    s_ns = run(N=40, dt=1.0, shrink=False, threshold=U.THRESHOLD)
    res = dict(s.stats)
    res.update({
        "rows_h": rows_lbl,
        "cols_cm": [0.0, 0.5, 1.0, "药材表面"],
        "table_C": table,
        "t_end_s": fmt4(t_end), "t_end_h": fmt4(t_end / 3600.0),
        "t_end_noshrink_h": fmt4(s_ns.t_end_s / 3600.0),
        "R_final_cm": fmt4(s.R_cm[-1]),
        "mass_err": s.mass_err,
        "mass_err_noshrink": s_ns.mass_err,
    })
    save_json(res, "problem4.json")
    np.savez_compressed(U.os.path.join(U.OUT_DIR, "problem4_fields.npz"),
                        tout=s.tout, C=C_tab, fixed=fixed, surf=surf,
                        r_moving=r_moving,
                        R_cm=s.R_cm, t_end=t_end,
                        tout_ns=s_ns.tout, C_ns=s_ns.C)
    figures(s, s_ns, fixed, surf, r_moving)
    print("P4 done %.1fs t_end=%.4f h; 无收缩对照 %.4f h" %
          (s.stats["runtime_s"], res["t_end_h"], res["t_end_noshrink_h"]))
    print("表6:", rows_lbl, table)


def figures(s, s_ns, fixed, surf, r_moving):
    import matplotlib.pyplot as plt
    import plot_utils as PU
    PU.setup()
    tt_h = s.tout / 3600.0
    # 图1：剖面族（物理坐标）+ 判停线
    fig, ax = plt.subplots(figsize=(6.0, 4.2))
    for hv in [6, 12, 18, 24, 30]:
        i = int(np.searchsorted(tt_h, hv))
        if i < len(tt_h) - 1:
            ax.plot(r_moving[i], s.C[i], label=f"{hv} h")
    ax.plot(r_moving[-1], s.C[-1], "k:", lw=1.4,
            label=f"{tt_h[-1]:.1f} h (结束)")
    ax.axhline(U.THRESHOLD, color="red", ls="--", lw=1.0, label="判停线 0.15")
    ax.set_xlabel("到中心距离 r / cm")
    ax.set_ylabel("C / (kg·kg$^{-1}$)")
    ax.legend(fontsize=8, ncols=2)
    fig.tight_layout()
    PU.save(fig, "fig_q4_profiles.pdf")
    # 图2：收缩 vs 不收缩：表面 C 与中心 C，标注两模型干燥前沿
    fig, axes = plt.subplots(1, 2, figsize=(9.4, 3.8), sharey=True)
    axes[0].plot(tt_h, s.C[:, 0], label="中心（收缩）")
    axes[0].plot(tt_h, s.C[:, -1], label="表面（收缩）")
    tn_h = s_ns.tout / 3600.0
    axes[0].plot(tn_h, s_ns.C[:, 0], "--", color="gray", label="中心（不收缩对照）")
    axes[0].axhline(0.15, color="red", lw=0.9, ls=":")
    axes[0].set_yscale("log")
    axes[0].set_xlabel("t / h"); axes[0].set_ylabel("C / (kg·kg$^{-1}$)")
    axes[0].legend(fontsize=8)
    axes[1].plot(tt_h, s.R_cm, color="tab:purple")
    axes[1].set_xlabel("t / h"); axes[1].set_ylabel("药材半径 R(t) / cm",
                                                     color="tab:purple")
    i_end = int(np.argmin(np.abs(s.tout - s.t_end_s)))
    axes[1].plot(s.tout[i_end]/3600.0, s.R_cm[i_end], "o")
    axes[1].axvline(s.t_end_s / 3600, color="green", lw=1.0)
    axes[1].axvline(s_ns.t_end_s / 3600, color="gray", lw=1.0, ls="--")
    axes[1].legend(["R(t)", "t_end(收缩)", "t_end(对照)"], fontsize=8)
    fig.tight_layout()
    PU.save(fig, "fig_q4_shrink.pdf")
    # 图3：C(r,t) 热力图（含收缩包络）
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    im = ax.pcolormesh(tt_h, np.linspace(0, 1, s.C.shape[1]),
                       s.C.T, shading="auto", cmap="viridis")
    ax.plot(tt_h, s.R_cm / 2.0, "w--", lw=1.2, label="表面（ξ=1）")
    ax.set_xlabel("时间 t / h"); ax.set_ylabel("ξ = r/R(t)")
    ax.legend(fontsize=8)
    cb = fig.colorbar(im, ax=ax, fraction=0.046)
    cb.set_label("C / (kg·kg$^{-1}$)")
    fig.tight_layout()
    PU.save(fig, "fig_q4_heatmap.pdf")


if __name__ == "__main__":
    main()
