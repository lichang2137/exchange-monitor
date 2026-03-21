"""
Exchange Volume 数据填充脚本
从各交易所 API 获取真实交易量数据，存入数据库

使用方式:
    cd backend
    source venv/bin/activate
    python -m scripts.seed_exchange_volume
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import models


# 交易所配置
EXCHANGES = ["binance", "okx", "bybit", "hyperliquid"]
MARKET_TYPES = ["spot", "futures"]


def fetch_binance_volume() -> dict:
    """从 Binance 获取真实交易量"""
    try:
        spot_resp = requests.get(
            "https://api.binance.com/api/v3/ticker/24hr",
            params={"symbol": "BTCUSDT"},
            timeout=10
        )
        spot_data = spot_resp.json()
        spot_volume = float(spot_data.get("quoteVolume", 0))
        
        # 合约
        try:
            futures_resp = requests.get(
                "https://fapi.binance.com/fapi/v1/ticker/24hr",
                params={"symbol": "BTCUSDT"},
                timeout=10
            )
            if futures_resp.status_code == 200:
                futures_data = futures_resp.json()
                futures_volume = float(futures_data.get("quoteVolume", 0))
            else:
                futures_volume = spot_volume * 4
        except:
            futures_volume = spot_volume * 4
        
        return {"spot": spot_volume, "futures": futures_volume}
    except Exception as e:
        print(f"  Binance API failed: {e}")
        return {"spot": 0, "futures": 0}


def fetch_okx_volume() -> dict:
    """从 OKX 获取真实交易量"""
    try:
        result = {"spot": 0, "futures": 0}
        
        # 现货
        spot_resp = requests.get(
            "https://www.okx.com/api/v5/market/ticker",
            params={"instId": "BTC-USDT"},
            timeout=10
        )
        if spot_resp.status_code == 200:
            data = spot_resp.json()
            if data.get("code") == "0":
                result["spot"] = float(data["data"][0].get("volCcy24h", 0))
        
        # 永续合约
        perp_resp = requests.get(
            "https://www.okx.com/api/v5/market/ticker",
            params={"instId": "BTC-USDT-SWAP"},
            timeout=10
        )
        if perp_resp.status_code == 200:
            data = perp_resp.json()
            if data.get("code") == "0":
                vol_btc = float(data["data"][0].get("volCcy24h", 0))
                last_px = float(data["data"][0].get("last", 0))
                result["futures"] = vol_btc * last_px
        
        return result
    except Exception as e:
        print(f"  OKX API failed: {e}")
        return {"spot": 0, "futures": 0}


def fetch_bybit_volume() -> dict:
    """从 Bybit 获取真实交易量"""
    try:
        result = {"spot": 0, "futures": 0}
        
        # 现货
        spot_resp = requests.get(
            "https://api.bybit.com/v5/market/tickers",
            params={"category": "spot", "symbol": "BTCUSDT"},
            timeout=10
        )
        if spot_resp.status_code == 200:
            data = spot_resp.json()
            if data.get("retCode") == 0:
                result["spot"] = float(data["result"]["list"][0].get("turnover24h", 0))
        
        # 永续合约
        perp_resp = requests.get(
            "https://api.bybit.com/v5/market/tickers",
            params={"category": "linear", "symbol": "BTCUSDT"},
            timeout=10
        )
        if perp_resp.status_code == 200:
            data = perp_resp.json()
            if data.get("retCode") == 0:
                result["futures"] = float(data["result"]["list"][0].get("turnover24h", 0))
        
        return result
    except Exception as e:
        print(f"  Bybit API failed: {e}")
        return {"spot": 0, "futures": 0}


def fetch_hyperliquid_volume() -> dict:
    """从 Hyperliquid 获取真实交易量"""
    try:
        url = "https://api.hyperliquid.xyz/info"
        headers = {"Content-Type": "application/json"}
        
        resp = requests.post(
            url, 
            json={"type": "metaAndAssetCtxs"},
            headers=headers,
            timeout=10
        )
        data = resp.json()
        
        total_volume = 0
        if len(data) > 1:
            for ctx in data[1]:
                day_volume = float(ctx.get("dayNtlVlm", 0))
                total_volume += day_volume
        
        return {"spot": 0, "futures": total_volume}
    except Exception as e:
        print(f"  Hyperliquid API failed: {e}")
        return {"spot": 0, "futures": 0}


def seed_realtime(db: Session, hours: int = 24):
    """获取最新交易量数据并写入数据库"""
    print(f"获取最近 {hours} 小时交易量数据...")
    
    fetchers = {
        "binance": fetch_binance_volume,
        "okx": fetch_okx_volume,
        "bybit": fetch_bybit_volume,
        "hyperliquid": fetch_hyperliquid_volume,
    }
    
    now = datetime.utcnow()
    
    for exchange, fetcher in fetchers.items():
        print(f"  获取 {exchange} 数据...")
        volumes = fetcher()
        
        for market_type in ["spot", "futures"]:
            volume = volumes.get(market_type, 0)
            if volume > 0:
                # 检查是否已存在
                existing = db.query(models.ExchangeVolumeTimeseries).filter(
                    models.ExchangeVolumeTimeseries.exchange == exchange,
                    models.ExchangeVolumeTimeseries.market_type == market_type
                ).first()
                
                if existing:
                    existing.volume_usd = volume
                    existing.ts = now
                    print(f"    {exchange} {market_type}: 更新 ${volume:,.0f}")
                else:
                    record = models.ExchangeVolumeTimeseries(
                        ts=now,
                        exchange=exchange,
                        market_type=market_type,
                        volume_usd=volume,
                        source="api"
                    )
                    db.add(record)
                    print(f"    {exchange} {market_type}: 新增 ${volume:,.0f}")
    
    db.commit()
    print("✅ 实时数据写入完成")


def seed_historical(db: Session, days: int = 7):
    """基于当前数据生成历史模拟数据（用于演示）"""
    print(f"生成 {days} 天历史模拟数据...")
    
    now = datetime.utcnow()
    
    # 当前真实数据
    current_volumes = {}
    fetchers = {
        "binance": fetch_binance_volume,
        "okx": fetch_okx_volume,
        "bybit": fetch_bybit_volume,
        "hyperliquid": fetch_hyperliquid_volume,
    }
    
    for exchange, fetcher in fetchers.items():
        print(f"  获取 {exchange} 当前数据...")
        try:
            current_volumes[exchange] = fetcher()
        except:
            current_volumes[exchange] = {"spot": 0, "futures": 0}
    
    for exchange in EXCHANGES:
        base_vol = current_volumes.get(exchange, {"spot": 1000000000, "futures": 5000000000})
        
        for day_offset in range(days, 0, -1):
            date = now - timedelta(days=day_offset)
            
            # 每天生成多条记录（每小时一条）
            for hour in range(24):
                ts = date + timedelta(hours=hour)
                
                for market_type in ["spot", "futures"]:
                    base = base_vol.get(market_type, 0)
                    if base == 0:
                        continue
                    
                    # 添加随机波动 ±20%
                    import random
                    factor = 1 + random.uniform(-0.2, 0.2)
                    volume = base * factor * (1 - day_offset * 0.01)  # 递减模拟增长
                    
                    record = models.ExchangeVolumeTimeseries(
                        ts=ts,
                        exchange=exchange,
                        market_type=market_type,
                        volume_usd=volume,
                        source="simulated"
                    )
                    db.add(record)
        
        print(f"  {exchange}: 已生成 {days * 24} 条记录")
    
    db.commit()
    print("✅ 历史模拟数据写入完成")


def main():
    print("=" * 50)
    print("Exchange Volume 数据填充")
    print("=" * 50)
    
    db = SessionLocal()
    
    try:
        # 1. 写入当前实时数据
        seed_realtime(db, hours=1)
        
        # 2. 生成历史模拟数据（最近7天）
        seed_historical(db, days=7)
        
        # 验证
        print("\n验证数据:")
        total_records = db.query(models.ExchangeVolumeTimeseries).count()
        print(f"  总记录数: {total_records}")
        
        for exchange in EXCHANGES:
            count = db.query(models.ExchangeVolumeTimeseries).filter(
                models.ExchangeVolumeTimeseries.exchange == exchange
            ).count()
            print(f"  {exchange}: {count} 条")
        
    finally:
        db.close()
    
    print("\n✅ 数据填充完成!")


if __name__ == "__main__":
    main()
