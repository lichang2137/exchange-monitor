# Exchange Monitor

交易所竞品监控可视化平台

## 项目简介

通过 BTC 价格与交易量多曲线对比，结合动态事件标注，帮助运营团队快速洞察市场变化、竞品动态和业务机会。

## 项目结构

```
exchange-monitor/
├── backend/          # FastAPI 后端
│   ├── app/
│   │   ├── main.py          # 主应用
│   │   ├── database.py       # 数据库配置
│   │   ├── models/          # 数据模型
│   │   ├── routers/          # API 路由
│   │   └── services/         # 业务服务
│   │       ├── btc_service.py      # BTC 价格服务（支持 AiCoin/CoinGecko/OKX/Hyperliquid）
│   │       └── exchange_service.py # 交易所交易量服务
│   ├── requirements.txt
│   ├── seed_data.py         # 种子数据（支持真实数据填充）
│   └── README.md
├── frontend/         # React + Vite 前端
│   ├── src/
│   │   ├── components/      # React 组件
│   │   ├── hooks/           # 自定义 Hooks
│   │   ├── services/        # API 服务
│   │   └── types/          # TypeScript 类型
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

## 功能特性

- 📊 **BTC 价格曲线** - 主图为 BTC/USDT 价格，走势时间为横轴
- 📈 **多交易所交易量** - 支持 Binance、OKX、Bybit、Bitget、Hyperliquid
- 🔄 **业务线切换** - 支持查看：总量 / 现货 / 合约
- ✅ **交易所勾选** - 可勾选启用/禁用特定交易所曲线
- 📰 **事件时间流** - 图表下方展示时间轴对应事件
- 🔍 **事件分类筛选** - 支持按类型筛选事件
- 🌐 **多数据源** - 支持 AiCoin、CoinGecko、OKX、Hyperliquid 实时数据

## 数据源

### BTC 价格
- **优先**: AiCoin（聚合数据源）
- **备用**: CoinGecko、OKX、Hyperliquid
- **fallback**: 模拟数据

### 交易所交易量
- **Hyperliquid**: 直接 API 获取（实时）
- **其他交易所**: AiCoin 聚合数据（需要付费订阅）
- **fallback**: 模拟数据

> ⚠️ 当前服务器（腾讯云硅谷）无法访问部分 API（AiCoin DNS 解析失败），BTC 数据会回退到 CoinGecko。

## 快速启动

### 后端

```bash
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn app.main:app --reload --port 8000
```

后端 API: http://localhost:8000

### 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端地址: http://localhost:5173

## 数据填充

### 方式一：模拟数据（默认）

```bash
cd backend
python3 seed_data.py
```

### 方式二：真实数据

```bash
cd backend
python3 seed_data.py --live --hours 168
```

> 注意：真实数据需要网络可达 AiCoin/CoinGecko/OKX/Hyperliquid API。

## API 端点

| 端点 | 说明 |
|------|------|
| GET /api/chart | 获取图表数据 |
| GET /api/events | 获取事件列表 |
| GET /health | 健康检查 |

## 技术栈

- **后端**: FastAPI + SQLite + SQLAlchemy
- **前端**: React + TypeScript + Vite + ECharts
- **数据源**: AiCoin, CoinGecko, OKX, Hyperliquid

## 部署

### 后端 (生产)

```bash
cd backend
pip install -r requirements.txt
gunicorn app.main:app -w 4 -b 0.0.0.0:8000
```

### 前端 (生产)

```bash
cd frontend
npm run build
# dist/ 目录可部署到任何静态服务器
```

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT
