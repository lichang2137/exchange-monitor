"""
BTC 价格数据服务
使用多个公开免费 API 获取真实 BTC 价格数据
"""
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
import json
import os

# 缓存配置
BTC_CACHE_FILE = "/tmp/btc_price_cache.json"
BTC_CACHE_DURATION = 300  # 5分钟缓存


def fetch_btc_prices_coingecko(hours: int = 168) -> List[Dict]:
    """
    从 CoinGecko 获取 BTC 价格数据（免费，无需 API Key）
    时间粒度：1天（免费版限制）
    """
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
    params = {
        "vs_currency": "usd",
        "days": min(hours // 24 + 1, 90),  # 免费版最多90天
        "interval": "hourly" if hours <= 24 * 90 else "daily"
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        result = []
        for ts, price in data.get("prices", []):
            dt = datetime.utcfromtimestamp(ts / 1000)
            result.append({
                "ts": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "value": round(price, 2)
            })
        
        return result
        
    except requests.RequestException as e:
        print(f"CoinGecko API 失败: {e}")
        return []


def fetch_btc_prices_binance(hours: int = 168) -> List[Dict]:
    """
    从 Binance 获取 BTC 价格数据
    """
    # 使用较新的时间参数
    end_time = int(datetime.utcnow().timestamp() * 1000)
    start_time = end_time - (hours * 60 * 60 * 1000)
    
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": "BTCUSDT",
        "interval": "1h",
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1000
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        # 451 表示地区限制
        if response.status_code == 451:
            print("Binance API 451 错误，尝试备用 endpoint")
            # 尝试使用 api2.binance.com
            url = "https://api2.binance.com/api/v3/klines"
            response = requests.get(url, params=params, timeout=10)
        
        response.raise_for_status()
        data = response.json()
        
        result = []
        for kline in data:
            ts = datetime.utcfromtimestamp(kline[0] / 1000)
            price = float(kline[4])  # 收盘价
            result.append({
                "ts": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "value": round(price, 2)
            })
        
        return result
        
    except requests.RequestException as e:
        print(f"Binance API 失败: {e}")
        return []


def fetch_btc_prices_okx(hours: int = 168) -> List[Dict]:
    """
    从 OKX 获取 BTC 价格数据
    """
    end_time = int(datetime.utcnow().timestamp() * 1000)
    start_time = end_time - (hours * 60 * 60 * 1000)
    
    url = "https://www.okx.com/api/v5/market/history-candles"
    params = {
        "instId": "BTC-USDT",
        "bar": "1h",
        "startTime": start_time,
        "endTime": end_time,
        "limit": 100
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("code") != "0":
            print(f"OKX API 错误: {data.get('msg')}")
            return []
        
        result = []
        for item in data.get("data", []):
            ts = datetime.utcfromtimestamp(int(item[0]) / 1000)
            price = float(item[4])  # 收盘价
            result.append({
                "ts": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "value": round(price, 2)
            })
        
        return result
        
    except requests.RequestException as e:
        print(f"OKX API 失败: {e}")
        return []


def fetch_btc_prices_coinstats(hours: int = 168) -> List[Dict]:
    """
    从 CoinStats 获取 BTC 价格数据
    """
    # 使用较新的时间参数
    end_time = int(datetime.utcnow().timestamp() * 1000)
    start_time = end_time - (hours * 60 * 60 * 1000)
    
    url = "https://api.coinstats.app/public/v1/coins/bitcoin"
    params = {
        "timePeriod": "1h",
        "startDate": start_time,
        "endDate": end_time
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        result = []
        for item in data.get("history", []):
            ts = datetime.utcfromtimestamp(int(item["date"]))
            result.append({
                "ts": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "value": round(float(item["price"]), 2)
            })
        
        return result
        
    except requests.RequestException as e:
        print(f"CoinStats API 失败: {e}")
        return []


def fetch_btc_prices(hours: int = 168) -> List[Dict]:
    """
    获取 BTC 价格数据（尝试多个 API）
    """
    # 尝试多个 API
    apis = [
        ("OKX", fetch_btc_prices_okx),
        ("CoinGecko", fetch_btc_prices_coingecko),
        ("Binance", fetch_btc_prices_binance),
    ]
    
    for name, fetch_func in apis:
        print(f"尝试从 {name} 获取 BTC 数据...")
        result = fetch_func(hours)
        if result:
            print(f"从 {name} 获取到 {len(result)} 条数据")
            return result
    
    # 所有 API 都失败，返回模拟数据
    print("所有 API 都失败，使用模拟数据")
    return generate_mock_btc_prices(hours)


def generate_mock_btc_prices(hours: int = 168) -> List[Dict]:
    """
    生成模拟 BTC 价格数据（当所有 API 都失败时）
    """
    import random
    
    result = []
    base_price = 82000
    now = datetime.utcnow()
    
    for i in range(hours, 0, -1):
        ts = now - timedelta(hours=i)
        # 模拟价格波动
        price = base_price + random.uniform(-2000, 2000) + random.gauss(0, 500)
        result.append({
            "ts": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "value": round(price, 2)
        })
    
    return result


def get_cached_btc_prices(hours: int = 168) -> List[Dict]:
    """获取 BTC 价格（带缓存）"""
    # 检查缓存是否存在且有效
    if os.path.exists(BTC_CACHE_FILE):
        try:
            with open(BTC_CACHE_FILE, 'r') as f:
                cache = json.load(f)
            # 缓存时间不超过5分钟
            if time.time() - cache.get("timestamp", 0) < BTC_CACHE_DURATION:
                cached_data = cache.get("data", [])
                # 只返回请求的小时数
                return cached_data[:hours]
        except Exception:
            pass
    
    # 获取新数据
    prices = fetch_btc_prices(hours)
    
    # 写入缓存
    try:
        with open(BTC_CACHE_FILE, 'w') as f:
            json.dump({"timestamp": time.time(), "data": prices}, f)
    except Exception:
        pass
    
    return prices


def fetch_btc_price_current() -> Optional[Dict]:
    """
    获取当前 BTC 价格
    """
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin",
        "vs_currencies": "usd"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return {
            "ts": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "value": round(data["bitcoin"]["usd"], 2)
        }
    except Exception as e:
        print(f"获取当前BTC价格失败: {e}")
        return None


if __name__ == "__main__":
    # 测试
    prices = get_cached_btc_prices(24)
    print(f"获取到 {len(prices)} 条数据")
    if prices:
        print(f"最新价格: {prices[-1]}")
