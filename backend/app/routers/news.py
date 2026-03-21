"""
News Router
提供市场动态、热点新闻、宏观事件 API

Endpoints:
- GET /api/news
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json

from app.database import get_db
from app.models import models

router = APIRouter()

# 默认时间范围
DEFAULT_RANGE_DAYS = 7
MAX_RANGE_DAYS = 30


def parse_news_type(news_type: Optional[str]) -> Optional[List[str]]:
    """解析 news_type 参数"""
    if not news_type:
        return None
    return [t.strip() for t in news_type.split(",")]


def news_to_dict(news: models.NewsItem) -> Dict[str, Any]:
    """将 NewsItem 模型转换为字典"""
    return {
        "id": news.id,
        "published_at": news.published_at.isoformat() if news.published_at else None,
        "news_type": news.news_type,
        "title": news.title,
        "summary": news.summary,
        "source": news.source,
        "source_url": news.source_url,
        "tags": json.loads(news.tags) if news.tags else [],
        "related_exchanges": json.loads(news.related_exchanges) if news.related_exchanges else [],
        "related_symbols": json.loads(news.related_symbols) if news.related_symbols else [],
        "importance_score": news.importance_score or 0,
    }


@router.get("/news", response_model=List[Dict[str, Any]])
def get_news(
    news_type: Optional[str] = Query(None, description="类型：market/macro/industry/hot，多个用逗号分隔"),
    range: Optional[str] = Query("7d", description="时间范围：7d / 30d"),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    返回市场动态、热点新闻、宏观事件
    
    - 按发布时间倒序排列
    - 支持按类型筛选
    - 支持按时间范围筛选
    """
    # 解析时间范围
    range_days = DEFAULT_RANGE_DAYS
    if range:
        range_str = range.lower().rstrip("d")
        try:
            range_days = min(int(range_str), MAX_RANGE_DAYS)
        except ValueError:
            range_days = DEFAULT_RANGE_DAYS
    
    # 计算时间边界
    start_time = datetime.now() - timedelta(days=range_days)
    
    # 构建查询
    query = db.query(models.NewsItem).filter(
        models.NewsItem.published_at >= start_time,
        models.NewsItem.is_published == True
    )
    
    # 解析类型筛选
    type_list = parse_news_type(news_type)
    if type_list:
        query = query.filter(models.NewsItem.news_type.in_(type_list))
    
    # 按发布时间倒序
    news_list = query.order_by(
        desc(models.NewsItem.published_at)
    ).limit(100).all()
    
    return [news_to_dict(n) for n in news_list]
