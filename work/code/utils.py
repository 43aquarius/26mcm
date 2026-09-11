"""公共工具：附件读取、物性函数、一维径向热-质耦合有限体积求解器、输出工具。

对应 reports/ANALYSIS_MODELING_REPORT.md 第 4-6 节的实现规格。
模型：圆柱药材，一维径向（问题4采用随体坐标动边界），Crank-Nicolson 控制体有限体积法，
非线性物性按场冻结并做定点迭代。
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, field

import numpy as np
import openpyxl
from scipy.linalg import solve_banded

# ---------------------------------------------------------------- 路径与常量

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ATT_DIR = os.path.join(PROJECT_ROOT, "附件")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
FIG_DIR = os.path.join(PROJECT_ROOT, "figures")
OUT_DIR = os.path.join(PROJECT_ROOT, "code", "outputs")
for _d in (RESULTS_DIR, FIG_DIR, OUT_DIR):
    os.makedirs(_d, exist_ok=True)

R0_CM = 2.0
R0_M = 0.02
LENGTH_CM = 25.0
T_INIT_C = 28.0
C_INIT = 2.55
D_FLOOR = 1.0e-14
C_FLOOR = 1.0e-6
THRESHOLD = 0.15
LATENT_HEAT = 2.45e6  # J/kg，水汽化潜热（仅灵敏度改进情形使用）
RHO_W = 1.0  # kg water / kg dry basis 与通量乘子（灵敏度情形，量级估计）

# ---------------------------------------------------------------- 附件数据


def load_att1():
    """附件1：t(s), 烘房温度(C), 烘房水分浓度(kg/kg)。"""
    wb = openpyxl.load_workbook(os.path.join(ATT_DIR, "附件1.xlsx"), read_only=True)
    ws = wb["Sheet1"]
    rows = np.array(list(ws.iter_rows(values_only=True))[1:], dtype=float)
    wb.close()
    t, Ta, Ca = rows[:, 0], rows[:, 1], rows[:, 2]
    assert np.allclose(np.diff(t), 60.0), "附件1时间步长应为60 s"
    return t, Ta, Ca


def load_att2():
    """附件2：t(s), 药材半径(cm)。"""
    wb = openpyxl.load_workbook(os.path.join(ATT_DIR, "附件2.xlsx"), read_only=True)
    ws = wb["Sheet1"]
    rows = np.array(list(ws.iter_rows(values_only=True))[1:], dtype=float)
    wb.close()
    t, R = rows[:, 0], rows[:, 1]
    assert np.all(np.diff(R) <= 1e-12), "附件2半径应单调不增"
    return t, R


_att_cache = {}


def att1_tail_mean():
    """附件1末30min均值：恒温干燥段边界条件。"""
    if "att1" not in _att_cache:
        _att_cache["att1"] = load_att1()
    t, Ta, Ca = _att_cache["att1"]
    mask = t >= t[-1] - 1800.0
    return float(np.mean(Ta[mask])), float(np.mean(Ca[mask]))


def air_schedule(t_query, mode="tail30"):
    """烘房边界条件调度。

    预热平衡段：附件1 线性插值（0-14400 s）；
    恒温干燥段（t>14400 s）：mode=tail30 取末30min均值；mode=lastpoint 取末点值。
    返回 (T_air_C, C_air) 两个数组。
    """
    if "att1" not in _att_cache:
        _att_cache["att1"] = load_att1()
    t, Ta, Ca = _att_cache["att1"]
    if mode == "lastpoint":
        Ta_inf, Ca_inf = float(Ta[-1]), float(Ca[-1])
    else:
        Ta_inf, Ca_inf = att1_tail_mean()
    tq = np.atleast_1d(np.asarray(t_query, dtype=float))
    Ta_i = np.interp(tq, t, Ta, left=Ta[0], right=Ta_inf)
    Ca_i = np.interp(tq, t, Ca, left=Ca[0], right=Ca_inf)
    return Ta_i, Ca_i


def radius_schedule_cm(t_query):
    """附件2：半径 R(cm)，超出数据后取末值。"""
    if "att2" not in _att_cache:
        _att_cache["att2"] = load_att2()
    t, R = _att_cache["att2"]
    return np.interp(t, t, R)


# ---------------------------------------------------------------- 物性函数


@dataclass
class Props:
    """物性参数集：att2=附录2（问题1），att3=附录3（问题2/3），att4=附录4（问题4）。"""

    mode: str = "att3"
    d_scale: float = 1.0  # D 前置系数乘子（灵敏度用）
    k_scale: float = 1.0
    rcp_scale: float = 1.0

    def rho(self, C):
        C = np.maximum(C, 0.0)
        if self.mode == "att2":
            return np.full_like(C, 820.0) + 0.0 * C
        if self.mode == "att4":
            return 760.0 + 90.0 * C
        return 650.0 + 128.0 * C

    def cp(self, C):
        C = np.maximum(C, 0.0)
        if self.mode == "att2":
            return np.full_like(C, 2600.0) + 0.0 * C
        if self.mode == "att4":
            return 1850.0 + 2150.0 * C / (C + 1.0)
        return 1450.0 + 2736.0 * C / (C + 1.0)

    def k(self, C):
        C = np.maximum(C, 0.0)
        if self.mode == "att2":
            return np.full_like(C, 0.36) + 0.0 * C
        if self.mode == "att4":
            k = 0.12 + 0.20 * C / (C + 1.0)
        else:
            k = 0.21 + 0.38 * C / (C + 1.0)
        return k * self.k_scale

    def rcp(self, C):
        return self.rho(C) * self.cp(C) * self.rcp_scale

    def D(self, C, T_C):
        """水分浓度扩散系数 m2/s。公式中的 T 以 K 计。"""
        Cc = np.clip(C, C_FLOOR, None)
        TK = np.maximum(T_C + 273.15, 200.0)
        if self.mode == "att2":
            D = 7.0e-9 * np.exp(-0.89 / Cc)
        elif self.mode == "att4":
            D = 4.2e-4 * np.exp(-0.30 * Cc) * np.exp(-3850.0 / TK)
        else:
            D = 2.4e-3 * np.exp(-0.45 * Cc) * np.exp(-3850.0 / TK)
        return np.maximum(D * self.d_scale, D_FLOOR)


H_CONV = 25.0
HM_CONV = 8.0e-7

# ---------------------------------------------------------------- 核心求解器


def _harm(a, b):
    return 2.0 * a * b / np.maximum(a + b, 1e-300)


@dataclass
class SimOut:
    tout: np.ndarray = None
    r_cm: np.ndarray = None      # 静态域: (N+1,)；动边界: (nt, N+1)
    T: np.ndarray = None
    C: np.ndarray = None
    R_cm: np.ndarray = None
    t_end_s: float = None
    mass_err: float = None
    stats: dict = field(default_factory=dict)


def simulate(
    t_max: float,
    dt: float,
    N: int = 20,
    props: Props | None = None,
    h: float = H_CONV,
    hm: float = HM_CONV,
    R_of_t_cm=None,          # callable t->R(cm)；None 表示恒为 2.0 cm
    threshold: float | None = None,
    out_every: float = 1.0,
    n_iter: int = 2,
    area_end_factor: float = 1.0,
    latent: bool = False,     # 表面蒸发潜热汇（灵敏度改进情形）
    att1_mode: str = "tail30",
    T0: float = T_INIT_C,
    C0: float = C_INIT,
    max_out_steps: int | None = None,
) -> SimOut:
    """一维径向热-质耦合控制体有限体积 + Crank-Nicolson 求解。

    节点 j=0..N 对应 r = xi_j·R(t)，xi_j = j/N；界面传导率
    g_{j+1/2} = 2π·Dface·(j+1/2)（随体坐标下与 R 无关），
    表面 g_R = h·2πR（热）/ h_m·2πR（质）。
    threshold：max_j C_j < threshold 时记录 t_end 并停止。
    """
    props = props or Props()
    dxi = 1.0 / N
    jmid = np.arange(N) + 0.5
    geo_face = 2.0 * math.pi * jmid
    jnode = np.arange(N + 1)
    xlo = np.maximum(jnode * dxi - 0.5 * dxi, 0.0)
    xhi = np.minimum(jnode * dxi + 0.5 * dxi, 1.0)
    V_norm = math.pi * (xhi**2 - xlo**2)

    Ta_a0, Ca_a0 = air_schedule(np.array([0.0]), att1_mode)
    T = np.full(N + 1, T0)
    C = np.full(N + 1, float(C0))

    def Rm(tt):
        return R0_M if R_of_t_cm is None else float(R_of_t_cm(tt)) * 1.0e-2

    n_steps = int(round(t_max / dt))
    out_stride = max(1, int(round(out_every / dt)))
    if max_out_steps is not None:
        n_steps = min(n_steps, max_out_steps * out_stride)

    tout, Ts, Cs, Rs = [], [], [], []
    t = 0.0
    prev_max = None
    t_end_exact = None
    W0 = float(np.sum(C * V_norm)) * Rm(t) ** 2
    flux_int = 0.0

    def flux_and_geo(field, gf, amb, g_amb):
        """给定界面传导率 gf（已含 2π 几何因子）与表面换热传导率，返回 (gf, 通量向量)。"""
        F = np.zeros(N + 1)
        F[:-1] += gf * (field[1:] - field[:-1])
        F[1:] -= gf * (field[1:] - field[:-1])
        F[N] += g_amb * (amb - field[N])
        return gf, F

    for n in range(n_steps + 1):
        if n % out_stride == 0:
            tout.append(t)
            Ts.append(T.copy())
            Cs.append(C.copy())
            Rs.append(Rm(t) * 100.0)
        if threshold is not None and t > 0:
            mc = float(np.max(C))
            if mc < threshold:
                # 事件时刻线性细化；补齐一条输出记录
                prev = prev_max if prev_max is not None else mc
                if prev >= threshold:
                    frac = (prev - threshold) / max(prev - mc, 1e-300)
                    t_end_exact = t - dt + frac * dt
                else:
                    t_end_exact = t
                if len(tout) == 0 or tout[-1] != t:
                    tout.append(t); Ts.append(T.copy()); Cs.append(C.copy())
                    Rs.append(Rm(t) * 100.0)
                t = t_end_exact
                break
        if n == n_steps:
            break
        t1 = t + dt
        R_new = Rm(t1)
        Ta_mid, Ca_mid = air_schedule(np.array([0.5 * (t + t1)]), att1_mode)
        Ta_a, Ca_a = float(Ta_mid[0]), float(Ca_mid[0])

        T_old, C_old = T.copy(), C.copy()
        Vj = V_norm * R_new**2
        for it in range(n_iter):
            # Picard：半步中点物性系数，对称用于新旧两端（守恒、含线性化极限）
            Tm = 0.5 * (T_old + T)
            Cm = 0.5 * (C_old + C)
            rc = props.rcp(Cm)
            gT = geo_face * _harm(props.k(Cm)[:-1], props.k(Cm)[1:])
            gC = geo_face * _harm(props.D(Cm, Tm)[:-1], props.D(Cm, Tm)[1:])
            gT_R = h * 2.0 * math.pi * R_new * area_end_factor
            gC_R = hm * 2.0 * math.pi * R_new * area_end_factor
            # 右端：旧时刻场 + 中点系数算的通量（两端同系数，保证离散守恒与线性极限精确）
            fT = np.zeros(N + 1)
            fT[:-1] += gT * (T_old[1:] - T_old[:-1])
            fT[1:] -= gT * (T_old[1:] - T_old[:-1])
            fT[N] += gT_R * (Ta_a - T_old[N])
            fC = np.zeros(N + 1)
            fC[:-1] += gC * (C_old[1:] - C_old[:-1])
            fC[1:] -= gC * (C_old[1:] - C_old[:-1])
            fC[N] += gC_R * (Ca_a - C_old[N])
            rhsT = Vj * rc / dt * T_old + 0.5 * fT
            rhsC = Vj / dt * C_old + 0.5 * fC
            abT = np.zeros((3, N + 1))
            abT[1] = Vj * rc / dt + 0.5 * np.concatenate(([gT[0]], gT[:-1] + gT[1:], [gT[-1] + gT_R]))
            abT[0, 1:] = -0.5 * gT
            abT[2, :-1] = -0.5 * gT
            rhs = rhsT.copy()
            rhs[N] += 0.5 * gT_R * Ta_a
            if latent:
                rhs[N] -= LATENT_HEAT * (hm * (C[N] - Ca_a)) * 2.0 * math.pi * R_new * area_end_factor * 0.5
            T_new = solve_banded((1, 1), abT, rhs)
            abC = np.zeros((3, N + 1))
            abC[1] = Vj / dt + 0.5 * np.concatenate(([gC[0]], gC[:-1] + gC[1:], [gC[-1] + gC_R]))
            abC[0, 1:] = -0.5 * gC
            abC[2, :-1] = -0.5 * gC
            rhs = rhsC.copy()
            rhs[N] += 0.5 * gC_R * Ca_a
            C_new = solve_banded((1, 1), abC, rhs)
            C_new = np.maximum(C_new, 0.0)
            # Picard 松弛，增强强非线性下的稳定
            om = 1.0 if it == n_iter - 1 else 0.7
            T = om * T_new + (1 - om) * T
            C = om * C_new + (1 - om) * C

        flux_int += dt * hm * 2.0 * math.pi * R_new * area_end_factor * (Ca_a - C[N])
        W = float(np.sum(C * V_norm)) * R_new**2
        prev_max = float(np.max(C))
        t = t1

    mass_err = abs((W0 - W) + flux_int) / max(abs(W0 - W), 1e-12)
    tout = np.array(tout)
    r_cm = np.arange(N + 1) / N * R0_CM
    if R_of_t_cm is not None:
        r_cm = (np.arange(N + 1) / N) * np.array(Rs)[:, None]
    out = SimOut(
        tout=tout,
        r_cm=r_cm,
        T=np.array(Ts),
        C=np.array(Cs),
        R_cm=np.array(Rs),
        mass_err=mass_err,
    )
    if threshold is not None:
        if t_end_exact is not None:
            out.t_end_s = float(t_end_exact)
        else:
            out.t_end_s = float("nan")
    out.stats.update(N=N, dt=dt, n_out=len(tout), t_end=out.t_end_s,
                     mass_err=mass_err, latent=latent,
                     area_end_factor=area_end_factor,
                     d_scale=props.d_scale, k_scale=props.k_scale,
                     rcp_scale=props.rcp_scale, h=h, hm=hm,
                     att1_mode=att1_mode)
    return out


# ---------------------------------------------------------------- 输出工具


def fmt4(x):
    return round(float(x), 4)


def save_json(obj, name):
    with open(os.path.join(RESULTS_DIR, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def load_json(name):
    with open(os.path.join(RESULTS_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)
