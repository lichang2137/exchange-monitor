"""
Dashboard Service
负责生成 Dashboard 摘要和各交易所每日动态

数据来源:
- exchange_volume_timeseries: 交易量时间序列
- exchange_events: 结构化事件
- dashboard_daily_snapshots: 每日快照 (可选，用于缓存)

API 端点:
- /api/dashboard/summary
- /api/dashboard/exchange-updates
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta, date
import json
import logging

from app.models import models

logger = logging.getLogger(__name__)

# 支持的交易所
SUPPORTED_EXCHANGES = ["binance", "okx", "bybit", "bitget", "hyperliquid"]

# 事件类型中文映射
EVENT_TYPE_NAMES = {
    "announcement": "公告",
    "listing": "上币",
    "delisting": "下币",
    "campaign": "活动",
    "fee_change": "费率调整",
    "product_launch": "产品上线",
    "vip_policy": "VIP政策",
    "wallet_issue": "钱包问题",
    "compliance": "合规",
    "partnership": "合作",
    "macro": "宏观",
    "social_hype": "社媒热点",
    "product": "产品更新",
    "news": "行业新闻",
}


def get_date_str(target_date: Optional[date] = None) -> str:
    """获取日期字符串，默认为今天"""
    if target_date is None:
        target_date = datetime.now().date()
    return target_date.strftime("%Y-%m-%d")


def get_date_range(date_str: str, days: int = 7) -> tuple:
    """获取日期范围"""
    end_dt = datetime.strptime(date_str, "%Y-%m-%d")
    start_dt = end_dt - timedelta(days=days)
    return start_dt, end_dt


# ========== 交易量聚合 ==========

def aggregate_daily_volumes(
    db: Session,
    exchange: str,
    target_date: date
) -> Dict[str, float]:
    """
    聚合指定交易所指定日期的交易量
    
    Returns:
        {
            "total_volume": float,
            "spot_volume": float,
            "futures_volume": float,
        }
    """
    date_str = target_date.strftime("%Y-%m-%d")
    
    # 查询该日期的交易量
    results = db.query(
        models.ExchangeVolumeTimeseries.market_type,
        func.sum(models.ExchangeVolumeTimeseries.volume_usd).label("total")
    ).filter(
        models.ExchangeVolumeTimeseries.exchange == exchange,
        func.date(models.ExchangeVolumeTimeseries.ts) == date_str
    ).group_by(
        models.ExchangeVolumeTimeseries.market_type
    ).all()
    
    volumes = {"total": 0, "spot": 0, "futures": 0}
    for row in results:
        market_type = row.market_type
        if market_type in volumes:
            volumes[market_type] = float(row.total)
    
    # 如果没有 total，计算 spot + futures
    if volumes["total"] == 0:
        volumes["total"] = volumes["spot"] + volumes["futures"]
    
    return volumes


def calculate_volume_change(
    db: Session,
    exchange: str,
    market_type: str,
    target_date: date
) -> float:
    """
    计算交易量变化百分比
    
    Args:
        db: 数据库会话
        exchange: 交易所
        market_type: 市场类型 (spot/futures/total)
        target_date: 目标日期
    
    Returns:
        变化百分比，如 12.5 表示 12.5%
    """
    date_str = target_date.strftime("%Y-%m-%d")
    prev_date = (target_date - timedelta(days=1)).strftime("%Y-%m-%d")
    
    # 获取目标日期和前一天的总量
    current = db.query(
        func.sum(models.ExchangeVolumeTimeseries.volume_usd)
    ).filter(
        models.ExchangeVolumeTimeseries.exchange == exchange,
        models.ExchangeVolumeTimeseries.market_type == market_type,
        func.date(models.ExchangeVolumeTimeseries.ts) == date_str
    ).scalar() or 0
    
    previous = db.query(
        func.sum(models.ExchangeVolumeTimeseries.volume_usd)
    ).filter(
        models.ExchangeVolumeTimeseries.exchange == exchange,
        models.ExchangeVolumeTimeseries.market_type == market_type,
        func.date(models.ExchangeVolumeTimeseries.ts) == prev_date
    ).scalar() or 0
    
    if previous == 0:
        return 0.0
    
    return round(((current - previous) / previous) * 100, 2)


# ========== 事件聚合 ==========

def aggregate_daily_events(
    db: Session,
    exchange: str,
    target_date: date
) -> Dict[str, Any]:
    """
    聚合指定交易所指定日期的事件
    
    Returns:
        {
            "event_count": int,
            "high_risk_event_count": int,
            "events_by_type": {event_type: count},
            "top_events": [list of event dicts],
        }
    """
    date_str = target_date.strftime("%Y-%m-%d")
    
    # 查询该日期的所有事件
    events = db.query(models.ExchangeEvent).filter(
        models.ExchangeEvent.exchange == exchange,
        func.date(models.ExchangeEvent.event_time) == date_str,
        models.ExchangeEvent.is_published == True
    ).order_by(
        models.ExchangeEvent.impact_score.desc()
    ).all()
    
    event_count = len(events)
    high_risk_count = sum(1 for e in events if e.risk_level == "high")
    
    # 按类型统计
    events_by_type = {}
    for e in events:
        if e.event_type not in events_by_type:
            events_by_type[e.event_type] = 0
        events_by_type[e.event_type] += 1
    
    # 取评分最高的3条作为重点事件
    top_events = events[:3] if len(events) > 3 else events
    
    return {
        "event_count": event_count,
        "high_risk_event_count": high_risk_count,
        "events_by_type": events_by_type,
        "top_events": [
            {
                "id": e.id,
                "event_type": e.event_type,
                "title": e.title,
                "event_time": e.event_time.isoformat() if e.event_time else None,
                "risk_level": e.risk_level,
                "impact_score": e.impact_score,
            }
            for e in top_events
        ],
    }


# ========== 生成 Takeaways ==========

def generate_takeaways(
    db: Session,
    target_date: date
) -> List[str]:
    """
    生成今日重点结论
    
    规则:
    1. 找出交易量变化最大的交易所
    2. 找出事件最多的交易所
    3. 找出高风险事件
    """
    takeaways = []
    date_str = target_date.strftime("%Y-%m-%d")
    
    for exchange in SUPPORTED_EXCHANGES:
        # 交易量变化
        try:
            change_pct = calculate_volume_change(db, exchange, "total", target_date)
            if abs(change_pct) > 10:  # 变化超过10%
                direction = "上升" if change_pct > 0 else "下降"
                takeaways.append(
                    f"{exchange.upper()} 今日总量{direction} {abs(change_pct):.1f}%"
                )
        except Exception as e:
            logger.warning(f"Failed to calculate volume change for {exchange}: {e}")
    
    # 事件最多的交易所
    event_counts = {}
    for exchange in SUPPORTED_EXCHANGES:
        count = db.query(models.ExchangeEvent).filter(
            models.ExchangeEvent.exchange == exchange,
            func.date(models.ExchangeEvent.event_time) == date_str,
            models.ExchangeEvent.is_published == True
        ).count()
        if count > 0:
            event_counts[exchange] = count
    
    if event_counts:
        top_exchange = max(event_counts, key=event_counts.get)
        takeaways.append(
            f"{top_exchange.upper()} 今日事件最多 ({event_counts[top_exchange]}条)"
        )
    
    # 高风险事件
    high_risk_events = db.query(models.ExchangeEvent).filter(
        models.ExchangeEvent.risk_level == "high",
        func.date(models.ExchangeEvent.event_time) == date_str,
        models.ExchangeEvent.is_published == True
    ).all()
    
    if high_risk_events:
        takeaways.append(
            f"今日有 {len(high_risk_events)} 条高风险事件需关注"
        )
    
    # 如果没有结论，添加默认结论
    if not takeaways:
        takeaways.append("今日市场平稳，无重大异动")
    
    return takeaways[:5]  # 最多5条


# ========== 找出 Top Movers ==========

def get_top_movers(db: Session, target_date: date) -> Dict[str, Dict]:
    """
    找出各市场类型变化最大的交易所
    
    Returns:
        {
            "total": {"exchange": "binance", "change_pct": 12.5},
            "spot": {"exchange": "okx", "change_pct": 8.3},
            "futures": {"exchange": "bybit", "change_pct": -5.2},
        }
    """
    result = {}
    
    for market_type in ["total", "spot", "futures"]:
        changes = {}
        for exchange in SUPPORTED_EXCHANGES:
            try:
                change = calculate_volume_change(db, exchange, market_type, target_date)
                changes[exchange] = change
            except:
                changes[exchange] = 0
        
        if changes:
            top_exchange = max(changes, key=changes.get)
            result[market_type] = {
                "exchange": top_exchange,
                "change_pct": changes[top_exchange]
            }
        else:
            result[market_type] = {"exchange": None, "change_pct": 0}
    
    return result


# ========== 风险汇总 ==========

def get_risk_summary(db: Session, target_date: date) -> Dict[str, int]:
    """
    获取风险汇总
    
    Returns:
        {
            "high_risk_events": int,
            "wallet_issues": int,
            "compliance_events": int,
        }
    """
    date_str = target_date.strftime("%Y-%m-%d")
    
    high_risk_count = db.query(models.ExchangeEvent).filter(
        models.ExchangeEvent.risk_level == "high",
        func.date(models.ExchangeEvent.event_time) == date_str,
        models.ExchangeEvent.is_published == True
    ).count()
    
    wallet_issue_count = db.query(models.ExchangeEvent).filter(
        models.ExchangeEvent.event_type == "wallet_issue",
        func.date(models.ExchangeEvent.event_time) == date_str,
        models.ExchangeEvent.is_published == True
    ).count()
    
    compliance_count = db.query(models.ExchangeEvent).filter(
        models.ExchangeEvent.event_type == "compliance",
        func.date(models.ExchangeEvent.event_time) == date_str,
        models.ExchangeEvent.is_published == True
    ).count()
    
    return {
        "high_risk_events": high_risk_count,
        "wallet_issues": wallet_issue_count,
        "compliance_events": compliance_count,
    }


# ========== 主函数 ==========

def get_dashboard_summary(db: Session, target_date: Optional[date] = None) -> Dict[str, Any]:
    """
    生成 Dashboard Summary
    
    Returns:
        {
            "date": "2026-03-17",
            "top_takeaways": [...],
            "top_movers": {...},
            "risk_summary": {...},
        }
    """
    if target_date is None:
        target_date = datetime.now().date()
    
    date_str = get_date_str(target_date)
    
    return {
        "date": date_str,
        "top_takeaways": generate_takeaways(db, target_date),
        "top_movers": get_top_movers(db, target_date),
        "risk_summary": get_risk_summary(db, target_date),
    }


def get_exchange_updates(db: Session, target_date: Optional[date] = None) -> List[Dict[str, Any]]:
    """
    生成各交易所每日动态
    
    Returns:
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
                "top_events": [...],
            },
            ...
        ]
    """
    if target_date is None:
        target_date = datetime.now().date()
    
    updates = []
    
    for exchange in SUPPORTED_EXCHANGES:
        # 获取交易量
        volumes = aggregate_daily_volumes(db, exchange, target_date)
        
        # 计算变化
        total_change = calculate_volume_change(db, exchange, "total", target_date)
        spot_change = calculate_volume_change(db, exchange, "spot", target_date)
        futures_change = calculate_volume_change(db, exchange, "futures", target_date)
        
        # 获取事件
        events_data = aggregate_daily_events(db, exchange, target_date)
        
        update = {
            "exchange": exchange,
            "total_volume": volumes["total"],
            "spot_volume": volumes["spot"],
            "futures_volume": volumes["futures"],
            "total_change_pct": total_change,
            "spot_change_pct": spot_change,
            "futures_change_pct": futures_change,
            "event_count": events_data["event_count"],
            "high_risk_event_count": events_data["high_risk_event_count"],
            "top_events": events_data["top_events"],
        }
        
        updates.append(update)
    
    return updates


# ========== 数据写入 (用于定时任务) ==========

def save_daily_snapshot(
    db: Session,
    target_date: Optional[date] = None
) -> None:
    """
    保存每日快照到数据库
    定时任务调用，每日执行一次
    """
    if target_date is None:
        target_date = datetime.now().date()
    
    date_str = get_date_str(target_date)
    
    for exchange in SUPPORTED_EXCHANGES:
        # 获取交易量
        volumes = aggregate_daily_volumes(db, exchange, target_date)
        
        # 计算变化
        total_change = calculate_volume_change(db, exchange, "total", target_date)
        spot_change = calculate_volume_change(db, exchange, "spot", target_date)
        futures_change = calculate_volume_change(db, exchange, "futures", target_date)
        
        # 获取事件统计
        events_data = aggregate_daily_events(db, exchange, target_date)
        
        # 检查是否已存在
        existing = db.query(models.DashboardDailySnapshot).filter(
            models.DashboardDailySnapshot.snapshot_date == date_str,
            models.DashboardDailySnapshot.exchange == exchange
        ).first()
        
        if existing:
            # 更新
            existing.total_volume = volumes["total"]
            existing.spot_volume = volumes["spot"]
            existing.futures_volume = volumes["futures"]
            existing.total_change_pct = total_change
            existing.spot_change_pct = spot_change
            existing.futures_change_pct = futures_change
            existing.event_count = events_data["event_count"]
            existing.high_risk_event_count = events_data["high_risk_event_count"]
        else:
            # 创建
            snapshot = models.DashboardDailySnapshot(
                snapshot_date=date_str,
                exchange=exchange,
                total_volume=volumes["total"],
                spot_volume=volumes["spot"],
                futures_volume=volumes["futures"],
                total_change_pct=total_change,
                spot_change_pct=spot_change,
                futures_change_pct=futures_change,
                event_count=events_data["event_count"],
                high_risk_event_count=events_data["high_risk_event_count"],
            )
            db.add(snapshot)
    
    db.commit()
    logger.info(f"Daily snapshot saved for {date_str}")
