from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional, Dict
from datetime import datetime, timedelta, timezone
import json

from app.database import get_db
from app.models import models
from app.services import coinalyze_service
from app.models.schemas import (
    ChartDataResponseV2, ChartEventResponse, BtcResponse, VolumeResponse,
    EventsListResponse, EventListItem,
    ExchangeInfo, FiltersResponse
)
from app.services.btc_service import fetch_btc_prices, generate_mock_btc_prices
from app.services.exchange_service import get_cached_exchange_volumes, get_all_exchange_volumes_series

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

@router.get("/chart-data")
def get_chart_data_unified(
    exchanges: Optional[str] = Query(None, description="交易所逗号分隔，如 binance,okx,bybit"),
    days: int = Query(7, ge=1, le=30, description="天数"),
    db: Session = Depends(get_db)
):
    """
    BTC 主交易对跨所情报看板数据接口
    返回格式:
    - dates: 所有日期（唯一有序）
    - price: BTC 日级收盘价
    - spot_volumes: 各所 BTC 现货 24h 量
    - futures_volumes: 各所 BTC 合约 24h 量
    - oi: 各所 BTC 持仓量（Coinalyze）
    - events: 事件（按选中交易所过滤）
    """
    if not exchanges:
        exchange_list = ["binance", "okx", "bybit", "bitget", "hyperliquid"]
    else:
        exchange_list = [e.strip() for e in exchanges.split(",")]

    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)

    # ========== 1. BTC 价格（每日收盘价）==========
    btc_records = db.query(models.BtcPrice).filter(
        models.BtcPrice.timestamp >= start_time,
        models.BtcPrice.timestamp <= end_time
    ).order_by(models.BtcPrice.timestamp).all()

    price_by_day: Dict[str, float] = {}
    for r in btc_records:
        day_key = r.timestamp.strftime("%Y-%m-%d")
        price_by_day[day_key] = r.price
    dates = sorted(price_by_day.keys())
    price_series = [price_by_day.get(d, None) for d in dates]

    # ========== 2. 现货量 / 合约量（来自 dashboard_daily_snapshots）==========
    spot_volumes: Dict[str, List[Optional[float]]] = {ex: [] for ex in exchange_list}
    futures_volumes: Dict[str, List[Optional[float]]] = {ex: [] for ex in exchange_list}

    for ex in exchange_list:
        snapshots = db.query(models.DashboardDailySnapshot).filter(
            models.DashboardDailySnapshot.snapshot_date.in_(dates),
            models.DashboardDailySnapshot.exchange == ex
        ).all()
        snap_map = {s.snapshot_date: s for s in snapshots}
        for d in dates:
            s = snap_map.get(d)
            if s:
                spot_volumes[ex].append(s.spot_volume)
                futures_volumes[ex].append(s.futures_volume)
            else:
                spot_volumes[ex].append(None)
                futures_volumes[ex].append(None)

    # ========== 3. OI 数据（Coinalyze）==========
    oi_data: List[Dict] = []
    try:
        from app.services import coinalyze_service
        oi_raw = coinalyze_service.fetch_current_oi_usd(["BTC"], exchange_list)
        for item in oi_raw:
            oi_data.append({
                "exchange": item["exchange"],
                "oi_usd": item["oi_usd"],
                "funding_rate": None,
            })
        fr_raw = coinalyze_service.fetch_current_funding_rates(["BTC"], exchange_list)
        fr_map = {f["exchange"]: f["funding_rate"] for f in fr_raw}
        for oi in oi_data:
            oi["funding_rate"] = fr_map.get(oi["exchange"])
    except Exception as e:
        print(f"Coinalyze OI error: {e}")

    # ========== 4. Events（来自 exchange_events，按交易所过滤）==========
    evt_query = db.query(models.ExchangeEvent).filter(
        models.ExchangeEvent.event_time >= start_time,
        models.ExchangeEvent.event_time <= end_time
    )
    if exchange_list:
        evt_query = evt_query.filter(models.ExchangeEvent.exchange.in_(exchange_list))
    evt_query = evt_query.order_by(models.ExchangeEvent.event_time)
    evt_records = evt_query.all()

    events_data = [
        {
            "id": r.id,
            "event_date": r.event_time.strftime("%Y-%m-%d"),
            "ts": r.event_time.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
            "exchange": r.exchange,
            "event_type": r.event_type,
            "title": r.title,
            "impact_score": r.impact_score if r.impact_score is not None else 50
        }
        for r in evt_records
    ]

    return {
        "dates": dates,
        "price": {"BTC": price_series},
        "spot_volumes": spot_volumes,
        "futures_volumes": futures_volumes,
        "oi": oi_data,
        "events": events_data,
        # 数据来源标识: official=官方API, converted=单位转换, estimated=估算
        "volume_methods": {
            "binance_spot": "official",
            "binance_futures": "official",
            "okx_spot": "official",
            "okx_futures": "official",
            "bybit_spot": "official",
            "bybit_futures": "official",
            "hyperliquid_futures": "estimated",  # 全所BTC合计，非单一币对
        },
    }

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
    exchange_list = exchanges.split(",") if isinstance(exchanges, str) and exchanges else [e["id"] for e in SUPPORTED_EXCHANGES]
    
    # 获取交易量 (使用缓存)
    cached_volumes = get_all_exchange_volumes_series(hours)
    
    # 构建返回数据
    volumes = []
    for ex in exchange_list:
        if ex not in cached_volumes:
            continue
        
        ex_data = cached_volumes[ex]
        
        if market_type == "total":
            # 总量 = 现货 + 合约
            spot_data = ex_data.get("spot", [])
            futures_data = ex_data.get("futures", [])
            
            # 合并数据
            for i in range(min(len(spot_data), len(futures_data))):
                spot_val = spot_data[i].get("value") or 0
                futures_val = futures_data[i].get("value") or 0
                volumes.append(VolumeResponse(
                    ts=spot_data[i]["ts"],
                    exchange=ex,
                    market_type="total",
                    value=spot_val + futures_val
                ))
        else:
            # 现货或合约
            market_data = ex_data.get(market_type, [])
            for item in market_data:
                volumes.append(VolumeResponse(
                    ts=item["ts"],
                    exchange=ex,
                    market_type=market_type,
                    value=item["value"]
                ))
    
    # 按时间排序
    volumes.sort(key=lambda x: x.ts)
    
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
    获取事件列表 - 优先 exchange_events 表，支持 event_type 和 exchange 筛选
    """
    # 默认时间范围：最近30天
    if not end_time:
        end_time = datetime.utcnow()
    if not start_time:
        start_time = end_time - timedelta(days=30)

    # 优先从 exchange_events 读取
    exchange_event_count = db.query(models.ExchangeEvent).filter(
        models.ExchangeEvent.event_time >= start_time,
        models.ExchangeEvent.event_time <= end_time
    ).count()

    if exchange_event_count > 0:
        query = db.query(models.ExchangeEvent).filter(
            models.ExchangeEvent.event_time >= start_time,
            models.ExchangeEvent.event_time <= end_time
        )
        if event_type:
            query = query.filter(models.ExchangeEvent.event_type == event_type)
        if exchange:
            query = query.filter(models.ExchangeEvent.exchange == exchange)

        total = query.count()
        records = query.order_by(desc(models.ExchangeEvent.event_time))\
            .offset((page - 1) * page_size)\
            .limit(page_size)\
            .all()

        return EventsListResponse(
            events=[
                EventListItem(
                    id=r.id,
                    ts=r.event_time.isoformat() + "Z",
                    exchange=r.exchange,
                    event_type=r.event_type,
                    title=r.title,
                    summary=r.summary,
                    source=r.source,
                    url=r.source_url
                )
                for r in records
            ],
            total=total
        )

    # Fallback 到 structured_events
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


# ========== Coinalyze 数据端点 ==========

@router.get("/coinalyze/oi-summary")
def get_oi_summary(
    symbol: str = Query("BTC", description="币种，如 BTC/ETH"),
):
    """
    获取指定币种在各所的持仓量(OI) + 资金费率汇总
    数据来源: Coinalyze
    """
    exchanges = ["binance", "okx", "bybit", "hyperliquid"]
    result = coinalyze_service.get_btc_oi_summary()
    return result


@router.get("/coinalyze/oi-history")
def get_oi_history(
    symbol: str = Query("BTC", description="币种"),
    exchange: str = Query("binance", description="交易所"),
    days: int = Query(7, ge=1, le=30, description="天数"),
):
    """
    获取指定币种/交易所的 OI 历史 (日级 OHLC)
    """
    history = coinalyze_service.fetch_oi_history(
        symbol=symbol.upper(),
        exchange=exchange.lower(),
        days=days
    )
    return {
        "symbol": symbol.upper(),
        "exchange": exchange.lower(),
        "history": history,
    }


@router.get("/coinalyze/funding-history")
def get_funding_history(
    symbol: str = Query("BTC", description="币种"),
    exchange: str = Query("binance", description="交易所"),
    days: int = Query(7, ge=1, le=30, description="天数"),
):
    """
    获取指定币种/交易所的资金费率历史 (日级)
    """
    history = coinalyze_service.fetch_funding_history(
        symbol=symbol.upper(),
        exchange=exchange.lower(),
        days=days
    )
    return {
        "symbol": symbol.upper(),
        "exchange": exchange.lower(),
        "history": history,
    }


@router.get("/coinalyze/ls-ratio")
def get_ls_ratio(
    symbol: str = Query("BTC", description="币种"),
    exchange: str = Query("binance", description="交易所"),
    days: int = Query(7, ge=1, le=30, description="天数"),
):
    """
    获取指定币种/交易所的多空比历史
    """
    history = coinalyze_service.fetch_long_short_ratio(
        symbol=symbol.upper(),
        exchange=exchange.lower(),
        days=days
    )
    return {
        "symbol": symbol.upper(),
        "exchange": exchange.lower(),
        "history": history,
    }
