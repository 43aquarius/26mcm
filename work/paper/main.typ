#let body-font = ("Source Han Serif CN")
#let song-font = ("Source Han Serif CN")
#let hei-font = ("Source Han Sans CN")
#let kai-font = ("Source Han Serif CN")

#let cn-numbering(..nums) = {
  let ns = nums.pos()
  if ns.len() == 1 {
    numbering("一、", ns.at(0))
  } else if ns.len() == 2 {
    numbering("1.1", ns.at(0), ns.at(1))
  } else {
    numbering("1.1.1", ns.at(0), ns.at(1), ns.at(2))
  }
}

#set document(title: "药材烘干过程的温度与水分浓度场演化模型", author: ())
#set page(
  paper: "a4",
  margin: (top: 2.5cm, bottom: 2.5cm, left: 2.5cm, right: 2.5cm),
  numbering: "1",
)
#set text(font: body-font, size: 12.05pt, lang: "zh")
#set par(
  first-line-indent: (amount: 2em, all: true),
  justify: true,
  leading: 0.72em,
  spacing: 0.35em,
)
#set heading(numbering: cn-numbering)
#set math.equation(numbering: "(1)")
#set enum(numbering: "1.")
#set table(inset: 0.45em)
#show heading.where(level: 1): set align(center)
#show heading.where(level: 1): set text(size: 17.3pt, weight: "bold")
#show heading.where(level: 1): set block(above: 1.25em, below: 0.82em)
#show heading.where(level: 2): set text(size: 14.45pt, weight: "bold")
#show heading.where(level: 2): set block(above: 1.15em, below: 0.55em)
#show heading.where(level: 3): set text(size: 12.05pt, weight: "bold")
#show heading.where(level: 3): set block(above: 1.15em, below: 0.55em)
#show figure.caption: it => text(size: 12pt, weight: "bold")[#it]
#show raw: set text(size: 10pt, font: ("DejaVu Sans Mono", "Source Han Sans CN"))
#show raw.where(block: true): set block(
  fill: luma(97%),
  stroke: 0.8pt + luma(70%),
  inset: 0.7em,
  above: 0.7em,
  below: 0.7em,
)

#let song = (body) => text(font: song-font, body)
#let hei = (body) => text(font: hei-font, weight: "bold", body)
#let kai = (body) => text(font: kai-font, body)
#let paper-title(body) = {
  align(center)[#text(size: 17.3pt, weight: "bold")[#body]]
  v(1em)
}
#let abstract-title() = align(center)[#text(size: 14pt, weight: "bold")[摘要]]
#let keywords-cn(body) = block(above: 1em)[
  #text(font: hei-font, size: 12pt, weight: "bold")[关键词：] #body
]
#let abstract-cn(body, keywords) = {
  abstract-title()
  block(above: 0.15em)[#body]
  keywords-cn(keywords)
  pagebreak()
}
#let toc-page() = {
  show outline.entry.where(level: 1): it => link(
    it.element.location(),
    block(above: 7pt)[
      #text(font: hei-font, size: 12pt, weight: "bold")[
        #grid(
          columns: (auto, 1fr, auto),
          column-gutter: 0.5em,
          [#it.prefix()#it.body()],
          [#repeat[.]],
          [#it.page()],
        )
      ]
    ],
  )
  outline(
    title: align(center)[#text(font: hei-font, size: 17.3pt, weight: "bold")[目录]],
    depth: 3,
  )
  pagebreak()
}
#let references-cn() = [
#heading(numbering: none, outlined: true)[参考文献]
#{ set par(first-line-indent: 0pt, spacing: 0.35em); include("references.typ") }
]
#let appendix-cn(file: "sections/A_code.typ") = [
#heading(numbering: none, outlined: true)[附录 A #h(1em) 核心代码]
#include(file)
]

#let three-line-table(caption, columns, header, body, inset: (x: 0.35em, y: 0.52em), cell-align: center) = {
  let col-count = header.len()
  let body-rows = calc.floor(body.len() / col-count)
  let bottom-y = body-rows + 1
  let styled-header = header.map(cell => strong(cell))

  block(width: 100%, breakable: false)[
    #align(center)[
      #box[
        #align(center)[#text(font: hei-font, size: 10.5pt, weight: "bold")[#caption]]
        #v(0.6em)
        #table(
          columns: columns,
          align: cell-align,
          stroke: none,
          inset: inset,
          table.hline(y: 0, stroke: 0.8pt),
          table.hline(y: 1, stroke: 0.5pt),
          table.hline(y: bottom-y, stroke: 0.8pt),
          ..styled-header,
          ..body,
        )
      ]
    ]
  ]
}

#counter(page).update(1)

#paper-title[药材烘干过程的温度与水分浓度场演化模型]

#abstract-cn[
  烘干是决定中药材品质的关键工序。本文以圆柱药材为对象，建立了热风条件下内部温度与干基水分浓度耦合输运的一维径向机理模型，为四个子问题给出了一致的求解框架与定量结果。

  针对问题一（附录2 常数物性、0–1800 s 预热平衡），将傅里叶导热与变系数 Fick 扩散方程经 Robin 对流边界与附件1 风况调度联立，采用节点控制体有限体积—Crank–Nicolson（物性中点 Picard 迭代）格式求解，$Delta r$ = 0.1 cm、$Delta t$ = 0.25 s，输出表1、表2 及 1 s 分辨率的 result1.xlsx：1800 s 时中心升温 5.58 °C、表面水分已降至 1.5116 kg/kg，呈现“表层先行失水、芯部滞后响应”的格局。

  针对问题二，物性改用附录3 经验式并衔接恒温段（50.013 °C、0.04999 kg/kg），得到表3、表4：3 h 末中心温度已达风温的 99.6%，而中心水分仅降至 2.1605 kg/kg，热、质过程时间尺度分离显著。针对问题三，以“全场 $C < 0.15$”为判停条件，得烘干时长 $t_"end"$ = 59273 s ≈ 16.4647 h（表5、result3.xlsx）。

  针对问题四，引入随体坐标将附件2 给出的半径收缩 $R(t)$（2.000→1.198 cm）映射为固定域问题，配合附录4 物性求得 $t_"end"$ = 70758 s ≈ 19.6550 h，判停时半径 1.2107 cm（表6、result4.xlsx）；相对“附录4 物性、不收缩”的对照基准 39.20 h，收缩使时长缩短 49.87\%。

  灵敏度分析表明：烘干时长由传质链控制——$h_m$、$D$ 的 ±20\% 扰动引起 −11.1\%～+16.8\%（问题三）与 −9.1\%～+13.5\%（问题四）的时长变化，而换热与导热参数影响不足 0.14\%；判停结果对网格/步长（≤0.01\%）、恒温取值（0.16\%）、端面修正（4.99\%）与潜热耦合（0.02\%）均稳健。据此建议优先以强化表面换质（提风速、降排潮湿度）调控干燥制度。
][
  传热传质 #h(1em) 有限体积法 #h(1em) Crank–Nicolson 格式 #h(1em) 判停条件 #h(1em) 动边界收缩 #h(1em) 灵敏度分析
]

#include("sections/1_restatement.typ")
#include("sections/2_analysis.typ")
#include("sections/3_assumptions.typ")
#include("sections/4_symbols.typ")
#include("sections/5_problem1.typ")
#include("sections/6_problem2.typ")
#include("sections/7_problem3.typ")
#include("sections/8_problem4.typ")
#include("sections/9_sensitivity.typ")
#include("sections/10_evaluation.typ")

#pagebreak()
#references-cn()
#pagebreak()
#appendix-cn()
