# Exchange Monitor Frontend

React + Vite 前端项目

## 快速启动

```bash
# 1. 进入项目目录
cd exchange-monitor-frontend

# 2. 安装依赖
npm install

# 3. 启动开发服务器
npm run dev
```

## 开发模式

确保后端服务已启动：
```bash
cd ../exchange-monitor-backend
uvicorn app.main:app --reload
```

前端会自动代理 `/api` 请求到后端。

## 构建生产版本

```bash
npm run build
```

## 项目结构

```
src/
├── components/          # UI 组件
│   ├── Header.tsx      # 顶部导航
│   ├── ControlPanel.tsx  # 控制面板
│   ├── PriceChart.tsx # 图表组件
│   ├── EventsList.tsx # 事件列表
│   └── EventModal.tsx # 事件详情弹窗
├── hooks/              # 自定义 Hooks
│   └── useData.ts     # 数据获取 Hook
├── services/          # API 服务
│   └── api.ts         # API 调用
├── types/             # TypeScript 类型
│   └── index.ts       # 类型定义
├── App.tsx            # 主应用组件
├── App.css            # 全局样式
└── main.tsx           # 入口文件
```

## 功能

- ✅ BTC 价格曲线（左轴）
- ✅ 多交易所交易量叠加（右轴）
- ✅ 市场类型切换（现货/合约/总量）
- ✅ 交易所多选
- ✅ 事件类型筛选
- ✅ 事件时间流列表
- ✅ 事件详情弹窗
- ✅ 深色 Dashboard 风格
- ✅ 图表缩放/拖拽
