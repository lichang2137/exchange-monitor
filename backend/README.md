# Exchange Monitor Backend

FastAPI 后端项目

## 快速启动

```bash
# 1. 进入项目目录
cd exchange-monitor-backend

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 初始化数据库并填充演示数据
python seed_data.py

# 5. 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API 文档

启动后访问：http://localhost:8000/docs

## 接口列表

| 接口 | 说明 |
|------|------|
| GET /api/chart | 获取图表数据 (BTC价格 + 交易量) |
| GET /api/events | 获取事件列表 |
| GET /api/exchanges | 获取支持的交易所 |
| GET /api/filters | 获取筛选器选项 |

## 项目结构

```
exchange-monitor-backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI 应用入口
│   ├── database.py      # 数据库配置
│   ├── models/
│   │   ├── __init__.py
│   │   ├── models.py   # SQLAlchemy 模型
│   │   └── schemas.py  # Pydantic 模式
│   └── routers/
│       ├── __init__.py
│       └── chart.py     # API 路由
├── seed_data.py         # 数据填充脚本
├── requirements.txt    # 依赖
└── README.md
```
