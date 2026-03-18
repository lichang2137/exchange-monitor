# Metric Dictionary v0.1

## 1. 时间粒度
默认时间粒度：1 day
后续可扩展为：1 hour / 4 hour / 1 day

## 2. BTC Price
- 字段名：btc_price
- 含义：BTC 在对应时间粒度的收盘价或最新价
- 单位：USD

## 3. Exchange Total Volume
- 字段名：exchange_total_volume
- 含义：交易所在对应时间粒度内的总交易量
- 单位：USD

## 4. Exchange Spot Volume
- 字段名：exchange_spot_volume
- 含义：交易所在对应时间粒度内的现货交易量
- 单位：USD

## 5. Exchange Futures Volume
- 字段名：exchange_futures_volume
- 含义：交易所在对应时间粒度内的合约交易量
- 单位：USD

## 6. Exchange Name 标准值
- binance
- okx
- bybit
- bitget
- hyperliquid
- coinbase
- gate
- kraken
- htx

## 7. Market Type 标准值
- total
- spot
- futures

## 8. 时间范围
- 7d
- 30d
- 90d
- 180d

## 9. 缺失值规则
- 缺失值默认返回 null
- 前端用折线断点展示，不强行补值
- 后续如需平滑，可单独增加填补策略

## 10. 事件时间
- 字段名：event_time
- 含义：事件发布时间
- 格式：ISO 8601

## 11. 事件与图表关系
事件默认按 event_time 映射到图表时间轴位置，不做复杂因果推断。

# Visual Style v0.1

## 12. Exchange Color Mapping
- Binance: #F0B90B
- OKX: #1E3A8A
- Bybit: #F97316
- Bitget: #38BDF8
- Hyperliquid: #22C55E
