from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional, Dict
from datetime import datetime, timedelta, timezone
import json

from app.database import get_db
from app.models import models
from app.models.schemas import (
    ChartDataResponseV2, ChartEventResponse, BtcResponse, VolumeResponse,
    EventsListResponse, EventListItem,
    ExchangeInfo, FiltersResponse
)
from app.services.btc_service import fetch_btc_prices, generate_mock_btc_prices

router = APIRouter()


# ========== 常量定义 ==========

SUPPORTED_EXCHANGES = [
    {"id": "binance", "name": "Binance", "color": "#F0B90B"},
    {"id": "okx", "name": "OKX", "color": "#FFFFFF"},
    {"id": "bybit", "name": "Bybit", "color": "#FFAB00"},
    {"id": "bitget", "name": "Bitget", "color": "#00C077"},
    {"id": "hyperliquid", "name": "Hyperliquid", "color": "#E84855"},
]

MARKET_TYPES = [
    {"id": "spot", "name": "现货"},
    {"id": "futures", "name": "合约"},
    {"id": "total", "name": "总量"},
]

EVENT_TYPES = [
    {"id": "announcement", "name": "公告", "color": "#f85149"},
    {"id": "listing", "name": "上币", "color": "#3fb950"},
    {"id": "delisting", "name": "下币", "color": "#f85149"},
    {"id": "campaign", "name": "活动", "color": "#58a6ff"},
    {"id": "fee_change", "name": "费率调整", "color": "#d29922"},
    {"id": "product_launch", "name": "产品上线", "color": "#a371f7"},
    {"id": "vip_policy", "name": "VIP政策", "color": "#db61a2"},
    {"id": "wallet_issue", "name": "钱包问题", "color": "#f85149"},
    {"id": "compliance", "name": "合规", "color": "#8b949e"},
    {"id": "partnership", "name": "合作", "color": "#39d0d6"},
    {"id": "macro", "name": "宏观", "color": "#8b949e"},
    {"id": "social_hype", "name": "社媒热点", "color": "#a371f7"},
    {"id": "product", "name": "产品更新", "color": "#d29922"},
    {"id": "news", "name": "行业新闻", "color": "#39d0d6"},
]

# 缓存文件路径
BTC_CACHE_FILE = "/tmp/btc_price_cache.json"
BTC_CACHE_DURATION = 300  # 5分钟缓存


def get_cached_btc_prices(hours: int = 168) -> List[Dict]:
    """获取 BTC 价格（带缓存）"""
    import os
    import time
    
    cache_file = BTC_CACHE_FILE
    
    # 检查缓存是否存在且有效
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                cache = json.load(f)
            # 缓存时间不超过5分钟
            if time.time() - cache.get("timestamp", 0) < BTC_CACHE_DURATION:
                cached_data = cache.get("data", [])
                # 只返回请求的小时数
                return cached_data[:hours]
        except Exception:
            pass
    
    # 获取新数据
    prices = fetch_btc_prices(hours)
    
    # 写入缓存
    try:
        with open(cache_file, 'w') as f:
            json.dump({"timestamp": time.time(), "data": prices}, f)
    except Exception:
        pass
    
    return prices


# ========== API Endpoints ==========

