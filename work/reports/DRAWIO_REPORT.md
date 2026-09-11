# DrawIO 图示生成报告

## 图示清单

| 文件 | 类型 | 来源依据 | 用途 | 状态 |
| --- | --- | --- | --- | --- |
| figures/fig_roadmap.drawio / .pdf | 技术路线图 | ANALYSIS_MODELING_REPORT.md 总体路线 | 问题分析/总体思路章节 | 已导出 |
| figures/fig_pipeline.drawio / .pdf | 数据-求解处理流程图 | ANALYSIS_MODELING_REPORT.md §5 数值方法 | 数据预处理与数值方法节 | 已导出 |
| figures/fig_domain_mapping.drawio / .pdf | 模型结构图（动边界坐标变换示意） | ANALYSIS_MODELING_REPORT.md §4 问题4 模型 | 问题4 建模节 | 已导出 |

## 未生成图示及原因

- `fig_flow_q1..q4`（逐子问题流程图）：四个子问题共用同一 PDE/差分框架，仅物性参数集、边界调度与判停条件不同，已在技术路线图（问题分叉区）与处理流程图中合并表达；单独画四张近似流程图无信息增量，遵循“图示服务论证”不凑数量。
- 问题4 收缩率等带数值图示属于数据图（fig_q4_shrink.pdf 等），由 3coding-visual 提供，不在本阶段重复。

## 导出与自检记录

- 沙箱内无 `drawio`/`draw.io` CLI（且 apt 源不可达，无法安装 electron 版）。按 skills 规则保留 `.drawio` 源文件，并用 `code/drawio_render.py` 按同一坐标布局把每张图等价导出为同名 PDF（矢量、中文用思源黑体）。
- 建议正式导出命令（本机装有 drawio-desktop 时）：
  `drawio --export --format pdf --crop --output figures/fig_roadmap.pdf figures/fig_roadmap.drawio`（其余同理）。
- 自检：三个 .drawio 均为合法 XML（vertex/edge 计数正常）；三张 PDF 非空、单页、无重叠节点；图中文字为中文且与论文语言一致；未绘制任何统计图/数据图；灰度下靠位置与线型可区分。
- 修复记录：domain_mapping 初版同心圆内嵌标签重叠、`∂T/ξ` 排版笔误、下标 ₁₂ 缺字形，均已修正（标签移到圆外、补 ∂、改用 t1/t2）。

## 给论文阶段的嵌入建议

- `fig_roadmap` → “问题分析/总体建模思路”节，caption 建议：技术路线图。
- `fig_pipeline` → “数据理解与数值求解方案”节，caption 建议：数据处理与数值求解流程。
- `fig_domain_mapping` → “问题四：考虑尺寸收缩的动边界模型”节，caption 建议：随体坐标变换与动边界示意。
