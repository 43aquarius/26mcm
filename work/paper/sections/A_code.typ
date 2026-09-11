本附录列出全部可运行源代码与支撑材料。代码位于 `code/` 目录，运行环境为 Python 3（依赖 numpy、scipy、matplotlib、openpyxl），从项目根目录依次执行：

```
python3 code/problem1.py   # 问题一：表1、表2、result1.xlsx
python3 code/problem2.py   # 问题二：表3、表4、result2.xlsx
python3 code/problem3.py   # 问题三：表5、result3.xlsx、判停时长
python3 code/problem4.py   # 问题四：表6、result4.xlsx、收缩判停
python3 code/sensitivity.py  # 收敛性、±20%参数扫描与模型变体
```

*支撑材料文件列表：* `code/utils.py`（公共求解器）、`code/problem1.py`–`code/problem4.py`（各子问题驱动）、`code/sensitivity.py`（灵敏度分析）、`code/plot_utils.py` 与 `code/eda_figs.py`、`code/drawio_render.py`（绘图辅助）、`results/result1.xlsx`–`results/result4.xlsx`（题面要求的完整结果）、`results/problem1.json`–`results/problem4.json` 与 `results/sensitivity.json`（表值与校验量）、`figures/`（论文用图 PDF）。

#heading(numbering: none, outlined: false)[code/utils.py（公共求解器）]
#raw(read("../../code/utils.py"), lang: "python")
#heading(numbering: none, outlined: false)[code/problem1.py]
#raw(read("../../code/problem1.py"), lang: "python")
#heading(numbering: none, outlined: false)[code/problem2.py]
#raw(read("../../code/problem2.py"), lang: "python")
#heading(numbering: none, outlined: false)[code/problem3.py]
#raw(read("../../code/problem3.py"), lang: "python")
#heading(numbering: none, outlined: false)[code/problem4.py]
#raw(read("../../code/problem4.py"), lang: "python")
#heading(numbering: none, outlined: false)[code/sensitivity.py]
#raw(read("../../code/sensitivity.py"), lang: "python")
