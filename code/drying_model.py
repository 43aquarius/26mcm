#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中药材烘干过程传热传质耦合模型
2026 年高教社杯全国大学生数学建模竞赛 A 题

作者：Mathematical Modeling Team
功能：求解圆柱坐标系下的一维非稳态热传导和水分扩散耦合问题
"""

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
import os

# ==================== 基础参数 ====================

# 几何参数 (SI 单位)
L = 0.25          # 药材长度 m
R0 = 0.02         # 初始半径 m

# 初始条件
T0 = 28.0         # 初始温度 °C
C0 = 2.55         # 初始水分浓度 kg/kg (干基)

# 问题 1 的恒定物性参数 (附录 2)
RHO_1 = 820.0           # 密度 kg/m³
CP_1 = 2600.0           # 比热容 J/(kg·K)
K_1 = 0.36              # 热导率 W/(m·K)
H = 25.0                # 对流换热系数 W/(m²·K)
HM = 8e-7               # 对流传质系数 m/s
LV = 2.26e6             # 水的汽化潜热 J/kg

# 网格参数
DR = 0.001              # 径向步长 0.1 cm = 0.001 m
N = int(R0 / DR)        # 网格数
DT = 1.0                # 时间步长 s

print(f"网格数 N = {N}, 径向步长 dr = {DR*100:.1f} cm, 时间步长 dt = {DT} s")

# ==================== 数据读取 ====================

def load_attachment1():
    """读取附件 1：烘房温度和水分浓度随时间变化"""
    df = pd.read_excel('/workspace/mm2glm/附件/附件1.xlsx')
    time_s = df['时间'].values
    temp_C = df['温度'].values
    conc = df['水分浓度'].values
    
    # 创建插值函数
    T_inf_interp = interp1d(time_s, temp_C, kind='linear', fill_value='extrapolate')
    C_inf_interp = interp1d(time_s, conc, kind='linear', fill_value='extrapolate')
    
    return T_inf_interp, C_inf_interp, time_s, temp_C, conc

def load_attachment2():
    """读取附件 2：药材半径随时间变化"""
    df = pd.read_excel('/workspace/mm2glm/附件/附件2.xlsx')
    time_s = df['时间'].values
    radius_cm = df['半径'].values
    
    R_interp = interp1d(time_s, radius_cm/100, kind='linear', fill_value='extrapolate')  # 转换为 m
    
    return R_interp, time_s, radius_cm

# ==================== 物性参数计算 ====================

def get_properties_problem1(C):
    """问题 1：恒定物性参数（附录 2）"""
    rho = RHO_1
    cp = CP_1
    k = K_1
    alpha = k / (rho * cp)
    D = 7e-9 * np.exp(-0.89 * C)
    return rho, cp, k, alpha, D

def get_properties_problem2(C, T_K):
    """问题 2-3：变物性参数（附录 3）"""
    rho = 650 + 128 * C
    cp = 1450 + 2736 * C / (C + 1)
    k = 0.21 + 0.38 * C / (C + 1)
    alpha = k / (rho * cp)
    # D = 2.4e-3 * exp(-0.45/C) * exp(-3850/T), T 单位 K
    D = 2.4e-3 * np.exp(-0.45 / C) * np.exp(-3850 / T_K)
    return rho, cp, k, alpha, D

def get_properties_problem4(C, T_K):
    """问题 4：考虑收缩的物性参数（附录 4）"""
    rho = 760 + 90 * C
    cp = 1850 + 2150 * C / (C + 1)
    k = 0.12 + 0.20 * C / (C + 1)
    alpha = k / (rho * cp)
    # D = 4.2e-4 * exp(-0.30/C) * exp(-3850/T), T 单位 K
    D = 4.2e-4 * np.exp(-0.30 / C) * np.exp(-3850 / T_K)
    return rho, cp, k, alpha, D

# ==================== TDMA 求解器（三对角矩阵算法）====================

def tdma_solve(a, b, c, d):
    """
    求解三对角线性方程组 Ax = d
    A 的对角线元素为 b，下对角线为 a，上对角线为 c
    
    参数:
        a: 下对角线 (n-1 个元素)
        b: 主对角线 (n 个元素)
        c: 上对角线 (n-1 个元素)
        d: 右端向量 (n 个元素)
    
    返回:
        x: 解向量
    """
    n = len(b)
    ac = np.zeros(n)
    dc = np.zeros(n)
    xc = np.zeros(n)
    
    ac[0] = 0
    dc[0] = 0
    
    for i in range(1, n):
        m = 1.0 / (b[i-1] - ac[i-1] * a[i-1])
        ac[i] = c[i-1] * m
        dc[i] = (d[i-1] - dc[i-1] * a[i-1]) * m
    
    xc[n-1] = (d[n-1] - dc[n-1] * a[n-1]) / (b[n-1] - a[n-1] * ac[n-1])
    
    for i in range(n-2, -1, -1):
        xc[i] = dc[i] - ac[i] * xc[i+1]
    
    return xc

# ==================== 问题 1 求解器 ====================

def solve_problem1():
    """
    问题 1：预热平衡阶段 (0-1800s)
    物性参数恒定，烘房条件时变
    """
    print("\n" + "="*60)
    print("问题 1：预热平衡阶段求解")
    print("="*60)
    
    # 加载烘房条件
    T_inf_interp, C_inf_interp, _, _, _ = load_attachment1()
    
    # 初始化场变量
    n_nodes = N + 1  # 包括中心点和表面
    T = np.ones(n_nodes) * T0  # 温度场 °C
    C = np.ones(n_nodes) * C0  # 水分场 kg/kg
    
    # 结果存储
    r_positions = np.arange(0, R0 + DR, DR)  # 0, 0.001, 0.002, ..., 0.02 m
    output_times = [100, 300, 600, 900, 1200, 1500, 1800]  # s
    output_positions_cm = [0, 0.5, 1, 1.5, 2]  # cm
    
    # 完整结果存储
    T_full = []
    C_full = []
    time_full = []
    
    # 时间推进
    t = 0
    print(f"开始时间推进，总时间 1800s...")
    
    while t <= 1800:  # 改为 <= 以包含 1800s
        # 当前烘房条件
        T_inf = T_inf_interp(t)
        C_inf = C_inf_interp(t)
        
        # 获取物性参数（使用平均水分浓度）
        C_avg = np.mean(C)
        rho, cp, k, alpha, D = get_properties_problem1(C_avg)
        
        beta_t = alpha * DT / (DR ** 2)
        beta_c = D * DT / (DR ** 2)
        
        # ===== 求解温度场 =====
        # 组装三对角矩阵
        a_t = np.zeros(n_nodes)
        b_t = np.zeros(n_nodes)
        c_t = np.zeros(n_nodes)
        d_t = np.zeros(n_nodes)
        
        # 中心节点 (i=0)
        b_t[0] = 1 + 2 * beta_t
        c_t[0] = -2 * beta_t
        d_t[0] = T[0]
        
        # 内部节点 (i=1 to N-1)
        for i in range(1, N):
            r_i = i * DR
            coef_left = beta_t * (1 - DR / (2 * r_i))
            coef_right = beta_t * (1 + DR / (2 * r_i))
            a_t[i] = -coef_left
            b_t[i] = 1 + 2 * beta_t
            c_t[i] = -coef_right
            d_t[i] = T[i]
        
        # 表面节点 (i=N) - 第三类边界条件
        # h*(T_inf - T_N) = -k*(T_N - T_{N-1})/DR
        # 整理得：T_N = (k*T_{N-1} + h*DR*T_inf) / (k + h*DR)
        # 在隐式格式中：T_N^{n+1} = (k*T_{N-1}^{n+1} + h*DR*T_inf) / (k + h*DR)
        # 代入方程：(1 + 2*beta_t)*T_N - 2*beta_t*T_{N-1} = T_N^n (近似)
        # 更精确的处理：将边界条件直接作为代数方程
        Bi = H * DR / k
        a_t[N] = -Bi
        b_t[N] = 1 + Bi
        d_t[N] = Bi * T_inf
        
        # 求解
        T_new = tdma_solve(a_t, b_t, c_t, d_t)
        T = T_new
        
        # ===== 求解水分场 =====
        # 组装三对角矩阵
        a_c = np.zeros(n_nodes)
        b_c = np.zeros(n_nodes)
        c_c = np.zeros(n_nodes)
        d_c = np.zeros(n_nodes)
        
        # 中心节点 (i=0)
        b_c[0] = 1 + 2 * beta_c
        c_c[0] = -2 * beta_c
        d_c[0] = C[0]
        
        # 内部节点 (i=1 to N-1)
        for i in range(1, N):
            r_i = i * DR
            coef_left = beta_c * (1 - DR / (2 * r_i))
            coef_right = beta_c * (1 + DR / (2 * r_i))
            a_c[i] = -coef_left
            b_c[i] = 1 + 2 * beta_c
            c_c[i] = -coef_right
            d_c[i] = C[i]
        
        # 表面节点 (i=N) - 第三类边界条件
        # -D*(C_N - C_{N-1})/DR = hm*(C_N - C_inf)
        # 整理得：C_N = (D*C_{N-1} + hm*DR*C_inf) / (D + hm*DR)
        Bi_m = HM * DR / D
        a_c[N] = -Bi_m
        b_c[N] = 1 + Bi_m
        d_c[N] = Bi_m * C_inf
        
        # 求解
        C_new = tdma_solve(a_c, b_c, c_c, d_c)
        C = C_new
        
        # 保存完整结果
        if int(t) % 1 == 0:  # 每秒保存
            T_full.append(T.copy())
            C_full.append(C.copy())
            time_full.append(t)
        
        t += DT
    
    print(f"时间推进完成，共 {len(time_full)} 个时间步")
    
    # ===== 输出表 1 和表 2 =====
    print("\n生成表 1：30 分钟内药材的温度...")
    table1_data = {'时间/s': output_times}
    for pos_cm in output_positions_cm:
        pos_idx = int(pos_cm / 0.1)  # 0.1cm 间隔
        if pos_idx >= n_nodes:
            pos_idx = n_nodes - 1
        temps = [T_full[t][pos_idx] for t in output_times]
        table1_data[f'{pos_cm}'] = temps
    
    table1_df = pd.DataFrame(table1_data)
    print(table1_df.to_string(index=False))
    
    print("\n生成表 2：30 分钟内药材的水分浓度...")
    table2_data = {'时间/s': output_times}
    for pos_cm in output_positions_cm:
        pos_idx = int(pos_cm / 0.1)
        if pos_idx >= n_nodes:
            pos_idx = n_nodes - 1
        concs = [C_full[t][pos_idx] for t in output_times]
        table2_data[f'{pos_cm}'] = concs
    
    table2_df = pd.DataFrame(table2_data)
    print(table2_df.to_string(index=False))
    
    # ===== 生成 result1.xlsx =====
    print("\n生成 result1.xlsx...")
    
    # 完整结果的时间点 (1~1800s)
    full_times = list(range(1, 1801))
    # 完整结果的位置 (0~2cm, 0.1cm 间隔)
    full_positions = [i * 0.1 for i in range(21)]
    
    # 温度工作表
    T_result = pd.DataFrame(index=full_times, columns=full_positions)
    C_result = pd.DataFrame(index=full_times, columns=full_positions)
    
    for t_idx, t in enumerate(full_times):
        if t_idx < len(T_full):
            for pos_idx, pos in enumerate(full_positions):
                grid_idx = int(pos / 0.1)
                if grid_idx < len(T_full[t_idx]):
                    T_result.loc[t, pos] = round(T_full[t_idx][grid_idx], 4)
                    C_result.loc[t, pos] = round(C_full[t_idx][grid_idx], 4)
    
    # 添加表头
    T_result.index.name = '时间\\到药材中心的距离'
    C_result.index.name = '时间\\到药材中心的距离'
    
    with pd.ExcelWriter('/workspace/results/result1.xlsx') as writer:
        T_result.to_excel(writer, sheet_name='温度')
        C_result.to_excel(writer, sheet_name='水分浓度')
    
    print("result1.xlsx 生成完成!")
    
    return T, C, time_full, T_full, C_full

# ==================== 主程序 ====================

if __name__ == "__main__":
    # 确保输出目录存在
    os.makedirs('/workspace/results', exist_ok=True)
    os.makedirs('/workspace/figures', exist_ok=True)
    
    # 运行问题 1
    T_final, C_final, time_full, T_full, C_full = solve_problem1()
    
    print("\n" + "="*60)
    print("问题 1 求解完成!")
    print("="*60)
    print(f"最终中心温度：{T_final[0]:.4f} °C")
    print(f"最终表面温度：{T_final[-1]:.4f} °C")
    print(f"最终中心水分：{C_final[0]:.4f} kg/kg")
    print(f"最终表面水分：{C_final[-1]:.4f} kg/kg")
