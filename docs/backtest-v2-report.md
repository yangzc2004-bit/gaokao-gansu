# V2 回测校准报告

## 总体
```
 samples  records  brier_score  avg_probability  actual_admit_rate
  111310    22262       0.2512           0.4036                0.6
```

## 按历史年数
```
 history_years  samples  avg_probability  actual_admit_rate
             1    22750           0.3471                0.6
             2    88560           0.4181                0.6
```

## 按冲稳保桶
```
bucket  samples  avg_probability  actual_admit_rate
     保    28306           0.6549             0.8104
     冲    38227           0.2415             0.4155
     稳    26140           0.4754             0.6882
```

## 当前阈值命中效果
```
bucket  threshold  samples  actual_admit_rate  avg_probability
     冲       0.20    24938             0.4684           0.3007
     稳       0.45    16118             0.7141           0.5165
     保       0.70     8831             0.8700           0.7630
```

## 概率分箱校准
```
probability_bin  samples  avg_probability  actual_admit_rate
  (-0.001, 0.2]    25911           0.0832             0.3666
     (0.2, 0.4]    27609           0.3040             0.4875
     (0.4, 0.6]    31414           0.4996             0.6977
     (0.6, 0.8]    22439           0.6854             0.8260
     (0.8, 1.0]     3937           0.8382             0.8580
```

## 说明
- 回测口径：使用 `slot1` 作为留出年，只使用 `slot2/slot3` 的真实历史数据生成 `target_rank` 与概率。
- 样本构造：围绕真实录取最低位次，按 `0.90/0.95/1.00/1.05/1.10` 五个倍数模拟考生位次。
- 录取标签：`user_rank <= slot1 最低位次` 记为录取成功，否则记为未录取。
- 该回测用于校准 V2 的概率与阈值，不代表真实全体考生分布。