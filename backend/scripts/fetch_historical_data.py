#!/usr/bin/env python3
"""
Exchange Monitor - 真实数据采集脚本 v2
从各交易所真实 API 获取最新数据，写入数据库
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import subprocess
import re
import time
from datetime import datetime
from app.database import SessionLocal
from app.models import models


# ============================================================
# BTC 价格
# ============================================================
def fetch_btc_price() -> dict:
    """从 OKX REST API 获取 BTC 当前价格"""
    try:
        resp = requests.get(
            "https://www.okx.com/api/v5/market/ticker",
            params={"instId": "BTC-USDT"},
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
                "Referer": "https://www.okx.com/",
            },
            timeout=15
        )
        if resp.status_code == 200:
            d = resp.json()
            data = d.get("data", [{}])[0]
            return {
                "price": float(data.get("last", 0)),
                "source": "okx_rest"
            }
    except Exception as e:
        print(f"  OKX REST failed: {e}")
    
    # Fallback: CoinGecko
    try:
        resp = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "bitcoin", "vs_currencies": "usd"},
            timeout=10
        )
        if resp.status_code == 200:
            return {"price": resp.json()["bitcoin"]["usd"], "source": "coingecko"}
    except:
        pass
    
    return {"price": 0, "source": "none"}


# ============================================================
# OKX REST API（现货）
# ============================================================
def fetch_okx_spot() -> float:
    """OKX REST API: BTC-USDT 现货 24h 成交额（USD）
    
    OKX BTC-USDT:
    - instId: BTC-USDT
    - volCcy24h: 成交量（BTC 数量）
    - last: 最新价格（USDT）
    - USD volume = volCcy24h × last
    """
    try:
        resp = requests.get(
            "https://www.okx.com/api/v5/market/ticker",
            params={"instId": "BTC-USDT"},
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
                "Referer": "https://www.okx.com/",
            },
            timeout=15
        )
        if resp.status_code == 200:
            d = resp.json()
            data = d.get("data", [{}])[0]
            # volCcy24h: 成交量（以计价货币计，USD 单位，直接就是 USD 成交额）
            # vol24h: 成交量（以基准货币计，BTC 单位）
            return float(data.get("volCcy24h", 0))  # 直接是 USD 成交额
    except Exception as e:
        print(f"  OKX spot failed: {e}")
    return 0.0


# ============================================================
# OKX REST API（合约）
# ============================================================
def fetch_okx_swap() -> float:
    """OKX REST API: BTC-USDT-SWAP (正向/USDT保证金) 24h 成交额（USD）
    
    OKX BTC-USDT-SWAP:
    - instId: BTC-USDT-SWAP (正向/USDT保证金)
    - contractVal: 0.01 BTC / contract
    - vol24h: 成交量（以张计）
    - USD volume = vol24h × contractVal × last_price
    """
    try:
        resp = requests.get(
            "https://www.okx.com/api/v5/market/ticker",
            params={"instId": "BTC-USDT-SWAP"},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15
        )
        if resp.status_code == 200:
            d = resp.json()
            data = d.get("data", [{}])[0]
            vol_contracts = float(data.get("vol24h", 0))  # contracts
            contract_val_btc = 0.01  # 0.01 BTC per contract (正向/USDT保证金)
            last = float(data.get("last", 0))
            return vol_contracts * contract_val_btc * last  # USD volume
    except Exception as e:
        print(f"  OKX swap (BTC-USDT-SWAP) failed: {e}")
    return 0.0


# ============================================================
# Binance
# ============================================================
def fetch_binance() -> dict:
    """Binance 现货 + 合约 24h 成交额（USD）"""
    headers = {"Accept": "application/json"}
    
    spot = fut = 0.0
    
    # 现货
    try:
        resp = requests.get(
            "https://api.binance.com/api/v3/ticker/24hr",
            params={"symbol": "BTCUSDT"},
            headers=headers, timeout=10
        )
        if resp.status_code == 200:
            spot = float(resp.json().get("quoteVolume", 0))
    except Exception as e:
        print(f"  Binance spot failed: {e}")
    
    # 合约
    try:
        resp = requests.get(
            "https://fapi.binance.com/fapi/v1/ticker/24hr",
            params={"symbol": "BTCUSDT"},
            timeout=10
        )
        if resp.status_code == 200:
            fut = float(resp.json().get("quoteVolume", 0))
    except Exception as e:
        print(f"  Binance futures failed: {e}")
    
    return {"spot": spot, "futures": fut}


# ============================================================
# Bybit
# ============================================================
def fetch_bybit() -> dict:
    """Bybit 现货 + 合约 24h 成交额（USD）"""
    headers = {"Accept": "application/json"}
    
    spot = fut = 0.0
    
    def get_vol(category, symbol):
        try:
            resp = requests.get(
                "https://api.bybit.com/v5/market/tickers",
                params={"category": category, "symbol": symbol},
                headers=headers, timeout=10
            )
            if resp.status_code == 200:
                d = resp.json()
                if d.get("retCode") == 0:
                    data = d.get("result", {}).get("list", [])
                    if data:
                        return float(data[0].get("turnover24h", 0))
        except Exception as e:
            print(f"  Bybit {category} failed: {e}")
        return 0.0
    
    spot = get_vol("spot", "BTCUSDT")
    fut = get_vol("linear", "BTCUSDT")
    return {"spot": spot, "futures": fut}


# ============================================================
# Hyperliquid
# ============================================================
def fetch_hyperliquid() -> float:
    """Hyperliquid 全所 BTC 合约 24h 成交量（USD）
    
    API: POST /info {type: "candleSnapshot", req: {coin: "BTC", interval: "1d", startTime}}
    返回格式: [{"t":..,"o":"..","c":"..","v":"..BTC量},...]
    
    字段说明:
    - v: BTC 成交量（注意是 BTC 数量，不是 USD）
    - o, c: 开盘/收盘价（USDC）
    - USD成交额 = v × (o + c) / 2
    """
    try:
        import time
        now_ms = int(time.time() * 1000)
        start_ms = now_ms - 2 * 24 * 60 * 60 * 1000  # 最近2天
        
        payload = {
            "type": "candleSnapshot",
            "req": {
                "coin": "BTC",
                "interval": "1d",
                "startTime": start_ms
            }
        }
        resp = requests.post(
            "https://api.hyperliquid.xyz/info",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        if resp.status_code == 200 and resp.text.strip():
            import json
            data = json.loads(resp.text)
            if isinstance(data, list) and len(data) > 0:
                latest = data[-1]
                v_btc = float(latest.get("v", 0))
                o = float(latest.get("o", 0))
                c = float(latest.get("c", 0))
                if v_btc > 0 and o > 0:
                    return v_btc * (o + c) / 2  # BTC量 × 平均价 = USD成交额
    except Exception as e:
        print(f"  Hyperliquid failed: {e}")
    return 0.0


# ============================================================
# 主采集
# ============================================================
def run_collection():
    now = datetime.utcnow()
    print(f"[{now.isoformat()}] === 真实数据采集 ===")
    
    db = SessionLocal()
    try:
        # BTC 价格
        print("\n[1] BTC 价格...")
        btc_info = fetch_btc_price()
        print(f"    BTC: ${btc_info['price']:,.0f} ({btc_info['source']})")
        
        # Binance
        print("\n[2] Binance...")
        bnb = fetch_binance()
        print(f"    Spot:  ${bnb['spot']/1e6:.1f}M")
        print(f"    Fut:   ${bnb['futures']/1e6:.1f}M")
        
        # OKX
        print("\n[3] OKX...")
        okx_spot = fetch_okx_spot()
        okx_fut = fetch_okx_swap()
        print(f"    Spot:  ${okx_spot/1e6:.1f}M")
        print(f"    Fut:   ${okx_fut/1e6:.1f}M")
        
        # Bybit
        print("\n[4] Bybit...")
        bybit = fetch_bybit()
        print(f"    Spot:  ${bybit['spot']/1e6:.1f}M")
        print(f"    Fut:   ${bybit['futures']/1e6:.1f}M")
        
        # Hyperliquid
        print("\n[5] Hyperliquid...")
        hl_fut = fetch_hyperliquid()
        print(f"    Fut:   ${hl_fut/1e6:.1f}M")
        
        # 写入数据库
        print("\n[写入] BTC 价格...")
        # 更新现有 OKX/Coingecko 源数据
        existing_btc = db.query(models.BtcPrice).filter(
            models.BtcPrice.source.in_(["okx_rest", "coingecko"])
        ).first()
        if existing_btc:
            existing_btc.price = btc_info['price']
            existing_btc.timestamp = now
        else:
            db.add(models.BtcPrice(
                timestamp=now,
                price=btc_info['price'],
                source=btc_info['source']
            ))
        
        # 写入交易量
        volumes = [
            ("binance",    "spot",     bnb["spot"]),
            ("binance",    "futures",  bnb["futures"]),
            ("okx",        "spot",     okx_spot),
            ("okx",        "futures",  okx_fut),
            ("bybit",      "spot",     bybit["spot"]),
            ("bybit",      "futures",  bybit["futures"]),
            ("hyperliquid","futures",  hl_fut),
        ]
        
        print("\n[写入] 交易量...")
        for ex, mtype, vol in volumes:
            existing = db.query(models.ExchangeVolumeTimeseries).filter(
                models.ExchangeVolumeTimeseries.exchange == ex,
                models.ExchangeVolumeTimeseries.market_type == mtype,
                models.ExchangeVolumeTimeseries.source == "api"
            ).first()
            if existing:
                existing.ts = now
                existing.volume_usd = vol
            elif vol > 0:
                db.add(models.ExchangeVolumeTimeseries(
                    ts=now,
                    exchange=ex,
                    market_type=mtype,
                    volume_usd=vol,
                    source="api"
                ))
            print(f"    {ex} {mtype}: ${vol/1e6:.1f}M")
        
        # 同时写入 Dashboard Daily Snapshot
        print("\n[写入] Dashboard 快照...")
        date_str = now.strftime("%Y-%m-%d")
        vol_map = {ex: {"spot": 0, "futures": 0} for ex, _, _ in volumes}
        for ex, mtype, vol in volumes:
            vol_map[ex][mtype] = vol
        for ex in vol_map:
            spot_v = vol_map[ex]["spot"]
            fut_v = vol_map[ex]["futures"]
            if spot_v > 0 or fut_v > 0:
                write_dashboard_snapshot(db, date_str, ex, spot_v, fut_v, now)
                print(f"    {ex}: spot=${spot_v/1e6:.1f}M, fut=${fut_v/1e6:.1f}M")
        
        db.commit()
        print(f"\n[完成] {now.isoformat()}")
        
    finally:
        db.close()


if __name__ == "__main__":
    run_collection()

# ========== 写入 Dashboard Daily Snapshot ==========
def write_dashboard_snapshot(db, date_str: str, exchange: str, spot_vol: float, fut_vol: float, now: datetime):
    """写入 Dashboard 每日快照（不存在则创建，存在则更新）"""
    existing = db.query(models.DashboardDailySnapshot).filter(
        models.DashboardDailySnapshot.snapshot_date == date_str,
        models.DashboardDailySnapshot.exchange == exchange
    ).first()
    if existing:
        existing.spot_volume = spot_vol
        existing.futures_volume = fut_vol
        existing.total_volume = spot_vol + fut_vol
        existing.updated_at = now
    else:
        db.add(models.DashboardDailySnapshot(
            snapshot_date=date_str,
            exchange=exchange,
            total_volume=spot_vol + fut_vol,
            spot_volume=spot_vol,
            futures_volume=fut_vol,
            event_count=0,
            high_risk_event_count=0,
        ))
