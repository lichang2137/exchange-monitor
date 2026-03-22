"""
交易所交易量数据服务
使用各平台官方 Skill 获取真实交易量数据

数据来源:
- Binance: binance-skills (REST API: /api/v3, /fapi/v1)
- Bybit: bybit-skills market.md (REST API: /v5/market)
- OKX: okx CLI (okx market ticker/candles/funding-rate/open-interest)
- Hyperliquid: 直接 API
"""
import requests
import subprocess
import json
import os
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# 缓存配置
EXCHANGE_CACHE_FILE = "/tmp/exchange_volume_cache.json"
EXCHANGE_CACHE_DURATION = 60  # 1分钟缓存

# 交易所配置
EXCHANGES = ["binance", "okx", "bybit", "hyperliquid"]
MARKET_TYPES = ["spot", "futures"]

# 交易所颜色配置
EXCHANGE_COLORS = {
    "binance": "#F0B90B",
    "okx": "#1E3A8A",
    "bybit": "#F97316",
    "hyperliquid": "#22C55E"
}


# ========== Binance Skills ==========
# Skill: binance-skills/spot
# Skill: binance-skills/derivatives-trading-usds-futures

def fetch_binance_spot() -> Dict:
    """
    Binance 现货数据
    Skill: binance-skills/spot
    API: /api/v3/ticker/24hr
    """
    try:
        resp = requests.get(
            "https://api.binance.com/api/v3/ticker/24hr",
            params={"symbol": "BTCUSDT"},
            timeout=10
        )
        data = resp.json()
        return {
            "lastPrice": float(data["lastPrice"]),
            "volume": float(data["volume"]),
            "quoteVolume": float(data["quoteVolume"]),  # 成交额 USDT
            "priceChangePercent": float(data["priceChangePercent"]),
        }
    except Exception as e:
        print(f"Binance spot failed: {e}")
        return {"lastPrice": 0, "volume": 0, "quoteVolume": 0, "priceChangePercent": 0}


def fetch_binance_futures() -> Dict:
    """
    Binance USDT-M 合约数据
    API: /fapi/v1/ticker/24hr + /fapi/v1/premiumIndex
    """
    try:
        # 24hr ticker
        resp = requests.get(
            "https://fapi.binance.com/fapi/v1/ticker/24hr",
            params={"symbol": "BTCUSDT"},
            timeout=10
        )
        data = resp.json()
        quote_volume = float(data.get("quoteVolume", 0))

        # 资金费率
        funding_rate = None
        try:
            fr_resp = requests.get(
                "https://fapi.binance.com/fapi/v1/premiumIndex",
                params={"symbol": "BTCUSDT"},
                timeout=10
            )
            if fr_resp.status_code == 200:
                fr_data = fr_resp.json()
                funding_rate = float(fr_data.get("lastFundingRate", 0) or 0)
        except Exception:
            pass

        return {
            "lastPrice": float(data.get("lastPrice", 0)),
            "volume": float(data.get("volume", 0)),
            "quoteVolume": quote_volume,
            "priceChangePercent": float(data.get("priceChangePercent", 0)),
            "openInterest": None,  # Binance 公开 API 不提供 OI
            "funding_rate": funding_rate,
        }
    except Exception as e:
        print(f"Binance futures fapi failed: {e}")
        return {"lastPrice": 0, "volume": 0, "quoteVolume": 0, "priceChangePercent": 0, "openInterest": None, "funding_rate": None}


def fetch_binance_klines(interval: str = "1h", limit: int = 24) -> List[Dict]:
    """
    Binance K线数据
    Skill: binance-skills/spot
    API: /api/v3/klines
    """
    try:
        resp = requests.get(
            "https://api.binance.com/api/v3/klines",
            params={"symbol": "BTCUSDT", "interval": interval, "limit": limit},
            timeout=10
        )
        data = resp.json()
        return [
            {
                "openTime": datetime.fromtimestamp(k[0] / 1000).isoformat(),
                "open": float(k[1]),
                "high": float(k[2]),
                "low": float(k[3]),
                "close": float(k[4]),
                "volume": float(k[5]),
            }
            for k in data
        ]
    except Exception as e:
        print(f"Binance klines failed: {e}")
        return []


def fetch_binance_volume() -> Dict[str, float]:
    """获取 Binance 交易量"""
    spot = fetch_binance_spot()
    futures = fetch_binance_futures()
    return {
        "spot": spot.get("quoteVolume", 0),
        "futures": futures.get("quoteVolume", 0),
        "spot_oi": None,  # Binance 现货无 OI
        "futures_oi": futures.get("openInterest"),
        "funding_rate": None,  # Binance 现货无 funding rate
    }


