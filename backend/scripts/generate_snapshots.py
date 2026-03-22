#!/usr/bin/env python3
"""
生成 Dashboard 每日快照
从 exchange_volume + btc_price_history 聚合每日快照
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models import models

EXCHANGES = ["binance", "okx", "bybit", "bitget", "hyperliquid"]


def generate_snapshots(days: int = 30):
    """生成最近N天的每日快照"""
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        cutoff = now - timedelta(days=days)

        # 1. 获取所有有数据的日期
        dates = set()
        vol_records = db.query(models.ExchangeVolume).filter(
            models.ExchangeVolume.timestamp >= cutoff
        ).all()
        for r in vol_records:
            dates.add(r.timestamp.strftime("%Y-%m-%d"))

        for date_str in sorted(dates):
            for exchange in EXCHANGES:
                # 查询该日该所 spot + futures
                day_start = datetime.strptime(date_str, "%Y-%m-%d")

                # Spot — 用日期字符串匹配（因为原始数据有不同小时）
                spot_rows = db.query(models.ExchangeVolume).filter(
                    models.ExchangeVolume.exchange == exchange,
                    models.ExchangeVolume.market_type == "spot"
                ).order_by(models.ExchangeVolume.timestamp).all()
                # 取当日第一个有效值
                spot_vol = 0
                for s in spot_rows:
                    if s.timestamp.strftime("%Y-%m-%d") == date_str:
                        spot_vol = s.volume
                        break

                # Futures
                fut_rows = db.query(models.ExchangeVolume).filter(
                    models.ExchangeVolume.exchange == exchange,
                    models.ExchangeVolume.market_type == "futures"
                ).order_by(models.ExchangeVolume.timestamp).all()
                fut_vol = 0
                for f in fut_rows:
                    if f.timestamp.strftime("%Y-%m-%d") == date_str:
                        fut_vol = f.volume
                        break

                total_vol = spot_vol + fut_vol

                # event count
                event_count = db.query(models.ExchangeEvent).filter(
                    models.ExchangeEvent.event_time >= day_start,
                    models.ExchangeEvent.event_time < day_start + timedelta(days=1),
                    models.ExchangeEvent.exchange == exchange
                ).count()

                # high risk
                high_risk = db.query(models.ExchangeEvent).filter(
                    models.ExchangeEvent.event_time >= day_start,
                    models.ExchangeEvent.event_time < day_start + timedelta(days=1),
                    models.ExchangeEvent.exchange == exchange,
                    models.ExchangeEvent.risk_level == "high"
                ).count()

                # Upsert
                existing = db.query(models.DashboardDailySnapshot).filter(
                    models.DashboardDailySnapshot.snapshot_date == date_str,
                    models.DashboardDailySnapshot.exchange == exchange
                ).first()

                if existing:
                    existing.spot_volume = spot_vol
                    existing.futures_volume = fut_vol
                    existing.total_volume = total_vol
                    existing.event_count = event_count
                    existing.high_risk_event_count = high_risk
                    existing.updated_at = datetime.utcnow()
                else:
                    snap = models.DashboardDailySnapshot(
                        snapshot_date=date_str,
                        exchange=exchange,
                        total_volume=total_vol,
                        spot_volume=spot_vol,
                        futures_volume=fut_vol,
                        event_count=event_count,
                        high_risk_event_count=high_risk,
                    )
                    db.add(snap)

        db.commit()

        # 输出统计
        total = db.query(models.DashboardDailySnapshot).count()
        print(f"✅ 快照生成完成，共 {total} 条记录")

        # 按交易所统计
        for ex in EXCHANGES:
            cnt = db.query(models.DashboardDailySnapshot).filter(
                models.DashboardDailySnapshot.exchange == ex
            ).count()
            print(f"  {ex}: {cnt} 条")

    finally:
        db.close()


if __name__ == "__main__":
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    generate_snapshots(days)
