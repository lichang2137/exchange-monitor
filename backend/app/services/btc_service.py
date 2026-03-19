"""
BTC 价格数据服务
使用 OKX API 获取真实 BTC 价格数据
"""
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
import json
import os
import subprocess
import re

# 缓存配置
BTC_CACHE_FILE = "/tmp/btc_price_cache.json"
BTC_CACHE_DURATION = 300  # 5分钟缓存


def fetch_btc_prices_okx(hours: int = 168) -> List[Dict]:
    """
    从 OKX 获取 BTC 价格数据
    使用 okx CLI 命令
    """
    try:
        # 使用 OKX CLI 获取 K 线数据
        result = subprocess.run(
            ["okx", "market", "candles", "BTC-USDT", "--bar", "1H", "--limit", str(min(hours, 168))],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            print(f"OKX CLI error: {result.stderr}")
            return []
        
        # 解析输出
        lines = result.stdout.strip().split('\n')
        if len(lines) < 2:
            return []
        
        result_list = []
        
        # 从数据行开始解析（跳过表头）
        for line in lines[1:]:
            # 使用正则提取数据
            # 格式: 3/19/2026, 8:00:00 AM   71253.1  71325.9  71051    71085.5  123.6371518
            match = re.match(r'(\d{1,2}/\d{1,2}/\d{4}),\s+(\d{1,2}:\d{2}:\d{2}\s*[AP]M)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)', line)
            if match:
                date_str = match.group(1)
                time_str = match.group(2)
                close_price = float(match.group(6))
                
                # 解析时间
                dt_str = f"{date_str} {time_str}"
                dt = datetime.strptime(dt_str, "%m/%d/%Y %I:%M:%S %p")
                # 转换为 UTC (OKX 时间是 UTC+8)
                dt = dt - timedelta(hours=8)
                
                result_list.append({
                    "ts": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "value": round(close_price, 2),
                    "source": "okx"
                })
        
        # 反转顺序（从旧到新）
        result_list.reverse()
        return result_list
        
    except Exception as e:
        print(f"OKX API 失败: {e}")
        return []


def fetch_btc_prices_coingecko(hours: int = 168) -> List[Dict]:
    """
    从 CoinGecko 获取 BTC 价格数据（备用）
    """
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
    params = {
        "vs_currency": "usd",
        "days": min(hours // 24 + 1, 7),  # 免费版最多7天
        "interval": "hourly"
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
                "value": round(price, 2),
                "source": "coingecko"
            })
        
        return result
        
    except requests.RequestException as e:
        print(f"CoinGecko API 失败: {e}")
        return []


def fetch_btc_prices(hours: int = 168) -> List[Dict]:
    """
    获取 BTC 价格数据（优先 OKX）
    """
    # 优先尝试 OKX
    apis = [
        ("OKX", fetch_btc_prices_okx),
        ("CoinGecko", fetch_btc_prices_coingecko),
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
        price = base_price + random.uniform(-2000, 2000) + random.gauss(0, 500)
        result.append({
            "ts": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "value": round(price, 2),
            "source": "mock"
        })
    
    return result


def get_cached_btc_prices(hours: int = 168) -> List[Dict]:
    """获取 BTC 价格（带缓存）"""
    if os.path.exists(BTC_CACHE_FILE):
        try:
            with open(BTC_CACHE_FILE, 'r') as f:
                cache = json.load(f)
            if time.time() - cache.get("timestamp", 0) < BTC_CACHE_DURATION:
                cached_data = cache.get("data", [])
                return cached_data[:hours]
        except Exception:
            pass
    
    prices = fetch_btc_prices(hours)
    
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
    try:
        result = subprocess.run(
            ["okx", "market", "ticker", "BTC-USDT"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if 'last' in line.lower():
                    parts = line.split()
                    for i, p in enumerate(parts):
                        if p == 'last':
                            price = float(parts[i+1])
                            return {
                                "ts": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                                "value": round(price, 2)
                            }
    except Exception as e:
        print(f"获取当前BTC价格失败: {e}")
    
    return None


if __name__ == "__main__":
    prices = get_cached_btc_prices(24)
    print(f"获取到 {len(prices)} 条数据")
    if prices:
        print(f"最新价格: {prices[-1]}")
