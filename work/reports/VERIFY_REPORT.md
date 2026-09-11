# VERIFY_REPORT — 最终验证与验收（6verity）

日期：2026-09-11 ｜ 引擎：Typst（zh/cumcm 模板）｜ 论文：`paper/main.typ` → `paper/main.pdf`

## 结论

**PASS（可提交）**。文本门禁脚本通过、编译零错误、PDF 视觉检查通过、数值与 `reports/RESULTS_REPORT.md` / 结果 JSON 一致、2026 格式规范逐项满足。

## Step 1 文本质量门禁

命令（脚本原文件为 CRLF，已 `tr -d '\r'` 后运行）：

```bash
bash /tmp/wc_lf.sh --paper-dir paper --main paper/main.typ --sections-dir paper/sections \
  --references paper/references.typ --figures-dir figures \
  --results-file reports/RESULTS_REPORT.md --problem-analysis reports/ANALYSIS_MODELING_REPORT.md
```

结果：`PASS: writing text gate passed`，无 FAIL/WARN（早期两条“figure not referenced”警告已通过把 fig_q3_heatmap 嵌入第 7 节、fig_domain_mapping 嵌入第 8 节解决）。

## Step 2 章节与标题顺序

include 数 10 = 章节文件 10（1重述/2分析/3假设/4符号/5问题一/6问题二/7问题三/8问题四/9灵敏度/10评价），前缀顺序与标题顺序一致，均为 `= 标题` 一级标题。与 `ANALYSIS_MODELING_REPORT.md` 的四问+灵敏度结构匹配（问题四新增 8_problem4.typ，灵敏度/评价顺延为 9/10）。

## Step 3 图表匹配

`figures/` 19 个 PDF 全部被论文引用：roadmap/pipeline（第2节）、q1×3（第5节）、att1/att2+q2×3（第6节）、q3×3（第7节）、q4×4（第8节，含 domain_mapping）、conv/tornado/variants（第9节）。caption 均为中文且与图意一致；连续图之间有解释文字。修复过一处真实缺陷：`fig_q2_evolution.pdf` 原生成代码 pcolormesh 轴数据错位（mesh 被压缩至 y∈[0,2] 带外），已改写为 imshow 场图并重新生成、复核。

## Step 4 写作质量与泄露

无 TODO/占位符/示例数据字样；无承诺书残留；正文不出现工作流文件名（ANALYSIS/RESULTS 报告、.json 路径均已改写为“附录 A/第 N 节”口径；结果文件 result1–4.xlsx 为题面交付物名，保留）。列表式写法仅存在于假设与评价的编号段落（学术惯例），无 #list/#enum 滥用。

## Step 5 数值一致性

对 PDF 全文抽取比对 RESULTS_REPORT 关键量（脚本核验，29 个代表数全部命中）：1800 s 中心/表面 33.5752/36.7853、1.5116；P2 3h 49.8328/0.9831；t_end 59273 s=16.4647 h、70758 s=19.6550 h、R(t_end)=1.2107 cm、对照 39.2019 h、缩短 49.87%；灵敏度 16.7581→(±16.8/−11.1%)、D0 7.96%、P4 D0 13.45%；变体 16.4378/15.6433 h；恒温段 50.013 °C/0.04999；收敛 0.0085% 等。表1–表6 数值与题面格式（行列取向、四位小数）一致；result1–4.xlsx 与表格同源（problem2.py 重跑仅再生图，表值逐位相同，已比对）。

## Step 6 引用与模板

`paper/references.typ` 5 条真实文献（数值传热学；Incropera 6th；Crank 2nd；传热学 4th；药典 2020 四部），正文 `#super[[n]]` 标注齐全（1–5 全部被引）。模板要素保留：摘要页起页码=1（`#counter(page).update(1)`）、中文摘要+关键词、参考文献与附录不编号；按 2026 规范删除目录页；标题已替换为论文题目；字体栈改为沙箱可用的思源宋体/黑体（提交环境可回退 Times New Roman/SimSun，见 main.typ 注释）。

## Step 7 编译与 PDF 检查

`typst.compile`（python 绑定 0.15）零 error/零 warning 路径：45 页、3.39 MB（≤20 MB）。pymupdf 逐页渲染抽查（摘要页、表1/表2 页、第6/7节图文页、第8节方程页、附录页）：无豆腐块（字体缺字）□、无公式溢出、表格未跨页断裂（对表1/表5 加了 weak page break）、代码附录自动换行正常。页结构：p1 摘要｜p2–19 正文（18 页 ≤30）｜p20 参考文献｜p21–45 附录 A。

## 匿名性与规范

全文无学校/院系/姓名/队号（“大学”仅出现于出版社名“西安交通大学出版社”）；页眉页脚无身份信息；电子版从摘要页开始（承诺书/编号页按规范不入电子版，提交时由官方系统生成）。

## 修复清单（本阶段实际改动）

1. 摘要/图题中的字面方括号与"上：/下："方向描述更正；关键字→关键词。
2. `**表3` 未闭合强调符导致整节解析失败 → 修复。
3. 数学模式 `10^-3`、`10/80` 分数化、`pm/le/gt.gt/pdv/Bigl` 等非法语法 → 全部改写；`%` 全局转义并回滚 `width: NN%` 误伤。
4. 章节标签引用 `@sec-*` 渲染成“小节八、”不佳 → 改为“第 N 节”文字。
5. `fig_q2_evolution.pdf` 重生成（见 Step 3）。
6. 附录 A 改为 `raw(read(...))` 内嵌全部 8 个源文件 + 支撑材料文件列表 + 运行命令。
7. 正文删除 `utils.simulate()` 内部函数名指涉。

## 遗留风险（不阻断提交）

- 参考文献卷/期页码省略（书籍类 GB/T 7714 允许）；若赛区要求严格版次页码，可在 references.typ 补页码。
- 模板字体为思源宋体/黑体替代（沙箱无 SimSun）；视觉规范一致，但在正式环境重编译时建议改回宋体以贴合附件模板观感（一行改动）。
- Q4 质量守恒口径已在正文如实说明（点值随体形式，不以定域守恒为校验）。
