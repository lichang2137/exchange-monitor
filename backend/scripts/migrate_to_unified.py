#!/usr/bin/env python3
"""
迁移脚本：将 btc_price_history 和 exchange_volume_timeseries 的数据
迁移到统一的 time_series_metrics 表。

幂等性：先删除已迁移数据，再重新迁移（避免重复）。
"""
import sys
import os

# 添加 backend 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.models import BtcPrice, ExchangeVolumeTimeseries, TimeSeriesMetric
from datetime import datetime

DATABASE_URL = "sqlite:///./exchange_monitor.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def migrate(delete_first: bool = True):
    """
    执行迁移。

    Args:
        delete_first: 是否先删除已迁移数据（幂等保证）
    """
    db = SessionLocal()
    try:
        print(f"[{datetime.now().isoformat()}] 开始迁移到 time_series_metrics...")

        # ========== 1. 迁移 btc_price_history -> time_series_metrics (price) ==========
        if delete_first:
            deleted = db.query(TimeSeriesMetric).filter(
                TimeSeriesMetric.metric_type == "price"
            ).delete(synchronize_session=False)
            print(f"  [price] 删除已迁移数据: {deleted} 条")

        btc_records = db.query(BtcPrice).all()
        price_objects = []
        for r in btc_records:
            price_objects.append(TimeSeriesMetric(
                timestamp=r.timestamp,
                metric_type="price",
                exchange=r.source or "binance",
                market_type="total",
                symbol="BTC",
                value=r.price,
                source=f"migrated_from_btc_price_history:{r.source or 'binance'}"
            ))

        if price_objects:
            db.bulk_save_objects(price_objects)
            print(f"  [price] 迁移 btc_price_history: {len(price_objects)} 条")

        # ========== 2. 迁移 exchange_volume_timeseries -> time_series_metrics (volume) ==========
        if delete_first:
            deleted = db.query(TimeSeriesMetric).filter(
                TimeSeriesMetric.metric_type == "volume"
            ).delete(synchronize_session=False)
            print(f"  [volume] 删除已迁移数据: {deleted} 条")

        vol_records = db.query(ExchangeVolumeTimeseries).all()
        volume_objects = []
        for r in vol_records:
            volume_objects.append(TimeSeriesMetric(
                timestamp=r.ts,
                metric_type="volume",
                exchange=r.exchange,
                market_type=r.market_type,
                symbol="BTC",
                value=r.volume_usd,
                source=f"migrated_from_exchange_volume_timeseries:{r.source or 'api'}"
            ))

        if volume_objects:
            db.bulk_save_objects(volume_objects)
            print(f"  [volume] 迁移 exchange_volume_timeseries: {len(volume_objects)} 条")

        db.commit()

        # ========== 验证统计 ==========
        total_count = db.query(TimeSeriesMetric).count()
        price_count = db.query(TimeSeriesMetric).filter(TimeSeriesMetric.metric_type == "price").count()
        volume_count = db.query(TimeSeriesMetric).filter(TimeSeriesMetric.metric_type == "volume").count()
        print(f"\n迁移完成！time_series_metrics 表统计:")
        print(f"  总记录数: {total_count}")
        print(f"  price:    {price_count}")
        print(f"  volume:   {volume_count}")

    except Exception as e:
        db.rollback()
        print(f"迁移失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    # 切换到 backend 目录（数据库文件所在目录）
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    migrate(delete_first=True)
