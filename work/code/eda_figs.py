"""附件数据理解图：附件1 风温/风湿；附件2 半径收缩。"""
import numpy as np

import utils as U


def main():
    import matplotlib.pyplot as plt
    import plot_utils as PU
    PU.setup()
    t, Ta, Ca = U.load_att1()
    fig, ax1 = plt.subplots(figsize=(6.0, 3.6))
    ax1.plot(t / 60, Ta, label="烘房温度", color="tab:red")
    ax1.set_xlabel("时间 t / min")
    ax1.set_ylabel("风温 / °C", color="tab:red")
    ax1.tick_params(axis="y", labelcolor="tab:red")
    ax2 = ax1.twinx()
    ax2.plot(t / 60, Ca, label="烘房水分浓度", color="tab:blue")
    ax2.set_ylabel("风房水分浓度 / (kg·kg$^{-1}$)", color="tab:blue")
    ax2.tick_params(axis="y", labelcolor="tab:blue")
    ax1.axvline(t[-1] / 60, color="gray", ls=":", lw=1)
    ax1.text(t[-1] / 60 - 35, 46.5, "附件1 数据末端\n(14400 s)", fontsize=8)
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="lower right", fontsize=8.5)
    fig.tight_layout()
    PU.save(fig, "fig_att1_air.pdf")

    t2, R = U.load_att2()
    fig, ax = plt.subplots(figsize=(6.0, 3.4))
    ax.plot(t2 / 3600, R, color="tab:purple")
    ax.set_xlabel("时间 t / h")
    ax.set_ylabel("药材半径 R(t) / cm")
    ax.annotate(f"收缩 {100*(2-R[-1])/2:.1f}%", xy=(t2[-1] / 3600, R[-1]),
                xytext=(30, 1.45), fontsize=9,
                arrowprops=dict(arrowstyle="->", lw=0.8))
    ax.annotate("t=67 h 后稳定 1.198 cm", xy=(67, 1.198), xytext=(12, 1.32),
                fontsize=9, arrowprops=dict(arrowstyle="->", lw=0.8))
    fig.tight_layout()
    PU.save(fig, "fig_att2_radius.pdf")
    print("EDA figures done")


if __name__ == "__main__":
    main()
