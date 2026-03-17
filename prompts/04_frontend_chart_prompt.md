请根据以下数据库表结构，生成 FastAPI 后端代码。

要求：
1. 提供 /api/chart
   返回 BTC price + exchange volumes
2. 提供 /api/events
   返回当前时间范围内事件
3. 提供 /api/exchanges
   返回支持的交易所列表
4. 提供 /api/filters
   返回 market_type 和 event_type 选项
5. 使用 SQLite
6. 代码要结构清晰，方便未来继续扩展
7. 给出启动方式

数据库结构如下：
[粘贴 schema]
