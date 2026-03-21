from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, Index, JSON
from sqlalchemy.sql import func
from app.database import Base


# ========== 现有模型 ==========

class BtcPrice(Base):
    """BTC 价格历史"""
    __tablename__ = "btc_price_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    price = Column(Float, nullable=False)
    volume_24h = Column(Float, default=0)
    source = Column(String(20), default="binance")
    created_at = Column(DateTime, server_default=func.now())
    
    __table_args__ = (
        Index('idx_btc_timestamp', 'timestamp'),
    )


class ExchangeVolume(Base):
    """交易所交易量"""
    __tablename__ = "exchange_volume"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    exchange = Column(String(20), nullable=False, index=True)
    market_type = Column(String(10), nullable=False)  # spot/futures/total
    volume = Column(Float, nullable=False)
    tx_count = Column(Integer, default=0)
    source = Column(String(20), default="api")
    created_at = Column(DateTime, server_default=func.now())
    
    __table_args__ = (
        Index('idx_vol_composite', 'exchange', 'market_type', 'timestamp'),
    )


class RawEvent(Base):
    """原始事件（采集用）"""
    __tablename__ = "raw_events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_time = Column(DateTime, nullable=False, index=True)
    source = Column(String(50))
    raw_title = Column(Text)
    raw_content = Column(Text)
    raw_url = Column(String(500))
    exchange = Column(String(20), index=True)
    event_type = Column(String(20), index=True)
    status = Column(String(20), default="pending", index=True)
    created_at = Column(DateTime, server_default=func.now())
    processed_at = Column(DateTime, nullable=True)


class StructuredEvent(Base):
    """结构化事件（展示用）"""
    __tablename__ = "structured_events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    raw_event_id = Column(Integer, nullable=True)
    event_time = Column(DateTime, nullable=False, index=True)
    event_type = Column(String(20), nullable=False, index=True)
    exchange = Column(String(20), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    summary = Column(Text)
    content = Column(Text)
    source_url = Column(String(500))
    importance = Column(Integer, default=3)  # 1-5
    is_published = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_struct_published_time', 'is_published', 'event_time'),
    )


# ========== v0.3 新增模型 ==========

class ExchangeVolumeTimeseries(Base):
    """
    交易所业务线交易量时间序列
    存储每日/每小时汇总的交易量数据
    """
    __tablename__ = "exchange_volume_timeseries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ts = Column(DateTime, nullable=False, index=True)
    exchange = Column(String(20), nullable=False)
    market_type = Column(String(10), nullable=False)  # total / spot / futures
    volume_usd = Column(Float, nullable=False)
    source = Column(String(50), default="api")
    created_at = Column(DateTime, server_default=func.now())
    
    __table_args__ = (
        Index('idx_vol_ts', 'ts'),
        Index('idx_exchange_market_ts', 'exchange', 'market_type', 'ts'),
    )


class ExchangeEvent(Base):
    """
    结构化后的交易所事件
    替代旧的 StructuredEvent，支持更丰富的字段
    """
    __tablename__ = "exchange_events"
    
    id = Column(String(50), primary_key=True)  # 如: evt_001
    event_time = Column(DateTime, nullable=False, index=True)
    exchange = Column(String(20), nullable=False, index=True)
    event_type = Column(String(30), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    summary = Column(Text)
    source = Column(String(50))
    source_url = Column(String(500))
    risk_level = Column(String(10))  # low / medium / high
    related_market_type = Column(String(10))  # spot / futures / total
    related_symbols = Column(Text)  # JSON array string
    tags = Column(Text)  # JSON array string
    impact_score = Column(Integer, default=0)  # 0-100
    is_published = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_event_time', 'event_time'),
        Index('idx_exchange_event', 'exchange', 'event_type'),
        Index('idx_risk_level', 'risk_level'),
    )


class DashboardDailySnapshot(Base):
    """
    Dashboard 每日快照
    用于摘要和每日动态
    """
    __tablename__ = "dashboard_daily_snapshots"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_date = Column(String(10), nullable=False)  # YYYY-MM-DD
    exchange = Column(String(20), nullable=False)
    total_volume = Column(Float, default=0)
    spot_volume = Column(Float, default=0)
    futures_volume = Column(Float, default=0)
    total_change_pct = Column(Float, default=0)
    spot_change_pct = Column(Float, default=0)
    futures_change_pct = Column(Float, default=0)
    event_count = Column(Integer, default=0)
    high_risk_event_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_date_exchange', 'snapshot_date', 'exchange', unique=True),
    )


class NewsItem(Base):
    """
    市场动态、热点新闻、宏观事件
    """
    __tablename__ = "news_items"
    
    id = Column(String(50), primary_key=True)  # 如: news_001
    published_at = Column(DateTime, nullable=False, index=True)
    news_type = Column(String(20), nullable=False, index=True)  # market / macro / industry / hot
    title = Column(String(200), nullable=False)
    summary = Column(Text)
    source = Column(String(50))
    source_url = Column(String(500))
    tags = Column(Text)  # JSON array string
    related_exchanges = Column(Text)  # JSON array string
    related_symbols = Column(Text)  # JSON array string
    importance_score = Column(Integer, default=0)  # 0-100
    is_published = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_published_at', 'published_at'),
        Index('idx_news_type', 'news_type'),
    )


class InsightSummary(Base):
    """
    Insight 摘要
    可选，支持规则生成或 AI 生成
    """
    __tablename__ = "insight_summaries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    summary_date = Column(String(10), nullable=False)  # YYYY-MM-DD
    summary_type = Column(String(10), nullable=False)  # daily / hourly
    title = Column(String(200))
    content = Column(Text)
    related_exchanges = Column(Text)  # JSON array string
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_summary_date_type', 'summary_date', 'summary_type'),
    )
