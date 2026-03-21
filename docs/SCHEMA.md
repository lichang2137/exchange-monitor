# Schema v0.3

## 1. exchange_volume_timeseries
用于存储交易所业务线交易量时间序列

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 自增ID |
| ts | TEXT | 时间戳，ISO 8601 |
| exchange | TEXT | 交易所名称 |
| market_type | TEXT | total / spot / futures |
| volume_usd | REAL | 交易量（USD） |
| source | TEXT | 数据来源 |
| created_at | TEXT | 创建时间 |

**索引建议：**
```sql
CREATE INDEX idx_ts ON exchange_volume_timeseries(ts);
CREATE INDEX idx_exchange_market_ts ON exchange_volume_timeseries(exchange, market_type, ts);
```

---

## 2. exchange_events
用于存储结构化后的交易所事件

| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT PRIMARY KEY | 事件ID |
| event_time | TEXT | 事件时间，ISO 8601 |
| exchange | TEXT | 交易所 |
| event_type | TEXT | 事件类型 |
| title | TEXT | 标题 |
| summary | TEXT | 摘要 |
| source | TEXT | 来源 |
| source_url | TEXT | 来源URL |
| risk_level | TEXT | 风险等级：low/medium/high |
| related_market_type | TEXT | 关联市场类型 |
| related_symbols | TEXT | 关联代币（JSON array） |
| tags | TEXT | 标签（JSON array） |
| impact_score | INTEGER | 影响评分（0-100） |
| created_at | TEXT | 创建时间 |

**索引建议：**
```sql
CREATE INDEX idx_event_time ON exchange_events(event_time);
CREATE INDEX idx_exchange_event_type ON exchange_events(exchange, event_type);
CREATE INDEX idx_risk_level ON exchange_events(risk_level);
```

---

## 3. dashboard_daily_snapshots
用于做 Dashboard 摘要和每日动态

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 自增ID |
| snapshot_date | TEXT | 快照日期 YYYY-MM-DD |
| exchange | TEXT | 交易所 |
| total_volume | REAL | 总量 |
| spot_volume | REAL | 现货量 |
| futures_volume | REAL | 合约量 |
| total_change_pct | REAL | 总量变化百分比 |
| spot_change_pct | REAL | 现货变化百分比 |
| futures_change_pct | REAL | 合约变化百分比 |
| event_count | INTEGER | 事件数量 |
| high_risk_event_count | INTEGER | 高风险事件数 |
| created_at | TEXT | 创建时间 |

**索引建议：**
```sql
CREATE UNIQUE INDEX idx_date_exchange ON dashboard_daily_snapshots(snapshot_date, exchange);
```

---

## 4. news_items
用于扩展市场动态、热点新闻、宏观事件

| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT PRIMARY KEY | 新闻ID |
| published_at | TEXT | 发布时间，ISO 8601 |
| news_type | TEXT | 类型：market/macro/industry/hot |
| title | TEXT | 标题 |
| summary | TEXT | 摘要 |
| source | TEXT | 来源 |
| source_url | TEXT | 来源URL |
| tags | TEXT | 标签（JSON array） |
| related_exchanges | TEXT | 关联交易所（JSON array） |
| related_symbols | TEXT | 关联代币（JSON array） |
| importance_score | INTEGER | 重要性评分（0-100） |
| created_at | TEXT | 创建时间 |

**索引建议：**
```sql
CREATE INDEX idx_published_at ON news_items(published_at);
CREATE INDEX idx_news_type ON news_items(news_type);
```

---

## 5. insight_summaries（可选）
先规则生成，后续可 AI 生成

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 自增ID |
| summary_date | TEXT | 摘要日期 YYYY-MM-DD |
| summary_type | TEXT | 类型：daily/hourly |
| title | TEXT | 标题 |
| content | TEXT | 内容 |
| related_exchanges | TEXT | 关联交易所（JSON array） |
| created_at | TEXT | 创建时间 |

---

## 数据流向图

```
┌─────────────────────────────────────────────────────────────┐
│                     数据采集层                                 │
├─────────────────────────────────────────────────────────────┤
│  Binance API  │  OKX API  │  Bybit API  │  Hyperliquid   │
└───────┬───────┴─────┬─────┴──────┬─────┴────────┬──────────┘
        │             │            │              │
        ▼             ▼            ▼              ▼
┌─────────────────────────────────────────────────────────────┐
│                   存储层 (SQLite)                             │
├──────────────┬──────────────┬───────────────┬────────────────┤
│ volume_      │ exchange_    │ dashboard_    │ news_          │
│ timeseries   │ events       │ daily_snapshots│ items         │
└──────────────┴──────────────┴───────────────┴────────────────┘
        │             │            │              │
        ▼             ▼            ▼              ▼
┌─────────────────────────────────────────────────────────────┐
│                   API 层 (FastAPI)                          │
├─────────────────────────────────────────────────────────────┤
│  /api/chart  │  /api/events  │  /api/dashboard/*  │  /api/news │
└──────────────┴──────────────┴─────────────────┴────────────┘
        │             │            │              │
        ▼             ▼            ▼              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Frontend (React)                          │
├──────────────┬──────────────┬───────────────┬────────────────┤
│   MainChart  │  EventList   │  Dashboard    │   NewsWatch    │
│   Insight    │  Exchange    │  Summary      │                │
└──────────────┴──────────────┴───────────────┴────────────────┘
```
