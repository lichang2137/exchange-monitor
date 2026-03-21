"""
Dashboard Router
提供 Dashboard 摘要和交易所每日动态 API

Endpoints:
- GET /api/dashboard/summary
- GET /api/dashboard/exchange-updates
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime, date

from app.database import get_db
from app.services.dashboard_service import (
    get_dashboard_summary,
    get_exchange_updates,
)

router = APIRouter()


@router.get("/summary")
def get_summary(
    date: Optional[str] = Query(None, description="日期 YYYY-MM-DD，默认今日"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取 Dashboard 摘要
    
    返回今日重点结论、交易量变化最大的交易所、风险汇总
    """
    target_date = None
    if date:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            pass  # 使用默认日期
    
    return get_dashboard_summary(db, target_date)


@router.get("/exchange-updates")
def get_exchanges(
    date: Optional[str] = Query(None, description="日期 YYYY-MM-DD，默认今日"),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    获取各交易所每日动态
    
    返回各交易所的交易量、变化百分比、事件统计和重点事件
    """
    target_date = None
    if date:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            pass  # 使用默认日期
    
    return get_exchange_updates(db, target_date)