@router.get("/chart", response_model=ChartDataResponseV2)
def get_chart_data_v2(
    market_type: str = Query("total", description="市场类型: spot/futures/total"),
    exchanges: Optional[str] = Query(None, description="交易所逗号分隔"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    db: Session = Depends(get_db)
):
    """
    获取图表数据 v2
    - BTC 价格时间序列 (真实数据 from Binance)
    - 交易所交易量时间序列
    - 事件列表
    """
    # 默认时间范围：最近7天
    if not end_time:
        end_time = datetime.utcnow()
    if not start_time:
        start_time = end_time - timedelta(days=7)
    
    # 计算需要的小时数
    hours = int((end_time - start_time).total_seconds() / 3600)
    hours = max(hours, 24)  # 至少24小时
    
    # 从 OKX 或 CoinGecko 获取真实 BTC 数据
    btc_data = get_cached_btc_prices(hours)
    
    # 如果获取失败或为空，生成模拟数据
    if not btc_data:
        btc_data = generate_mock_btc_prices(hours)
    
    # 过滤时间范围
    def parse_ts(ts_str: str) -> datetime:
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    
    btc = [
        BtcResponse(ts=item["ts"], value=item["value"])
        for item in btc_data
        if start_time.replace(tzinfo=timezone.utc) <= parse_ts(item["ts"]) <= end_time.replace(tzinfo=timezone.utc)
    ]
    
    # 解析交易所
    exchange_list = exchanges.split(",") if exchanges else [e["id"] for e in SUPPORTED_EXCHANGES]
    
    # 查询交易量 (从数据库)
    if market_type == "total":
        # 总量 = 现货 + 合约
        spot_query = db.query(models.ExchangeVolume).filter(
            models.ExchangeVolume.timestamp >= start_time,
            models.ExchangeVolume.timestamp <= end_time,
            models.ExchangeVolume.exchange.in_(exchange_list),
            models.ExchangeVolume.market_type == "spot"
        ).order_by(models.ExchangeVolume.timestamp, models.ExchangeVolume.exchange)
        
        futures_query = db.query(models.ExchangeVolume).filter(
            models.ExchangeVolume.timestamp >= start_time,
            models.ExchangeVolume.timestamp <= end_time,
            models.ExchangeVolume.exchange.in_(exchange_list),
            models.ExchangeVolume.market_type == "futures"
        ).order_by(models.ExchangeVolume.timestamp, models.ExchangeVolume.exchange)
        
        spot_data = { (v.timestamp, v.exchange): v.volume for v in spot_query.all()}
        futures_data = { (v.timestamp, v.exchange): v.volume for v in futures_query.all()}
        
        volumes = []
        for (ts, ex), spot_vol in spot_data.items():
            futures_vol = futures_data.get((ts, ex), 0)
            volumes.append(VolumeResponse(
                ts=ts.isoformat() + "Z",
                exchange=ex,
                market_type="total",
                value=spot_vol + futures_vol
            ))
        volumes.sort(key=lambda x: x.ts)
    else:
        vol_query = db.query(models.ExchangeVolume).filter(
            models.ExchangeVolume.timestamp >= start_time,
            models.ExchangeVolume.timestamp <= end_time,
            models.ExchangeVolume.exchange.in_(exchange_list),
            models.ExchangeVolume.market_type == market_type
        ).order_by(models.ExchangeVolume.timestamp)
        
        volumes = [
            VolumeResponse(
                ts=v.timestamp.isoformat() + "Z",
                exchange=v.exchange,
                market_type=v.market_type,
                value=v.volume
            )
            for v in vol_query.all()
        ]
    
    # 查询事件
    events_query = db.query(models.StructuredEvent).filter(
        models.StructuredEvent.is_published == True,
        models.StructuredEvent.event_time >= start_time,
        models.StructuredEvent.event_time <= end_time
    ).order_by(models.StructuredEvent.event_time)
    
    events = [
        ChartEventResponse(
            id=f"evt_{e.id}",
            ts=e.event_time.isoformat() + "Z",
            exchange=e.exchange,
            event_type=e.event_type,
            title=e.title
        )
        for e in events_query.all()
    ]
    
    return ChartDataResponseV2(btc=btc, volumes=volumes, events=events)


@router.get("/events", response_model=EventsListResponse)
def get_events_v2(
    event_type: Optional[str] = Query(None, description="事件类型"),
    exchange: Optional[str] = Query(None, description="交易所"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """
    获取事件列表 v2
    """
    # 默认时间范围：最近30天
    if not end_time:
        end_time = datetime.utcnow()
    if not start_time:
        start_time = end_time - timedelta(days=30)
    
    query = db.query(models.StructuredEvent).filter(
        models.StructuredEvent.is_published == True,
        models.StructuredEvent.event_time >= start_time,
        models.StructuredEvent.event_time <= end_time
    )
    
    if event_type:
        query = query.filter(models.StructuredEvent.event_type == event_type)
    if exchange:
        query = query.filter(models.StructuredEvent.exchange == exchange)
    
    total = query.count()
    events = query.order_by(desc(models.StructuredEvent.event_time))\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()
    
    return EventsListResponse(
        events=[
            EventListItem(
                id=f"evt_{e.id}",
                ts=e.event_time.isoformat() + "Z",
                exchange=e.exchange,
                event_type=e.event_type,
                title=e.title,
                summary=e.summary,
                source=e.exchange,
                url=None
            )
            for e in events
        ],
        total=total
    )


@router.get("/exchanges", response_model=List[ExchangeInfo])
def get_exchanges():
    """获取支持的交易所列表"""
    return [ExchangeInfo(**e) for e in SUPPORTED_EXCHANGES]


@router.get("/filters", response_model=FiltersResponse)
def get_filters():
    """获取筛选器选项"""
    return FiltersResponse(
        market_types=MARKET_TYPES,
        event_types=EVENT_TYPES
    )


@router.get("/btc/refresh")
def refresh_btc_cache():
    """手动刷新 BTC 缓存"""
    import os
    if os.path.exists(BTC_CACHE_FILE):
        os.remove(BTC_CACHE_FILE)
    prices = get_cached_btc_prices(168)
    return {"status": "ok", "count": len(prices)}
