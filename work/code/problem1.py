"""问题1：预热平衡阶段（0–1800 s）温度场与水分浓度场。

附录2 物性 + D=7e-9·exp(-0.89/C)；风况取附件1。
输出：results/result1.xlsx（按附件3模板）、表1/表2、字段 npz、图。
"""
import time

import numpy as np

import utils as U
from utils import Props, air_schedule, fmt4, save_json, simulate


def run(N=20, dt=0.25, n_iter=2, out_every=1.0, tag=""):
    t0 = time.time()
    s = simulate(
        t_max=1800, dt=dt, N=N, props=Props(mode="att2"),
        out_every=out_every, n_iter=n_iter,
    )
    rt = time.time() - t0
    s.stats["runtime_s"] = rt
    return s


def tables(s):
    """表1/表2：行 t=100..1800，列 r=0,0.5,1,1.5,2 cm。"""
    ti = [int(round(tv / s.tout[1])) for tv in [100, 300, 600, 900, 1200, 1500, 1800]]
    ri = [0, 5, 10, 15, 20]
    T_tab = [[fmt4(s.T[i, j]) for j in ri] for i in ti]
    C_tab = [[fmt4(s.C[i, j]) for j in ri] for i in ti]
    return {"times_s": [100, 300, 600, 900, 1200, 1500, 1800],
            "radii_cm": [0.0, 0.5, 1.0, 1.5, 2.0],
            "table_T": T_tab, "table_C": C_tab}


def write_result_xlsx(s, path):
    import openpyxl
    wb = openpyxl.Workbook()
    n = len(s.tout)
    for k, (sheet, field) in enumerate([("温度", s.T), ("水分浓度", s.C)]):
        ws = wb.active if k == 0 else wb.create_sheet()
        ws.title = sheet
        ws.append(["时间\\到药材中心的距离"] + [fmt4(r) for r in s.r_cm])
        for i in range(n):
            tsec = int(round(s.tout[i]))
            if tsec <= 0:
                continue
            ws.append([tsec] + [fmt4(v) for v in field[i]])
    wb.save(path)


def figures(s):
    import matplotlib.pyplot as plt
    import plot_utils as PU
    PU.setup()
    tt = s.tout
    r = s.r_cm
    # 图1：温度剖面族
    fig, ax = plt.subplots(figsize=(5.6, 4.0))
    for tv, ls in zip([100, 300, 600, 900, 1200, 1500, 1800],
                      ["-", "--", "-.", (0, (5, 2)), (0, (3, 1, 1, 1)), (0, (1, 1)), (0, (3, 5, 1, 5))]):
        i = int(round(tv / tt[1]))
        ax.plot(r, s.T[i], linestyle=ls, label=f"t = {tv} s")
    ax.set_xlabel("到药材中心的距离 r / cm")
    ax.set_ylabel("温度 T / °C")
    ax.legend(loc="upper left", ncols=2, fontsize=8)
    fig.tight_layout()
    PU.save(fig, "fig_q1_temp_profiles.pdf")
    # 图2：水分剖面族
    fig, ax = plt.subplots(figsize=(5.6, 4.0))
    for tv in [100, 300, 600, 900, 1200, 1500, 1800]:
        i = int(round(tv / tt[1]))
        ax.plot(r, s.C[i], label=f"t = {tv} s")
    ax.set_xlabel("到药材中心的距离 r / cm")
    ax.set_ylabel("水分浓度 C / (kg·kg$^{{-1}}$)")
    ax.legend(loc="center left", bbox_to_anchor=(1.0, 0.5), fontsize=8)
    fig.tight_layout()
    PU.save(fig, "fig_q1_moist_profiles.pdf")
    # 图3：中心与表面随时间演化（双轴）
    fig, ax1 = plt.subplots(figsize=(5.8, 4.0))
    ax1.plot(tt, s.T[:, 0], label="中心温度", color="tab:red")
    ax1.plot(tt, s.T[:, -1], "--", label="表面温度", color="tab:red")
    Ta_a, _ = air_schedule(tt)
    ax1.plot(tt, Ta_a, ":", label="烘房风温", color="black", lw=1.2)
    ax1.set_xlabel("时间 t / s")
    ax1.set_ylabel("温度 / °C", color="tab:red")
    ax1.tick_params(axis="y", labelcolor="tab:red")
    ax2 = ax1.twinx()
    ax2.plot(tt, s.C[:, 0], label="中心水分", color="tab:blue")
    ax2.plot(tt, s.C[:, -1], "--", label="表面水分", color="tab:blue")
    ax2.set_ylabel("水分浓度 / (kg·kg$^{-1}$)", color="tab:blue")
    ax2.tick_params(axis="y", labelcolor="tab:blue")
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="center right", fontsize=8.5)
    fig.tight_layout()
    PU.save(fig, "fig_q1_evol.pdf")


def main():
    s = run()
    tab = tables(s)
    res = dict(s.stats)
    res.update(tab)
    res["mass_err"] = s.mass_err
    write_result_xlsx(s, U.os.path.join(U.RESULTS_DIR, "result1.xlsx"))
    np.savez_compressed(
        U.os.path.join(U.OUT_DIR, "problem1_fields.npz"),
        tout=s.tout, r=s.r_cm, T=s.T, C=s.C,
    )
    save_json(res, "problem1.json")
    figures(s)
    print("P1 done in %.1fs" % s.stats["runtime_s"])
    print("表1 温度:", tab["table_T"])
    print("表2 水分:", tab["table_C"])


if __name__ == "__main__":
    main()
