"""
初始化数据库并填充演示数据
支持真实数据填充（使用 --live 参数）
"""
import random
import argparse
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal, init_db
from app.models import models
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 交易所配置
EXCHANGES = ["binance", "okx", "bybit", "bitget", "hyperliquid"]
MARKET_TYPES = ["spot", "futures"]

# 事件数据（包含所有事件类型）
EVENTS_DATA = [
    {"event_time": "2026-03-17 14:00", "event_type": "listing", "exchange": "binance", 
     "title": "Binance 上线 AXL 代币", "summary": "Binance 宣布上线 AXL 代币并开放 USDT 交易对", "importance": 4},
    {"event_time": "2026-03-17 10:30", "event_type": "campaign", "exchange": "bybit",
     "title": "Bybit 合约返现活动", "summary": "Bybit 开启合约交易返现活动，最高返还 50%", "importance": 3},
    {"event_time": "2026-03-17 09:00", "event_type": "fee_change", "exchange": "okx",
     "title": "OKX 调整合约maker费率", "summary": "OKX 宣布下调合约 maker 费率至 0.01%", "importance": 3},
    {"event_time": "2026-03-16 18:00", "event_type": "announcement", "exchange": "okx",
     "title": "OKX 升级风控系统", "summary": "OKX 宣布升级风控系统，新增异常交易监测功能", "importance": 3},
    {"event_time": "2026-03-16 12:00", "event_type": "product_launch", "exchange": "bybit",
     "title": "Bybit Launchpad 2.0 上线", "summary": "Bybit 推出新一代 Launchpad 平台", "importance": 4},
    {"event_time": "2026-03-16 08:00", "event_type": "vip_policy", "exchange": "binance",
     "title": "Binance VIP 政策更新", "summary": "Binance 调整 VIP 等级门槛，新增机构用户特权", "importance": 3},
    {"event_time": "2026-03-15 16:00", "event_type": "listing", "exchange": "okx",
     "title": "OKX 上线 SOL 合约", "summary": "OKX 开放 SOL 永续合约交易，最高 50x 杠杆", "importance": 4},
    {"event_time": "2026-03-15 12:00", "event_type": "delisting", "exchange": "bitget",
     "title": "Bitget 下线 XLM 合约", "summary": "Bitget 宣布下架 XLM 永续合约", "importance": 2},
    {"event_time": "2026-03-15 09:00", "event_type": "social_hype", "exchange": "binance",
     "title": "BTC 突破 85000 引发讨论", "summary": "BTC 价格突破 85000 USDT，社交媒体热议", "importance": 5},
    {"event_time": "2026-03-14 20:00", "event_type": "macro", "exchange": "行业",
     "title": "SEC 通过比特币 ETF 新规", "summary": "SEC 宣布通过比特币 ETF 新的监管框架", "importance": 5},
    {"event_time": "2026-03-14 14:00", "event_type": "campaign", "exchange": "binance",
     "title": "Binance 现货零手续费周", "summary": "Binance 开启现货交易零手续费周活动", "importance": 3},
    {"event_time": "2026-03-14 10:00", "event_type": "compliance", "exchange": "okx",
     "title": "OKX 获得新加坡牌照", "summary": "OKX 获得新加坡数字支付代币服务牌照", "importance": 4},
    {"event_time": "2026-03-13 15:00", "event_type": "partnership", "exchange": "bybit",
     "title": "Bybit 与 Mastercard 合作", "summary": "Bybit 宣布与 Mastercard 合作推出加密卡", "importance": 4},
    {"event_time": "2026-03-13 11:00", "event_type": "announcement", "exchange": "bybit",
     "title": "Bybit 获得迪拜牌照", "summary": "Bybit 获得迪拜 VASP 牌照，可在阿联酋合法运营", "importance": 4},
    {"event_time": "2026-03-12 15:00", "event_type": "listing", "exchange": "bitget",
     "title": "Bitget 上线 ORDI", "summary": "Bitget 开放 ORDI 代币充值", "importance": 3},
    {"event_time": "2026-03-12 10:00", "event_type": "product", "exchange": "hyperliquid",
     "title": "Hyperliquid 更新订单簿", "summary": "Hyperliquid 升级订单簿引擎，提升流动性", "importance": 3},
    {"event_time": "2026-03-11 14:00", "event_type": "wallet_issue", "exchange": "binance",
     "title": "Binance 钱包维护", "summary": "Binance 钱包维护公告，暂停充值提现 2 小时", "importance": 2},
    {"event_time": "2026-03-11 09:00", "event_type": "news", "exchange": "行业",
     "title": "香港批准更多加密平台", "summary": "香港证监会批准更多加密资产交易平台", "importance": 4},
]


