= 符号说明

本文主要符号及含义如下表所示，其余符号在首次出现处说明。

#align(center)[
  #table(
    columns: (5.2em, 22em, 8em),
    align: (center, left, center),
    inset: (x: 0.5em, y: 0.45em),
    stroke: none,
    table.hline(stroke: 0.8pt),
    [#strong[符号]], [#strong[含义]], [#strong[单位]],
    table.hline(stroke: 0.5pt),
    [$r$, $R$, $L$], [径向坐标；药材当前半径；药材长度], [m（cm）],
    [$xi = r/R(t)$], [随体归一化径向坐标（问题四）], [—],
    [$t$, $t_"end"$], [时间；烘干结束时刻], [s；h],
    [$T(r,t)$], [药材温度], [°C],
    [$T_a(t)$], [烘房风温], [°C],
    [$C(r,t)$], [药材干基水分浓度], [kg/kg],
    [$C_a(t)$], [烘房空气水分浓度], [kg/kg],
    [$rho(C)$], [密度], [kg/m³],
    [$c_p(C)$], [比热容], [J/(kg·K)],
    [$k(C)$], [热传导系数], [W/(m·K)],
    [$D(C,T)$], [水分浓度扩散系数], [m²/s],
    [$h$], [对流换热系数], [W/(m²·K)],
    [$h_m$], [对流传质系数], [m/s],
    [$xi_j = j/N$], [径向节点（$j = 0,…,N$）], [—],
    [$Delta r$, $Delta t$], [径向/时间步长], [m；s],
    [$"Bi"_h$, $"Bi"_m$], [热/质毕渥数 $h R / k$、$h_m R / D$], [—],
    [$"Fo" = D t/R^2$], [傅里叶数（扩散时间尺度）], [—],
    table.hline(stroke: 0.8pt),
  )
]
