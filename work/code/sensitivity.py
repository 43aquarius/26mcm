"""灵敏度分析与数值检验：网格/步长收敛、参数扰动、边界条件与模型变体。

产出 results/sensitivity.json 与图 fig_conv.pdf、fig_sens_tornado.pdf、fig_variants.pdf。
"""
import time

import numpy as np

import utils as U
from utils import LENGTH_CM, Props, R0_CM, fmt4, save_json, simulate


def run_p3(**kw):
    kw.setdefault("N", 20)
    kw.setdefault("dt", 1.0)
    kw.setdefault("n_iter", 2)
    kw.setdefault("out_every", 600.0)
    kw.setdefault("threshold", U.THRESHOLD)
    kw.setdefault("t_max", 259200.0)
    kw.setdefault("props", Props(mode="att3"))
    return simulate(**kw)


def run_p4(**kw):
    kw.setdefault("N", 20)
    kw.setdefault("dt", 2.0)
    kw.setdefault("n_iter", 2)
    kw.setdefault("out_every", 600.0)
    kw.setdefault("threshold", U.THRESHOLD)
    kw.setdefault("t_max", 259200.0)
    kw.setdefault("props", Props(mode="att4"))
    t2, R2 = U.load_att2()
    kw.setdefault("R_of_t_cm", lambda t: float(np.interp(t, t2, R2)))
    return simulate(**kw)