def generate_btc_prices(db: Session, hours: int = 168, use_live: bool = False):
    """生成 BTC 价格数据"""
    if use_live:
        # 尝试从真实 API 获取
        try:
            from app.services.btc_service import get_cached_btc_prices
            print("从 AiCoin/CoinGecko/OKX/Hyperliquid 获取真实 BTC 数据...")
            prices = get_cached_btc_prices(hours)
            
            if prices and len(prices) > 0:
                # 清空旧数据
                db.query(models.BtcPrice).delete()
                
                for p in prices:
                    # 获取数据来源
                    source = p.get("source", "okx")
                    btc = models.BtcPrice(
                        timestamp=datetime.strptime(p["ts"], "%Y-%m-%dT%H:%M:%SZ"),
                        price=p["value"],
                        volume_24h=random.uniform(25000000000, 35000000000),
                        source=source
                    )
                    db.add(btc)
                
                db.commit()
                print(f"✅ 已从 API 获取 {len(prices)} 条 BTC 价格数据")
                return
        except Exception as e:
            print(f"获取真实数据失败: {e}，使用模拟数据")
    
    # 模拟数据
    now = datetime.utcnow()
    base_price = 82000
    
    for i in range(hours, 0, -1):
        timestamp = now - timedelta(hours=i)
        # 添加随机波动
        price = base_price + random.uniform(-2000, 2000) + random.gauss(0, 500)
        volume = random.uniform(25000000000, 35000000000)
        
        btc = models.BtcPrice(
            timestamp=timestamp,
            price=round(price, 2),
            volume_24h=volume,
            source="mock"
        )
        db.add(btc)
    
    db.commit()
    print(f"✅ 已生成 {hours} 条 BTC 价格模拟数据")


def generate_volume_data(db: Session, hours: int = 168, use_live: bool = False):
    """生成交易所交易量数据"""
    # 交易量基准配置（USDT，单位：百万）
    volume_config = {
        "binance": {"spot": 25000, "futures": 75000},
        "okx": {"spot": 15000, "futures": 45000},
        "bybit": {"spot": 12000, "futures": 38000},
        "bitget": {"spot": 8000, "futures": 25000},
        "hyperliquid": {"spot": 0, "futures": 20000},
    }
    
    if use_live:
        try:
            from app.services.exchange_service import get_cached_exchange_volumes
            print("从 AiCoin/Hyperliquid 获取真实交易量数据...")
            live_volumes = get_cached_exchange_volumes(24)
            
            # 更新基准配置
            for exchange, volumes in live_volumes.items():
                if exchange in volume_config:
                    if volumes.get("spot", 0) > 0:
                        volume_config[exchange]["spot"] = volumes["spot"] / 1_000_000
                    if volumes.get("futures", 0) > 0:
                        volume_config[exchange]["futures"] = volumes["futures"] / 1_000_000
            
            print(f"✅ 已获取真实交易量数据: {live_volumes}")
        except Exception as e:
            print(f"获取真实交易量失败: {e}，使用模拟数据")
    
    now = datetime.utcnow()
    
    for exchange in EXCHANGES:
        for market_type in MARKET_TYPES:
            base_volume = volume_config.get(exchange, {}).get(market_type, 10000)
            
            for i in range(hours, 0, -1):
                timestamp = now - timedelta(hours=i)
                # 添加随机波动
                volume = base_volume * random.uniform(0.5, 1.5) * 1_000_000  # 转换为 USDT
                
                vol = models.ExchangeVolume(
                    timestamp=timestamp,
                    exchange=exchange,
                    market_type=market_type,
                    volume=round(volume, 2),
                    tx_count=random.randint(10000, 500000),
                    source="mock" if not use_live else "cmc+hyperliquid"
                )
                db.add(vol)
    
    db.commit()
    print(f"✅ 已生成 {hours} x {len(EXCHANGES)} x {len(MARKET_TYPES)} 条交易量数据")


def generate_events(db: Session):
    """生成事件数据"""
    for event_data in EVENTS_DATA:
        event = models.StructuredEvent(
            event_time=datetime.strptime(event_data["event_time"], "%Y-%m-%d %H:%M"),
            event_type=event_data["event_type"],
            exchange=event_data["exchange"],
            title=event_data["title"],
            summary=event_data["summary"],
            importance=event_data["importance"],
            is_published=True
        )
        db.add(event)
    
    db.commit()
    print(f"✅ 已生成 {len(EVENTS_DATA)} 条事件数据")


def seed_database(use_live: bool = False, hours: int = 168):
    """填充数据库"""
    print(f"初始化数据库 (use_live={use_live}, hours={hours})...")
    init_db()
    
    db = SessionLocal()
    try:
        # 清空现有数据
        print("清空现有数据...")
        db.query(models.BtcPrice).delete()
        db.query(models.ExchangeVolume).delete()
        db.query(models.StructuredEvent).delete()
        db.commit()
        
        # 生成新数据
        generate_btc_prices(db, hours, use_live)
        generate_volume_data(db, hours, use_live)
        generate_events(db)
        
        print("🎉 数据库填充完成!")
        
    except Exception as e:
        print(f"❌ 填充数据库失败: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="初始化 Exchange Monitor 数据库")
    parser.add_argument("--live", action="store_true", help="使用真实 API 数据填充")
    parser.add_argument("--hours", type=int, default=168, help="生成多少小时的数据（默认168小时=7天）")
    
    args = parser.parse_args()
    
    seed_database(use_live=args.live, hours=args.hours)
