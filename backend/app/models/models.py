from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, Index
from sqlalchemy.sql import func
from app.database import Base


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
