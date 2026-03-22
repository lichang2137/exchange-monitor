"""
Coinalyze 数据服务
来源: https://api.coinalyze.net/v1/
覆盖: Binance / OKX / Bybit / Hyperliquid 的合约 OI，资金费率
认证: Header api_key
速率限制: 40次/分钟
"""

import os
import json
import time
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional

BASE_URL = "https://api.coinalyze.net/v1"

# Coinalyze 交易所代码 + 各所 symbol 格式映射
# 格式说明:
#   Binance:    {base}USDT_PERP.A   → BTCUSDT_PERP.A
#   OKX:       {base}USD_PERP.3   → BTCUSD_PERP.3  (注意是USD不是USDT)
#   Bybit:     {base}USDT.{code}   → BTCUSDT.6
#   Hyperliquid: {base}.{code}     → BTC.H
EXCHANGE_MAP = {
    "binance":      {"code": "A", "format": "{base}USDT_PERP.{code}", "example": "BTCUSDT_PERP.A"},
    "okx":          {"code": "3", "format": "{base}USD_PERP.{code}",  "example": "BTCUSD_PERP.3"},
    "bybit":        {"code": "6", "format": "{base}USDT.{code}",      "example": "BTCUSDT.6"},
    "hyperliquid":  {"code": "H", "format": "{base}.{code}",         "example": "BTC.H"},
    "bitget":       {"code": "Y", "format": "{base}_USDT.{code}",   "example": "BTC_USDT.Y"},
}


def _symbol(base: str, exchange: str) -> str:
    """生成各所正确的 Coinalyze symbol"""
    if exchange.lower() not in EXCHANGE_MAP:
        return f"{base}USDT_PERP.A"  # 默认 Binance 格式
    m = EXCHANGE_MAP[exchange.lower()]
    return m["format"].format(base=base, code=m["code"])


def _headers() -> Dict[str, str]:
    return {"api_key": os.getenv("COINALYZE_API_KEY", ""), "accept": "application/json"}


def _now_ts() -> int:
    return int(datetime.utcnow().timestamp())


def fetch_current_oi_usd(symbols: List[str], exchanges: List[str]) -> List[Dict]:
    """
    获取当前 OI (USD)，支持多所多币种
    返回: [{"exchange": "binance", "symbol": "BTC", "oi_btc": float, "oi_usd": float}]
    """
    # 构建 Coinalyze symbol 列表 (每个交易所对应格式不同)
    coinalyze_syms = {_symbol(s, ex): (s, ex) for s in symbols for ex in exchanges}
    
    results = []
    batch = list(coinalyze_syms.keys())
    
    for i in range(0, len(batch), 20):
        symbols_param = ",".join(batch[i:i+20])
        try:
            resp = requests.get(
                f"{BASE_URL}/open-interest",
                params={"symbols": symbols_param, "convert_to_usd": "true"},
                headers=_headers(),
                timeout=10
            )
            if resp.status_code == 200:
                for item in resp.json():
                    sym = item.get("symbol", "")
                    if sym in coinalyze_syms:
                        base, ex = coinalyze_syms[sym]
                        results.append({
                            "symbol": base,
                            "exchange": ex,
                            "oi_btc": item.get("value", 0),  # convert_to_usd=true 时是 USD
                            "oi_usd": item.get("value", 0),
                            "update_ms": item.get("update", 0),
                        })
        except Exception as e:
            print(f"Coinalyze OI error: {e}")
    
    return results


def fetch_current_funding_rates(symbols: List[str], exchanges: List[str]) -> List[Dict]:
    """
    获取当前资金费率 (annualized rate fraction)
    """
    coinalyze_syms = {_symbol(s, ex): (s, ex) for s in symbols for ex in exchanges}
    
    results = []
    batch = list(coinalyze_syms.keys())
    
    for i in range(0, len(batch), 20):
        symbols_param = ",".join(batch[i:i+20])
        try:
            resp = requests.get(
                f"{BASE_URL}/funding-rate",
                params={"symbols": symbols_param},
                headers=_headers(),
                timeout=10
            )
            if resp.status_code == 200:
                for item in resp.json():
                    sym = item.get("symbol", "")
                    if sym in coinalyze_syms:
                        base, ex = coinalyze_syms[sym]
                        results.append({
                            "symbol": base,
                            "exchange": ex,
                            "funding_rate": item.get("value", 0),  # fraction, e.g. 0.0001 = 0.01%
                            "update_ms": item.get("update", 0),
                        })
        except Exception as e:
            print(f"Coinalyze Funding Rate error: {e}")
    
    return results


