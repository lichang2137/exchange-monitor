# Exchange Monitor

交易所竞品监控可视化平台

## 项目结构

```
exchange-monitor/
├── backend/          # FastAPI 后端
│   ├── app/
│   ├── requirements.txt
│   └── README.md
└── frontend/         # React + Vite 前端
    ├── src/
    ├── package.json
    └── README.md
```

## 快速启动

### 后端

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

### 配置

前端默认连接 `http://localhost:8000`，如需修改请编辑：
- `frontend/src/services/api.ts`

## 功能

- BTC 价格曲线
- 5 所交易量叠加 (Binance/OKX/Bybit/Bitget/Hyperliquid)
- 总量/现货/合约切换
- 事件时间流