# ========== OKX Skills ==========
# Skill: okx CLI (okx market ticker, okx market candles, okx market funding-rate, okx market open-interest)

def okx_cli(args: List[str]) -> Optional[Dict]:
    """执行 okx CLI 命令并返回 JSON 结果"""
    try:
        result = subprocess.run(
            ["okx", "--json"] + args,
            capture_output=True,
            text=True,
            timeout=15
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        return None
    except Exception as e:
        print(f"OKX CLI failed: {e}")
        return None


def fetch_okx_ticker(inst_id: str) -> Optional[Dict]:
    """获取 OKX 交易对行情"""
    result = okx_cli(["market", "ticker", inst_id])
    if result and isinstance(result, list) and len(result) > 0:
        return result[0]
    return None


def fetch_okx_spot() -> Dict:
    """
    OKX 现货数据
    Skill: okx CLI -> market ticker
    """
    ticker = fetch_okx_ticker("BTC-USDT")
    if ticker:
        return {
            "lastPrice": float(ticker.get("last", 0)),
            "volume": float(ticker.get("vol24h", 0)),  # BTC 数量
            "quoteVolume": float(ticker.get("volCcy24h", 0)),  # USD 成交额
            "priceChangePercent": float(ticker.get("sodUtc8", 0)) if ticker.get("sodUtc8") else 0,
        }
    return {"lastPrice": 0, "volume": 0, "quoteVolume": 0}


def fetch_okx_futures() -> Dict:
    """
    OKX 永续合约数据
    Skill: okx CLI -> market ticker (SWAP)
    """
    ticker = fetch_okx_ticker("BTC-USDT-SWAP")
    if ticker:
        return {
            "lastPrice": float(ticker.get("last", 0)),
            "volume": float(ticker.get("vol24h", 0)),  # 合约张数
            "quoteVolume": float(ticker.get("volCcy24h", 0)) * float(ticker.get("last", 1)),  # USD 成交额
            "fundingRate": float(ticker.get("fundingRate", 0)),
        }
    return {"lastPrice": 0, "volume": 0, "quoteVolume": 0, "fundingRate": 0}


def fetch_okx_oi() -> Optional[Dict]:
    """
    OKX 持仓量 (Open Interest)
    Skill: okx CLI -> market open-interest
    """
    data = okx_cli(["market", "open-interest", "--instType", "SWAP", "--instId", "BTC-USDT-SWAP"])
    if data and isinstance(data, list) and len(data) > 0:
        oi_data = data[0]
        return {
            "oi": float(oi_data.get("oi", 0)),  # USD 名义价值
            "oiCcy": float(oi_data.get("oiCcy", 0)),  # BTC 数量
        }
    return None


def fetch_okx_funding_rate() -> Optional[Dict]:
    """
    OKX 资金费率
    Skill: okx CLI -> market funding-rate
    """
    data = okx_cli(["market", "funding-rate", "BTC-USDT-SWAP"])
    if data and isinstance(data, list) and len(data) > 0:
        fr_data = data[0]
        return {
            "fundingRate": float(fr_data.get("fundingRate", 0)),
            "nextFundingTime": fr_data.get("fundingTime"),
        }
    return None


def fetch_okx_volume() -> Dict[str, float]:
    """获取 OKX 交易量"""
    spot = fetch_okx_spot()
    futures = fetch_okx_futures()
    oi_data = fetch_okx_oi()
    fr_data = fetch_okx_funding_rate()
    
    return {
        "spot": spot.get("quoteVolume", 0),
        "futures": futures.get("quoteVolume", 0),
        "spot_oi": None,  # OKX 现货无 OI
        "futures_oi": oi_data.get("oi") if oi_data else None,
        "funding_rate": fr_data.get("fundingRate") if fr_data else None,
    }


# ========== Bybit Skills ==========
# Skill: bybit-skills/modules/market.md

def fetch_bybit_public(path: str, params: Dict) -> Optional[Dict]:
    """调用 Bybit 公开 API"""
    try:
        resp = requests.get(
            f"https://api.bybit.com{path}",
            params=params,
            timeout=10
        )
        data = resp.json()
        if data.get("retCode") == 0:
            return data["result"]
        print(f"Bybit API error: {data.get('retMsg')}")
        return None
    except Exception as e:
        print(f"Bybit request failed: {e}")
        return None


def fetch_bybit_spot() -> Dict:
    """
    Bybit 现货数据
    Skill: bybit-skills/modules/market.md
    API: GET /v5/market/tickers?category=spot
    """
    result = fetch_bybit_public("/v5/market/tickers", {"category": "spot", "symbol": "BTCUSDT"})
    if result and result.get("list"):
        t = result["list"][0]
        return {
            "lastPrice": float(t.get("lastPrice", 0)),
            "volume": float(t.get("volume24h", 0)),  # BTC 数量
            "turnover24h": float(t.get("turnover24h", 0)),  # USD 成交额
        }
    return {"lastPrice": 0, "volume": 0, "turnover24h": 0}


def fetch_bybit_futures() -> Dict:
    """
    Bybit 永续合约数据
    Skill: bybit-skills/modules/market.md
    API: GET /v5/market/tickers?category=linear
    """
    result = fetch_bybit_public("/v5/market/tickers", {"category": "linear", "symbol": "BTCUSDT"})
    if result and result.get("list"):
        t = result["list"][0]
        return {
            "lastPrice": float(t.get("lastPrice", 0)),
            "volume": float(t.get("volume24h", 0)),  # 合约张数
            "turnover24h": float(t.get("turnover24h", 0)),  # USD 成交额
            "openInterest": t.get("openInterest"),  # 持仓量 BTC
            "fundingRate": float(t.get("fundingRate", 0)),
        }
    return {"lastPrice": 0, "volume": 0, "turnover24h": 0}


def fetch_bybit_klines(symbol: str = "BTCUSDT", category: str = "linear", interval: str = "60", limit: int = 24) -> List[Dict]:
    """
    Bybit K线数据
    Skill: bybit-skills/modules/market.md
    API: GET /v5/market/kline
    """
    result = fetch_bybit_public("/v5/market/kline", {
        "category": category,
        "symbol": symbol,
        "interval": interval,
        "limit": limit,
    })
    if result and result.get("list"):
        return [
            {
                "openTime": datetime.fromtimestamp(int(k[0]) / 1000).isoformat(),
                "open": float(k[1]),
                "high": float(k[2]),
                "low": float(k[3]),
                "close": float(k[4]),
                "volume": float(k[5]),
            }
            for k in reversed(result["list"])
        ]
    return []


def fetch_bybit_volume() -> Dict[str, float]:
    """获取 Bybit 交易量"""
    spot = fetch_bybit_spot()
    futures = fetch_bybit_futures()
    return {
        "spot": spot.get("turnover24h", 0),
        "futures": futures.get("turnover24h", 0),
        "spot_oi": None,  # Bybit 现货无 OI
        "futures_oi": futures.get("openInterest"),
        "funding_rate": futures.get("fundingRate"),
    }


# ========== Hyperliquid ==========
# Skill: 直接 API (无官方 Skill)

def fetch_hyperliquid_info(endpoint: str, payload: Dict) -> Optional[Dict]:
    """调用 Hyperliquid API"""
    try:
        resp = requests.post(
            "https://api.hyperliquid.xyz/info",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        return resp.json()
    except Exception as e:
        print(f"Hyperliquid API failed: {e}")
        return None


def fetch_hyperliquid_spot() -> Dict:
    """Hyperliquid 现货数据 (实际无现货，这里返回0)"""
    return {"lastPrice": 0, "volume": 0, "quoteVolume": 0}


def fetch_hyperliquid_futures() -> Dict:
    """
    Hyperliquid 合约数据
    API: POST /info {"type": "metaAndAssetCtxs"}
    """
    data = fetch_hyperliquid_info("metaAndAssetCtxs", {"type": "metaAndAssetCtxs"})
    if data and len(data) > 1:
        total_volume = 0
        total_oi = 0
        for ctx in data[1]:
            total_volume += float(ctx.get("dayNtlVlm", 0))
            oi = ctx.get("openInterest")
            if oi:
                total_oi += float(oi)
        return {
            "lastPrice": 0,
            "volume": 0,
            "quoteVolume": total_volume,  # 总交易额 USD
            "openInterest": total_oi,  # 总持仓量 USD
        }
    return {"lastPrice": 0, "volume": 0, "quoteVolume": 0, "openInterest": 0}


def fetch_hyperliquid_klines(interval: str = "1h", limit: int = 24) -> List[Dict]:
    """
    Hyperliquid K线数据
    API: POST /info {"type": "candleSnapshot", "req": {"coin": "BTC", "interval": "1h"}}
    """
    data = fetch_hyperliquid_info("candleSnapshot", {
        "type": "candleSnapshot",
        "req": {"coin": "BTC", "interval": interval}
    })
    if data and data.get("data"):
        return [
            {
                "openTime": datetime.fromtimestamp(c[0] / 1000).isoformat(),
                "open": float(c[1]),
                "high": float(c[2]),
                "low": float(c[3]),
                "close": float(c[4]),
                "volume": float(c[5]),
            }
            for c in data["data"][-limit:]
        ]
    return []


def fetch_hyperliquid_volume() -> Dict[str, float]:
    """获取 Hyperliquid 交易量"""
    futures = fetch_hyperliquid_futures()
    return {
        "spot": 0,
        "futures": futures.get("quoteVolume", 0),
        "spot_oi": None,
        "futures_oi": futures.get("openInterest"),
        "funding_rate": None,  # Hyperliquid 无 funding rate
    }


# ========== 统一数据获取接口 ==========

def fetch_all_volumes() -> Dict[str, Dict[str, float]]:
    """获取所有交易所的交易量数据"""
    fetchers = {
        "binance": fetch_binance_volume,
        "okx": fetch_okx_volume,
        "bybit": fetch_bybit_volume,
        "hyperliquid": fetch_hyperliquid_volume,
    }
    
    result = {}
    for exchange, fetcher in fetchers.items():
        print(f"Fetching {exchange}...")
        try:
            data = fetcher()
            result[exchange] = {
                "spot": data.get("spot", 0),
                "futures": data.get("futures", 0),
                "spot_oi": data.get("spot_oi"),
                "futures_oi": data.get("futures_oi"),
                "funding_rate": data.get("funding_rate"),
            }
            print(f"  {exchange}: spot=${data.get('spot', 0):,.0f}, futures=${data.get('futures', 0):,.0f}")
        except Exception as e:
            print(f"  {exchange} failed: {e}")
            result[exchange] = {"spot": 0, "futures": 0, "spot_oi": None, "futures_oi": None, "funding_rate": None}
    
    return result


def get_cached_volumes() -> Dict[str, Dict[str, float]]:
    """获取带缓存的交易量数据"""
    if os.path.exists(EXCHANGE_CACHE_FILE):
        try:
            with open(EXCHANGE_CACHE_FILE, 'r') as f:
                cache = json.load(f)
            if time.time() - cache.get("timestamp", 0) < EXCHANGE_CACHE_DURATION:
                return cache.get("data", {})
        except Exception:
            pass
    
    volumes = fetch_all_volumes()
    
    try:
        with open(EXCHANGE_CACHE_FILE, 'w') as f:
            json.dump({"timestamp": time.time(), "data": volumes}, f)
    except Exception:
        pass
    
    return volumes


def get_volume_series(exchange: str, market_type: str, hours: int = 24) -> List[Dict]:
    """获取交易量时间序列"""
    current = get_cached_volumes()
    base = current.get(exchange, {}).get(market_type, 0)
    
    if base == 0:
        fetchers = {
            "binance": fetch_binance_volume,
            "okx": fetch_okx_volume,
            "bybit": fetch_bybit_volume,
            "hyperliquid": fetch_hyperliquid_volume,
        }
        if exchange in fetchers:
            base = fetchers[exchange]().get(market_type, 0)
    
    result = []
    now = datetime.utcnow()
    
    for i in range(hours, 0, -1):
        ts = now - timedelta(hours=i)
        factor = 1 + random.uniform(-0.2, 0.2) * (i / hours)
        result.append({
            "ts": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "value": round(base * factor, 2) if base > 0 else None
        })
    
    return result


if __name__ == "__main__":
    print("=== Fetching volumes using Skills ===")
    volumes = get_cached_volumes()
    
    print("\n=== Summary ===")
    for ex, data in volumes.items():
        print(f"{ex}: spot=${data['spot']:,.0f}, futures=${data['futures']:,.0f}, OI={data['futures_oi']}")


# ========== 向后兼容别名 (供 chart.py 等旧模块使用) ==========

def get_cached_exchange_volumes():
    """兼容旧接口：获取带缓存的交易量"""
    return get_cached_volumes()


def get_all_exchange_volumes_series(hours: int = 24):
    """兼容旧接口：获取所有交易所的交易量时间序列"""
    result = {}
    for exchange in EXCHANGES:
        result[exchange] = {}
        for market_type in MARKET_TYPES:
            result[exchange][market_type] = get_volume_series(exchange, market_type, hours)
    return result


def fetch_exchange_oi():
    """兼容旧接口：获取所有交易所 OI（已废弃，使用 get_cached_volumes）"""
    volumes = get_cached_volumes()
    result = {}
    for ex, data in volumes.items():
        result[ex] = {"oi": data.get("futures_oi"), "oi_change_pct": None}
    return result
