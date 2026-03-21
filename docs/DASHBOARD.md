# Dashboard v0.3 结构

## 页面目标
在现有 BTC + Exchange Volume 主图基础上，增加交易所每日动态、业务线异动、重点事件、市场新闻四类信息，使页面从"图表页"升级为"情报看板"。

---

## 1. 页面总体结构

### A. 顶部 Header
- Logo / 项目名
- 刷新按钮
- 数据更新时间
- 后续可扩展：数据源状态提示

---

### B. 控制面板 Control Panel
- 时间范围：7d / 30d / 90d
- 市场类型：total / spot / futures
- 交易所多选：
  - Binance
  - OKX
  - Bybit
  - Bitget
  - Hyperliquid
- 事件类型筛选：
  - 全部
  - 公告
  - 上币
  - 下币
  - 活动
  - 费率调整
  - 产品上线
  - VIP政策
  - 钱包问题
  - 合规
  - 合作
  - 宏观
  - 社媒热点
  - 行业新闻

---

### C. 主图区 Main Timeline Chart
#### 图表内容
- 横轴：时间
- 左轴：BTC Price
- 右轴：Exchange Volume
- 折线：
  - BTC
  - Binance
  - OKX
  - Bybit
  - Bitget
  - Hyperliquid
- 图上事件点：
  - 与时间轴对齐
  - hover 显示事件摘要
  - click 联动下方事件流

#### 交互
- legend 开关
- dataZoom
- hover tooltip
- click event point

---

### D. Insight Summary 区块（新增）
位于主图下方第一层，2~3 张摘要卡片

#### 卡片 1：今日重点结论
示例：
- Binance 今日现货量上升，主要伴随上币和活动事件
- OKX 合约量变化较大，需关注费率政策
- Bybit 产品上线事件较多

#### 卡片 2：业务线异动
- 今日现货量变化最大交易所
- 今日合约量变化最大交易所
- 今日总量变化最大交易所

#### 卡片 3：重点风险
- 高优先级事件数
- 钱包问题 / 合规事件
- 异常波动提醒

---

### E. Daily Exchange Updates 区块（新增）
按交易所分板块展示每日动态

#### 展示方式
每家交易所一个卡片或一列：
- Binance
- OKX
- Bybit
- Bitget
- Hyperliquid

#### 每张卡片内容
- 今日总事件数
- 今日重点事件 3 条
- 今日 volume 摘要
- 今日主要业务线变化（spot/futures）

---

### F. Event Timeline 区块（升级现有事件流）
#### 顶部筛选
- 事件类型
- 交易所
- 风险等级

#### 列表内容
每条事件显示：
- 时间
- 事件类型
- 交易所
- 标题
- 摘要
- 来源
- 点击查看详情

#### 联动
- 点击主图事件点，高亮对应卡片
- 点击事件卡片，可在图上高亮对应时间点

---

### G. Market & News Watch 区块（后续扩展）
先保留占位，不一定 v0.3 全做完

包含：
- 热点新闻
- 宏观事件
- 市场异动
- 后续社媒热点

---

## 2. 页面优先级

### v0.3 必须完成
- 主图
- Insight Summary
- Daily Exchange Updates
- Event Timeline

### v0.4 再完成
- Market & News Watch
- 宏观和新闻扩展
- 更复杂的规则总结