def main():
    res = {}
    # ---------- 1. 收敛性：问题1（N 与 dt 同时减半）----------
    t0 = time.time()
    s1_20 = simulate(t_max=1800, dt=0.25, N=20, props=Props(mode="att2"), out_every=100., n_iter=2)
    s1_40 = simulate(t_max=1800, dt=0.0625, N=40, props=Props(mode="att2"), out_every=100., n_iter=2)
    s1_80 = simulate(t_max=1800, dt=0.015625, N=80, props=Props(mode="att2"), out_every=100., n_iter=2)
    rA = np.linspace(0, 2, 21)
    rB = np.linspace(0, 2, 41)
    rC = np.linspace(0, 2, 81)
    d20_40T = d20_40C = d40_80 = 0.0
    for i in [1, 3, 6, 9, 12, 15, 18]:
        d20_40T = max(d20_40T, float(np.max(np.abs(s1_20.T[i] - np.interp(rA, rB, s1_40.T[i])))))
        d20_40C = max(d20_40C, float(np.max(np.abs(s1_20.C[i] - np.interp(rA, rB, s1_40.C[i])))))
        d40_80 = max(d40_80, float(np.max(np.abs(s1_40.T[i] - np.interp(rB, rC, s1_80.T[i])))))
        d40_80 = max(d40_80, float(np.max(np.abs(s1_40.C[i] - np.interp(rB, rC, s1_80.C[i])))))
    res["p1_conv"] = {
        "maxdiff_T_N20_N40": fmt4(d20_40T),
        "maxdiff_C_N20_N40": fmt4(d20_40C),
        "maxdiff_N40_N80": fmt4(d40_80),
        "mass_err_N20": float(f"{s1_20.mass_err:.2e}"),
        "runtime_s": round(time.time() - t0, 1),
    }
    print("P1 conv:", res["p1_conv"], flush=True)

    # ---------- 2. 问题3 网格/步长与守恒 ----------
    t0 = time.time()
    s3_base = run_p3()
    s3_dt2 = run_p3(dt=2.0)
    s3_N40 = run_p3(N=40, dt=0.5)
    base = s3_base.t_end_s
    res["p3_conv"] = {
        "t_end_base_h": fmt4(base / 3600),
        "t_end_dt2_h": fmt4(s3_dt2.t_end_s / 3600),
        "t_end_N40dt05_h": fmt4(s3_N40.t_end_s / 3600),
        "dt2_rel_dev_pct": fmt4(100 * abs(s3_dt2.t_end_s - base) / base),
        "N40_rel_dev_pct": fmt4(100 * abs(s3_N40.t_end_s - base) / base),
        "mass_err": float(f"{s3_base.mass_err:.2e}"),
        "runtime_s": round(time.time() - t0, 1),
    }
    print("P3 conv:", res["p3_conv"], flush=True)

    # ---------- 3. 参数扰动（±20%，单因素）对 t_end3 ----------
    sweep = {}
    for name, key in [("h", "h"), ("h_m", "hm"), ("k", "k_scale"),
                      ("rho_cp", "rcp_scale"), ("D0", "d_scale")]:
        def t_for(factor):
            kw = dict(props=Props(mode="att3"))
            if key == "h":
                kw["h"] = U.H_CONV * factor
            elif key == "hm":
                kw["hm"] = U.HM_CONV * factor
            else:
                kw["props"] = Props(mode="att3", **{key: factor})
            return run_p3(**kw).t_end_s
        lo = t_for(0.8)
        hi = t_for(1.2)
        sweep[name] = {"base_h": fmt4(base / 3600), "m20_h": fmt4(lo / 3600),
                       "p20_h": fmt4(hi / 3600),
                       "rel_change_pct": fmt4(max(abs(lo - base), abs(hi - base)) / base * 100)}
        print("P3", name, sweep[name], flush=True)
    res["p3_sweep"] = sweep

    # ---------- 4. 边界条件/模型变体（问题3） ----------
    s3_last = run_p3(att1_mode="lastpoint")
    s3_end = run_p3(area_end_factor=1 + R0_CM / LENGTH_CM)
    s3_latent = run_p3(latent=True)
    res["p3_variants"] = {
        "t_end_lastpoint_h": fmt4(s3_last.t_end_s / 3600),
        "t_end_endface_corr_h": fmt4(s3_end.t_end_s / 3600),
        "t_end_latent_h": fmt4(s3_latent.t_end_s / 3600),
        "rel_lastpoint_pct": fmt4(100 * (s3_last.t_end_s - base) / base),
        "rel_endface_pct": fmt4(100 * (s3_end.t_end_s - base) / base),
        "rel_latent_pct": fmt4(100 * (s3_latent.t_end_s - base) / base),
    }
    print("P3 variants:", res["p3_variants"], flush=True)

    # ---------- 5. 问题4：网格一致性、收缩收益、灵敏度 ----------
    t0 = time.time()
    s4_base = run_p4()
    s4_N40 = run_p4(N=40, dt=1.0)
    s4_fixed = run_p4(R_of_t_cm=lambda t: 2.0)
    base4 = s4_base.t_end_s
    p4 = {"N40_rel_dev_pct": fmt4(100 * abs(s4_N40.t_end_s - base4) / base4),
          "t_end_base_h": fmt4(base4 / 3600),
          "t_end_noshrink_h": fmt4(s4_fixed.t_end_s / 3600),
          "shrink_speedup_pct": fmt4(100 * (1 - base4 / s4_fixed.t_end_s)),
          "mass_err": float(f"{s4_base.mass_err:.2e}")}
    for name, key in [("h", "h"), ("h_m", "hm"), ("D0", "d_scale"),
                      ("k", "k_scale"), ("rho_cp", "rcp_scale")]:
        def t4_for(factor):
            kw = {}
            if key == "h":
                kw["h"] = U.H_CONV * factor
            elif key == "hm":
                kw["hm"] = U.HM_CONV * factor
            else:
                kw["props"] = Props(mode="att4", **{key: factor})
            return run_p4(**kw).t_end_s
        lo = t4_for(0.8)
        hi = t4_for(1.2)
        p4[name] = {"base_h": fmt4(base4 / 3600), "m20_h": fmt4(lo / 3600),
                    "p20_h": fmt4(hi / 3600),
                    "rel_change_pct": fmt4(max(abs(lo - base4), abs(hi - base4)) / base4 * 100)}
        print("P4", name, p4[name], flush=True)
    p4["runtime_s"] = round(time.time() - t0, 1)
    res["p4"] = p4

    # ---------- 6. 物性参数集一致性（附录2 vs 附录3，问题1 30min） ----------
    s30 = simulate(t_max=1800, dt=0.25, N=20, props=Props(mode="att3"), out_every=100., n_iter=2)
    res["p1_vs_p2_at1800"] = {
        "T_center_att2": fmt4(s1_20.T[-1, 0]), "T_center_att3": fmt4(s30.T[-1, 0]),
        "T_surf_att2": fmt4(s1_20.T[-1, -1]), "T_surf_att3": fmt4(s30.T[-1, -1]),
        "C_center_att2": fmt4(s1_20.C[-1, 0]), "C_center_att3": fmt4(s30.C[-1, 0]),
        "C_surf_att2": fmt4(s1_20.C[-1, -1]), "C_surf_att3": fmt4(s30.C[-1, -1]),
    }
    print("P1 vs P2 @1800:", res["p1_vs_p2_at1800"], flush=True)

    save_json(res, "sensitivity.json")
    figures(res)
    print("SENS DONE", flush=True)


