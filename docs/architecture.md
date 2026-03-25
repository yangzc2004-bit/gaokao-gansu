# 系统架构设计

## 1. 分层架构

### 数据层
- 原始招生数据：`data.xlsx`
- 原始规则文档：`rules.txt`
- 清洗结果：`data/processed/admission_records.csv`
- 历史指标长表：`data/processed/admission_metrics_long.csv`
- 规则库：`configs/policy_rules.gansu.json`
- 区域字典：`configs/region_dict.gansu.json`

### 服务层
- `backend/pipeline/clean_admissions.py`：清洗招生库
- `backend/pipeline/build_policy_rules.py`：构造规则库
- `backend/rules/eligibility.py`：专项资格判定
- `backend/recommend/ranker.py`：冲稳保与政策红利推荐
- `backend/features/subject_parser.py`：选科解析
- `backend/features/rank_risk.py`：位次风险分层

### 展示层
- `frontend/app.py`：Streamlit 主入口
- `frontend/components/cards.py`：志愿卡片
- `frontend/components/charts.py`：趋势图与 CV 图

## 2. 核心数据流

1. 读取 `data.xlsx`
2. 标准化字段名、批次、科类、院校标签、选科表达式
3. 将近三年录取字段宽表转成长表
4. 解析 `rules.txt` 为可执行 JSON 规则
5. 输入用户画像，运行资格判定
6. 在可报范围内按位次风险、波动、学校层次、政策红利排序
7. 输出冲/稳/保/政策红利四个列表

## 3. 推荐逻辑

### 冲稳保
- 冲：预测位次略高于考生当前位次，允许一定风险
- 稳：预测位次与考生位次接近，波动可控
- 保：预测位次明显低于考生当前位次，优先确定性

### 政策红利
重点排序以下候选：
- 用户满足但市场关注度较低的专项计划
- 位次要求相对宽松、学校层次较优的志愿
- 近年平均位次稳定且 CV 低的专业组
- 与用户地区、户籍、民族、学籍高度匹配的计划

## 4. 前端交互

### 左侧输入
- 科类：历史 / 物理
- 四选二：化学 / 生物 / 地理 / 政治（按实际新高考组合约束）
- 分数
- 位次
- 所在地区（县/区）
- 户籍性质
- 民族
- 学籍连续年限
- 监护人户籍
- 是否建档立卡
- 是否革命老区/两州一县/农村户籍等

### 右侧输出
- `冲`
- `稳`
- `保`
- `政策红利`

每张卡片展示：
- 学校名称 / 专业组 / 专业
- 批次 / 科类 / 选科要求
- 近三年最低位次趋势
- 平均位次
- CV 波动
- 命中政策
- 推荐理由

## 5. 第一版技术取舍

- 预测主轴：位次优先
- 推荐方式：规则引擎 + 区间分层 + 稳定性排序
- 不在第一版引入复杂机器学习训练流程
- 第二版可升级为 LightGBM / XGBoost 概率评分
