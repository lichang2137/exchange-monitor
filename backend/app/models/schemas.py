from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


# ========== Response Models ==========

class BtcResponse(BaseModel):
    """BTC 价格响应 (新格式)"""
    ts: str  # ISO 格式时间
    value: float


class VolumeResponse(BaseModel):
    """交易量响应 (新格式)"""
    ts: str
    exchange: str
    market_type: str
    value: float


class ChartEventResponse(BaseModel):
    """图表事件响应 (新格式)"""
    id: str
    ts: str
    exchange: str
    event_type: str
    title: str


class ChartDataResponseV2(BaseModel):
    """图表数据响应 v2"""
    btc: List[BtcResponse]
    volumes: List[VolumeResponse]
    events: List[ChartEventResponse]


class EventListItem(BaseModel):
    """事件列表项 (新格式)"""
    id: str
    ts: str
    exchange: str
    event_type: str
    title: str
    summary: Optional[str] = None
    source: Optional[str] = None
    url: Optional[str] = None


class EventsListResponse(BaseModel):
    """事件列表响应 v2"""
    events: List[EventListItem]
    total: int


class ExchangeInfo(BaseModel):
    """交易所信息"""
    id: str
    name: str
    color: str


class FiltersResponse(BaseModel):
    """筛选器选项响应"""
    market_types: List[dict]
    event_types: List[dict]


# ========== Legacy Models (兼容旧版) ==========

class BtcPriceResponse(BaseModel):
    """BTC 价格响应 (旧格式)"""
    timestamp: datetime
    price: float
    volume_24h: Optional[float] = None
    source: str


class ExchangeVolumeResponse(BaseModel):
    """交易所交易量响应 (旧格式)"""
    timestamp: datetime
    exchange: str
    market_type: str
    volume: float


class ChartDataResponse(BaseModel):
    """图表数据响应 (旧格式)"""
    btc_prices: List[BtcPriceResponse]
    volumes: List[ExchangeVolumeResponse]


class EventResponse(BaseModel):
    """事件响应 (旧格式)"""
    id: int
    event_time: datetime
    event_type: str
    exchange: str
    title: str
    summary: Optional[str] = None
    content: Optional[str] = None
    importance: int
    
    class Config:
        from_attributes = True


class EventsResponse(BaseModel):
    """事件列表响应 (旧格式)"""
    events: List[EventResponse]
    total: int