def figures(res):
    import matplotlib.pyplot as plt
    import plot_utils as PU
    PU.setup()
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.6))
    axes[0].bar(["T (N20-N40)", "C (N20-N40)", "max (N40-N80)"],
                [res["p1_conv"]["maxdiff_T_N20_N40"],
                 res["p1_conv"]["maxdiff_C_N20_N40"],
                 res["p1_conv"]["maxdiff_N40_N80"]],
                width=0.45, color=["tab:blue", "tab:orange", "tab:green"])
    for k, v in zip(range(3), [res["p1_conv"]["maxdiff_T_N20_N40"],
                               res["p1_conv"]["maxdiff_C_N20_N40"],
                               res["p1_conv"]["maxdiff_N40_N80"]]):
        axes[0].text(k, v + 2e-4, f"{v:.4f}", ha="center", fontsize=8.5)
    axes[0].set_ylabel("表中值最大绝对偏差")
    axes[0].set_title("问题1 网格/步长收敛（N、dt 减半）", fontsize=10)
    axes[1].bar(["dt=2 vs dt=1", "N40 vs N20"],
                [res["p3_conv"]["dt2_rel_dev_pct"], res["p3_conv"]["N40_rel_dev_pct"]],
                width=0.4, color="tab:purple")
    for k, v in zip(range(2), [res["p3_conv"]["dt2_rel_dev_pct"],
                               res["p3_conv"]["N40_rel_dev_pct"]]):
        axes[1].text(k, v + 0.02, f"{v:.3f}%", ha="center", fontsize=8.5)
    axes[1].set_ylabel("t_end 相对偏差 / %")
    axes[1].set_title("问题3 数值精度", fontsize=10)
    fig.tight_layout()
    PU.save(fig, "fig_conv.pdf")

    # 龙卷风图（问题3 与问题4 并排）
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.8), sharey=False)
    for ax, sw, ttl in [(axes[0], res["p3_sweep"], "问题3"),
                        (axes[1], {k: v for k, v in res["p4"].items() if isinstance(v, dict)},
                         "问题4")]:
        names = list(sw.keys())
        lo = [sw[n]["base_h"] - sw[n]["m20_h"] for n in names]
        hi = [sw[n]["p20_h"] - sw[n]["base_h"] for n in names]
        order = np.argsort([max(abs(a), abs(b)) for a, b in zip(lo, hi)])
        names = [names[i] for i in order]
        lo = [lo[i] for i in order]
        hi = [hi[i] for i in order]
        y = np.arange(len(names))
        ax.barh(y - 0.18, lo, height=0.36, color="tab:blue", label="−20%")
        ax.barh(y + 0.18, hi, height=0.36, color="tab:red", label="+20%")
        ax.axvline(0, color="k", lw=0.8)
        ax.set_yticks(y, names)
        ax.set_xlabel("Δt_end / h")
        ax.set_title(f"{ttl}：±20% 参数扰动", fontsize=10)
        ax.legend(fontsize=8.5, loc="lower right")
    fig.tight_layout()
    PU.save(fig, "fig_sens_tornado.pdf")

    # 变体对比柱
    fig, ax = plt.subplots(figsize=(6.6, 3.6))
    labels = ["基准\n(P3)", "末点恒温", "端面修正", "潜热耦合", "基准\n(P4)", "P4 不收缩"]
    vals = [res["p3_conv"]["t_end_base_h"],
            res["p3_variants"]["t_end_lastpoint_h"],
            res["p3_variants"]["t_end_endface_corr_h"],
            res["p3_variants"]["t_end_latent_h"],
            res["p4"]["t_end_base_h"],
            res["p4"]["t_end_noshrink_h"]]
    colors = ["tab:gray", "tab:gray", "tab:gray", "tab:gray", "tab:purple", "tab:purple"]
    bars = ax.bar(labels, vals, color=colors, width=0.55)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.5, f"{v:.2f}", ha="center", fontsize=8.5)
    ax.set_ylabel("t_end / h")
    ax.set_title("模型变体下烘干时长对比", fontsize=10)
    fig.tight_layout()
    PU.save(fig, "fig_variants.pdf")


if __name__ == "__main__":
    main()
