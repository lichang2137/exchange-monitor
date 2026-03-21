# API Contract v0.3

## 1. GET /api/chart
返回主图数据

### Query Parameters
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| range | string | 否 | 时间范围：7d / 30d / 90d（默认7d） |
| market_type | string | 否 | 市场类型：total / spot / futures（默认total） |
| exchanges | string | 否 | 交易所列表，逗号分隔（默认全部） |

### Response
```json
{
  "btc": [
    { "ts": "2026-03-10T00:00:00Z", "value": 81234.5 }
  ],
  "volumes": [
    {
      "ts": "2026-03-10T00:00:00Z",
      "exchange": "binance",
      "market_type": "spot",
      "value": 123456789
    }
  ],
  "events": [
    {
      "id": "evt_001",
      "ts": "2026-03-10T10:00:00Z",
      "exchange": "binance",
      "event_type": "listing",
      "title": "Binance 上线 AXL 代币",
      "risk_level": "medium"
    }
  ]
}
```

### Response Fields
| 字段 | 类型 | 说明 |
|------|------|------|
| btc | array | BTC 价格时间序列 |
| btc[].ts | string | ISO 8601 时间戳 |
| btc[].value | number | BTC 价格（USD） |
| volumes | array | 交易所交易量时间序列 |
| volumes[].ts | string | ISO 8601 时间戳 |
| volumes[].exchange | string | 交易所名称 |
| volumes[].market_type | string | 市场类型 |
| volumes[].value | number | 交易量（USD） |
| events | array | 事件列表 |
| events[].id | string | 事件ID |
| events[].ts | string | ISO 8601 时间戳 |
| events[].exchange | string | 交易所 |
| events[].event_type | string | 事件类型 |
| events[].title | string | 标题 |
| events[].risk_level | string | 风险等级 |

---

## 2. GET /api/events
返回事件流列表

### Query Parameters
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| range | string | 否 | 时间范围：7d / 30d / 90d（默认7d） |
| event_type | string | 否 | 事件类型筛选 |
| exchange | string | 否 | 交易所筛选 |
| risk_level | string | 否 | 风险等级筛选 |
| page | integer | 否 | 页码（默认1） |
| page_size | integer | 否 | 每页数量（默认20） |

### Response
```json
{
  "events": [
    {
      "id": "evt_001",
      "event_time": "2026-03-10T10:00:00Z",
      "exchange": "binance",
      "event_type": "listing",
      "title": "Binance 上线 AXL 代币",
      "summary": "Binance announced the listing of AXL...",
      "source": "binance_announcement",
      "source_url": "https://...",
      "risk_level": "medium",
      "related_market_type": "spot",
      "impact_score": 72
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 20
}
```

---

## 3. GET /api/dashboard/summary
返回 Dashboard 顶部摘要

### Query Parameters
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| date | string | 否 | 日期 YYYY-MM-DD（默认今日） |

### Response
```json
{
  "date": "2026-03-17",
  "top_takeaways": [
    "Binance 今日现货量上升，伴随上币事件",
    "OKX 合约量变化较大，需关注费率调整",
    "Bybit 今日产品上线和活动事件较多"
  ],
  "top_movers": {
    "total": { "exchange": "binance", "change_pct": 12.5 },
    "spot": { "exchange": "binance", "change_pct": 15.2 },
    "futures": { "exchange": "okx", "change_pct": 9.1 }
  },
  "risk_summary": {
    "high_risk_events": 2,
    "wallet_issues": 1,
    "compliance_events": 0
  }
}
```

---

## 4. GET /api/dashboard/exchange-updates
返回各交易所每日动态板块

### Query Parameters
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| date | string | 否 | 日期 YYYY-MM-DD（默认今日） |

### Response
```json
[
  {
    "exchange": "binance",
    "total_volume": 1234567890,
    "spot_volume": 456789012,
    "futures_volume": 777777878,
    "total_change_pct": 12.5,
    "spot_change_pct": 8.3,
    "futures_change_pct": 15.1,
    "event_count": 5,
    "high_risk_event_count": 1,
    "top_events": [
      {
        "id": "evt_001",
        "event_type": "listing",
        "title": "Binance 上线 AXL 代币",
        "event_time": "2026-03-17T14:00:00Z"
      }
    ]
  }
]
```

---

## 5. GET /api/news
返回市场动态、热点新闻、宏观事件

### Query Parameters
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| news_type | string | 否 | 类型：market/macro/industry/hot |
| range | string | 否 | 时间范围：7d / 30d（默认7d） |

### Response
```json
[
  {
    "id": "news_001",
    "published_at": "2026-03-17T08:00:00Z",
    "news_type": "macro",
    "title": "Federal Reserve signals pause",
    "summary": "...",
    "source": "Reuters",
    "source_url": "https://...",
    "tags": ["macro", "fed"],
    "related_exchanges": [],
    "related_symbols": ["BTC"],
    "importance_score": 88
  }
]
```

---

## 6. GET /api/exchanges
返回支持的交易所列表

### Response
```json
[
  {
    "id": "binance",
    "name": "Binance",
    "color": "#F0B90B"
  },
  {
    "id": "okx",
    "name": "OKX",
    "color": "#FFFFFF"
  }
]
```

---

## 7. GET /api/filters
返回筛选器选项

### Response
```json
{
  "market_types": [
    { "id": "spot", "name": "现货" },
    { "id": "futures", "name": "合约" },
    { "id": "total", "name": "总量" }
  ],
  "event_types": [
    { "id": "announcement", "name": "公告", "color": "#f85149" },
    { "id": "listing", "name": "上币", "color": "#3fb950" },
    { "id": "delisting", "name": "下币", "color": "#f85149" },
    { "id": "campaign", "name": "活动", "color": "#58a6ff" },
    { "id": "fee_change", "name": "费率调整", "color": "#d29922" },
    { "id": "product_launch", "name": "产品上线", "color": "#a371f7" }
  ]
}
```

---

## 8. GET /health
健康检查

### Response
```json
{
  "status": "ok"
}
```

---

## 错误响应格式

```json
{
  "detail": "Error message here"
}
```

## HTTP Status Codes

| Code | 说明 |
|------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |
