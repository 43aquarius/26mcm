"""问题2：整个烘干过程模型（附录3 统一经验公式），论文给 0–3 h。

预热平衡段（0–14400 s）风况取附件1；恒温干燥段取附件1末30min均值恒定。
输出：result2.xlsx、表3/表4、字段 npz、图。
"""
import time

import numpy as np

import utils as U
from utils import Props, air_schedule, fmt4, save_json, simulate

T_3H = 10800.0


def run(N=20, dt=0.25, n_iter=2, out_every=1.0):
    t0 = time.time()
    s = simulate(t_max=T_3H, dt=dt, N=N, props=Props(mode="att3"),
                 out_every=out_every, n_iter=n_iter)
    s.stats["runtime_s"] = time.time() - t0
    return s


def tables(s):
    ti = [int(round(tv / s.tout[1])) for tv in [1800, 3600, 5400, 7200, 9000, 10800]]
    ri = [0, 5, 10, 15, 20]
    return {"times_h": [0.5, 1.0, 1.5, 2.0, 2.5, 3.0],
            "radii_cm": [0.0, 0.5, 1.0, 1.5, 2.0],
            "table_T": [[fmt4(s.T[i, j]) for j in ri] for i in ti],
            "table_C": [[fmt4(s.C[i, j]) for j in ri] for i in ti]}


def write_result_xlsx(s, path):
    import openpyxl
    wb = openpyxl.Workbook()
    for k, (sheet, field) in enumerate([("温度", s.T), ("水分浓度", s.C)]):
        ws = wb.active if k == 0 else wb.create_sheet()
        ws.title = sheet
        ws.append(["时间\\到药材中心的距离"] + [fmt4(r) for r in s.r_cm])
        for i in range(len(s.tout)):
            tsec = int(round(s.tout[i]))
            if tsec <= 0:
                continue
            ws.append([tsec] + [fmt4(v) for v in field[i]])
    wb.save(path)


def figures(s):
    import matplotlib.pyplot as plt
    import plot_utils as PU
    PU.setup()
    r = s.r_cm
    tt = s.tout
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.8))
    for hv in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]:
        i = int(round(hv * 3600 / tt[1]))
        axes[0].plot(r, s.T[i], label=f"{hv} h")
        axes[1].plot(r, s.C[i], label=f"{hv} h")
    axes[0].set_xlabel("r / cm"); axes[0].set_ylabel("温度 T / °C")
    axes[0].set_title("温度剖面（附录3物性）", fontsize=10)
    axes[1].set_xlabel("r / cm")
    axes[1].set_ylabel("水分浓度 C / (kg·kg$^{-1}$)")
    axes[1].set_title("水分浓度剖面", fontsize=10)
    for ax in axes:
        ax.legend(fontsize=8)
    fig.tight_layout()
    PU.save(fig, "fig_q2_profiles.pdf")

    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.6))
    im0 = axes[0].imshow(s.T, origin="lower", aspect="auto", cmap="magma",
                         extent=[0, tt[-1] / 3600.0, 0, r[-1]])
    axes[0].set_xlabel("时间 t / h"); axes[0].set_ylabel("r / cm")
    axes[0].set_title("温度场 T(r,t) 演化（0–3 h）", fontsize=10)
    im1 = axes[1].imshow(s.C, origin="lower", aspect="auto", cmap="viridis",
                         extent=[0, tt[-1] / 3600.0, 0, r[-1]])
    axes[1].set_xlabel("时间 t / h"); axes[1].set_ylabel("r / cm")
    axes[1].set_title("水分浓度场 C(r,t) 演化", fontsize=10)
    for ax, im, lab in zip(axes, (im0, im1),
                           ("T / °C", "C / (kg·kg$^{-1}$)")):
        cb = fig.colorbar(im, ax=ax, fraction=0.046)
        cb.set_label(lab, fontsize=9)
        cb.outline.set_visible(False)
    fig.tight_layout()
    PU.save(fig, "fig_q2_evolution.pdf")


def s_interp(tnew, told, Y):
    """(nt,nr) 场按列插值到新时间网格 -> (len(tnew), nr)"""
    return np.vstack([np.interp(tnew, told, Y[:, j]) for j in range(Y.shape[1])]).T


def main():
    s = run()
    tab = tables(s)
    res = dict(s.stats)
    res.update(tab)
    res["mass_err"] = s.mass_err
    res["att1_tail_mean"] = U.att1_tail_mean()
    write_result_xlsx(s, U.os.path.join(U.RESULTS_DIR, "result2.xlsx"))
    np.savez_compressed(U.os.path.join(U.OUT_DIR, "problem2_fields.npz"),
                        tout=s.tout, r=s.r_cm, T=s.T, C=s.C)
    save_json(res, "problem2.json")
    figures(s)
    print("P2 done %.1fs" % s.stats["runtime_s"])
    print("表3:", tab["table_T"])
    print("表4:", tab["table_C"])


if __name__ == "__main__":
    main()
