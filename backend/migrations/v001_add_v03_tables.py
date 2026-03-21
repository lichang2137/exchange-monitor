"""
数据库迁移脚本 v0.3
将新的数据表添加到已存在的 SQLite 数据库

使用方法:
    cd backend
    python -m migrations.v001_add_v03_tables

执行前会:
1. 检查数据库是否存在
2. 创建新的数据表
3. 不影响现有数据
"""

import sys
import os

# 添加 backend 目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, Base
from app.models import models


def run_migration():
    """执行迁移"""
    print("=" * 50)
    print("Exchange Monitor v0.3 数据库迁移")
    print("=" * 50)
    
    # 检查数据库文件是否存在
    db_path = "./exchange_monitor.db"
    if os.path.exists(db_path):
        size = os.path.getsize(db_path)
        print(f"✅ 发现现有数据库: {db_path} ({size} bytes)")
    else:
        print(f"📝 数据库不存在，将创建新数据库")
    
    print("\n📦 创建新数据表...")
    
    # 创建所有新表
    new_tables = [
        models.ExchangeVolumeTimeseries,
        models.ExchangeEvent,
        models.DashboardDailySnapshot,
        models.NewsItem,
        models.InsightSummary,
    ]
    
    for table_class in new_tables:
        table_name = table_class.__tablename__
        try:
            table_class.__table__.create(bind=engine, checkfirst=True)
            print(f"  ✅ {table_name}")
        except Exception as e:
            print(f"  ❌ {table_name}: {e}")
    
    print("\n✅ 迁移完成!")
    print("\n新增表结构:")
    print("  - exchange_volume_timeseries: 交易量时间序列")
    print("  - exchange_events: 结构化事件")
    print("  - dashboard_daily_snapshots: 每日快照")
    print("  - news_items: 新闻条目")
    print("  - insight_summaries: 摘要")


if __name__ == "__main__":
    run_migration()