def fetch_oi_history(symbol: str, exchange: str, days: int = 7) -> List[Dict]:
    """
    获取 OI 历史 (日级 OHLC)，返回按时间升序
    """
    coinalyze_sym = _symbol(symbol.upper(), exchange)
    now = datetime.utcnow()
    ago = now - timedelta(days=days)
    
    try:
        resp = requests.get(
            f"{BASE_URL}/open-interest-history",
            params={
                "symbols": coinalyze_sym,
                "interval": "daily",
                "from": int(ago.timestamp()),
                "to": int(now.timestamp()),
            },
            headers=_headers(),
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list) and len(data) > 0:
                return [
                    {
                        "ts": datetime.utcfromtimestamp(h["t"]).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "open": h["o"],
                        "high": h["h"],
                        "low": h["l"],
                        "close": h["c"],
                        "exchange": exchange,
                        "symbol": symbol.upper(),
                    }
                    for h in data[0].get("history", [])
                ]
    except Exception as e:
        print(f"Coinalyze OI history error: {e}")
    return []


def fetch_funding_history(symbol: str, exchange: str, days: int = 7) -> List[Dict]:
    """
    获取资金费率历史 (日级 OHLC)
    """
    coinalyze_sym = _symbol(symbol.upper(), exchange)
    now = datetime.utcnow()
    ago = now - timedelta(days=days)
    
    try:
        resp = requests.get(
            f"{BASE_URL}/funding-rate-history",
            params={
                "symbols": coinalyze_sym,
                "interval": "daily",
                "from": int(ago.timestamp()),
                "to": int(now.timestamp()),
            },
            headers=_headers(),
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list) and len(data) > 0:
                return [
                    {
                        "ts": datetime.utcfromtimestamp(h["t"]).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "open": h["o"],
                        "high": h["h"],
                        "low": h["l"],
                        "close": h["c"],
                        "exchange": exchange,
                        "symbol": symbol.upper(),
                    }
                    for h in data[0].get("history", [])
                ]
    except Exception as e:
        print(f"Coinalyze Funding history error: {e}")
    return []


def fetch_long_short_ratio(symbol: str, exchange: str, days: int = 7) -> List[Dict]:
    """
    获取多空比历史
    """
    coinalyze_sym = _symbol(symbol.upper(), exchange)
    now = datetime.utcnow()
    ago = now - timedelta(days=days)
    
    try:
        resp = requests.get(
            f"{BASE_URL}/long-short-ratio-history",
            params={
                "symbols": coinalyze_sym,
                "interval": "daily",
                "from": int(ago.timestamp()),
                "to": int(now.timestamp()),
            },
            headers=_headers(),
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list) and len(data) > 0:
                return [
                    {
                        "ts": datetime.utcfromtimestamp(h["t"]).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "ratio": h.get("r", 0),
                        "long_pct": h.get("l", 0),
                        "short_pct": h.get("s", 0),
                        "exchange": exchange,
                        "symbol": symbol.upper(),
                    }
                    for h in data[0].get("history", [])
                ]
    except Exception as e:
        print(f"Coinalyze LS ratio error: {e}")
    return []


def get_btc_oi_summary() -> Dict:
    """
    获取 BTC 在各所的 OI + 资金费率汇总
    """
    exchanges = ["binance", "okx", "bybit", "hyperliquid"]
    symbols = ["BTC"]
    
    oi_data = fetch_current_oi_usd(symbols, exchanges)
    fr_data = fetch_current_funding_rates(symbols, exchanges)
    
    # 按 exchange 合并
    merged: Dict[str, Dict] = {}
    for item in oi_data:
        ex = item["exchange"]
        merged[ex] = {
            "exchange": ex,
            "symbol": "BTC",
            "oi_usd": item["oi_usd"],
            "funding_rate": None,
            "update_ms": item["update_ms"],
        }
    for item in fr_data:
        ex = item["exchange"]
        if ex in merged:
            merged[ex]["funding_rate"] = item["funding_rate"]
    
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "data": list(merged.values()),
    }


if __name__ == "__main__":
    print("=== BTC OI + Funding Summary ===")
    result = get_btc_oi_summary()
    print(json.dumps(result, indent=2))
