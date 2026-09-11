# 方案

依据 `skills/1start-mathmodel` 启动：对 2026 年高教社杯全国大学生数学建模竞赛 **A 题（药材的烘干问题）** 执行完整 skills 工作流，最终产出符合 skills 要求的完整论文。

## 用户偏好

- 排版引擎：<Typst>（用户初选 LaTeX；沙箱网络仅放通 GitHub/PyPI，apt 源、CTAN、TeX Live 镜像均不可达，无法安装 xelatex。经检查 skills 的 `5writing` 对全部 14 个中文模板提供 Typst 等价模板，故按 skills 的“模板族 + Typst 引擎”路线执行，使用 `zh/cumcm` 模板，`typst compile`（经 PyPI `typst` 0.15.0 的编译接口）+ 思源黑体/宋体。此决定记录为环境约束下的等价方案。）
- 竞赛类型：国赛（CUMCM 2026，A 题）
- 论文语言：中文
- 子问题数量：已知 4 个（问题 1～4），章节按 4 个问题扩展

## workflow

| step | skills | 产物 |
| --- | --- | --- |
| 1. 赛题分析与建模设计 | `2analysis-modeling` | `reports/ANALYSIS_MODELING_REPORT.md` |
| 2. 编程实现和图表生成 | `3coding-visual` | `code/`、`results/`、`reports/RESULTS_REPORT.md`、`figures/*.pdf`、result1~4.xlsx |
| 3. 流程与架构图绘制 | `4drawio` | `figures/fig_*.drawio + .pdf`、`reports/DRAWIO_REPORT.md` |
| 4. 竞赛论文撰写 | `5writing` | `paper/`（zh/cumcm 模板，含摘要、正文 10 节、参考文献、附录） |
| 5. 验证和验收 | `6verity` | `reports/VERIFY_REPORT.md` + 最终 PDF |

## 建模方向（供各阶段执行）

- 机理/动力学类题型：圆柱药材内部**热—质耦合扩散**的一维径向偏微分方程初边值问题。
  - 能量方程：ρ(C)·cp(C)·∂T/∂t = (1/r)·∂/∂r( k(C)·r·∂T/∂r )，r∈(0,R)
  - 水分方程：∂C/∂t = (1/r)·∂/∂r( D(C,T)·r·∂C/∂r )（干基浓度，固相骨架不动）
  - 边界：r=0 对称 ∂T/∂r=∂C/∂r=0；r=R 对流换热 −k∂T/∂r = h(T−T_a(t))、对流传质 −D∂C/∂r = h_m(C−C_a(t))
  - 初值：T(r,0)=28°C，C(r,0)=2.55 kg/kg
- 问题 1：物性取附录 2 常数 + D=7e-9·exp(−0.89/C)；风温/风湿取附件 1（0–14400 s 每 60 s，线性插值）；输出 0–1800 s。
- 问题 2：物性统一改用附录 3 经验公式（ρ=650+128C 等）；烘房条件：预热平衡段（附件 1，至 14400 s）→ 恒温干燥段（附件 1 末端稳定值 T≈50 °C、C_a≈0.05 kg/kg 恒定）；论文表给 0–3 h。
- 问题 3：同问题 2 模型外推至全时段，判定 max_r C(r,t)<0.15 kg/kg 的最早时刻为烘干时长；每 60 s 输出。
- 问题 4：半径 R(t) 由附件 2 给出（2→1.198 cm，3 天内收缩），采用随体坐标 ξ=r/R(t) 的动边界差分格式；物性用附录 4 公式；同样以 C<0.15 判停。
- 数值方法：节点控制体有限差分（柱坐标面积加权、界面调和平均导热/扩散系数），Crank–Nicolson + 物性冻结定点迭代；网格加密（dr、dt 减半）做收敛性校验；总水量守恒校验。
- 灵敏度：h、h_m、k、ρcp 与 D 前置系数 ±20% 扰动对 t_end 的影响（龙卷风图）；端面对流面积修正、恒温取值方式、问题 2 附录 2/附录 3 参数差异对比。

## 风险控制

- 表 1–表 6 与 result1–4.xlsx 数值必须来自同一次计算输出，统一四位小数口径。
- D(C) 在 C→0 时奇异 → 数值下限截断 max(D,1e-14)。
- 附件 2 半径仅到 259200 s（72 h）→ 超出部分取常值 1.198 并在论文注明。
- 论文遵守 `format2026.doc`：A4、四边 ≥2.5cm、首页摘要、无目录、正文 ≤30 页、附录含全部代码与支撑材料清单、不出现身份信息。

## 预期产物

- `paper/main.typ` + `paper/sections/*` + 编译 PDF（≈20–26 页）
- `results/result1.xlsx … result4.xlsx`（按附件 3 模板）
- `results/tables_problem*.json`、`figures/*.pdf`（数据图 + 非数据图）
- `reports/ANALYSIS_MODELING_REPORT.md`、`RESULTS_REPORT.md`、`DRAWIO_REPORT.md`、`VERIFY_REPORT.md`
