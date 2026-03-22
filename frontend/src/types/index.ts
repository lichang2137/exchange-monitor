// 类型定义 - API v3

export interface BtcPrice {
  ts: string;
  value: number;
}

export interface ExchangeVolume {
  ts: string;
  exchange: string;
  market_type: string;
  value: number;
}

export interface ChartEvent {
  id: string;
  event_date?: string;  // YYYY-MM-DD，来自后端 event_date 字段
  ts: string;
  exchange: string;
  event_type: string;
  title: string;
  impact_score?: number;
}

// 新版图表数据（来自 /api/chart-data v3）
export interface ChartData {
  dates: string[];
  price: Record<string, number[]>;  // { BTC: [price...] }
  spot_volumes: Record<string, (number | null)[]>;
  futures_volumes: Record<string, (number | null)[]>;
  oi: OIData[];
  events: ChartEvent[];
  // 数据来源标识: official | converted | estimated
  volume_methods?: Record<string, 'official' | 'converted' | 'estimated'>;
}

export interface OIData {
  exchange: string;
  oi_usd: number;
  funding_rate: number | null;
}

export interface EventItem {
  id: string;
  ts: string;
  exchange: string;
  event_type: string;
  title: string;
  summary: string | null;
  source: string | null;
  url: string | null;
}

export interface EventsResponse {
  events: EventItem[];
  total: number;
}

export interface Exchange {
  id: string;
  name: string;
  color: string;
}

export interface FilterOption {
  id: string;
  name: string;
  color?: string;
}

export interface Filters {
  market_types: FilterOption[];
  event_types: FilterOption[];
}

// 图表数据类型
export type MarketType = 'spot' | 'futures';

// ========== Dashboard Types ==========

export interface TopMover {
  exchange: string | null;
  change_pct: number;
}

export interface RiskSummary {
  high_risk_events: number;
  wallet_issues: number;
  compliance_events: number;
}

export interface DashboardSummary {
  date: string;
  top_takeaways: string[];
  top_movers: {
    total: TopMover;
    spot: TopMover;
    futures: TopMover;
  };
  risk_summary: RiskSummary;
}

export interface TopEvent {
  id: string;
  event_time: string;
  event_type: string;
  title: string;
  impact_score?: number;
}

export interface ExchangeUpdate {
  exchange: string;
  total_volume: number | null;
  spot_volume: number | null;
  futures_volume: number | null;
  futures_oi: number | null;

  total_change_pct: number | null;
  spot_change_pct: number | null;
  futures_change_pct: number | null;
  oi_change_pct: number | null;

  event_count: number;
  high_priority_event_count: number;

  top_events: TopEvent[];

  summary_line: string;
}

export interface NewsItem {
  id: string;
  published_at: string | null;
  news_type: string;
  title: string;
  summary: string | null;
  source: string | null;
  source_url: string | null;
  tags: string[];
  related_exchanges: string[];
  related_symbols: string[];
  importance_score: number;
}

// 事件类型映射
export const EVENT_TYPE_LABELS: Record<string, string> = {
  announcement: '公告',
  listing: '上币',
  delisting: '下币',
  campaign: '活动',
  fee_change: '费率调整',
  product_launch: '产品上线',
  vip_policy: 'VIP政策',
  wallet_issue: '钱包问题',
  compliance: '合规',
  partnership: '合作',
  macro: '宏观',
  social_hype: '社媒热点',
  product: '产品更新',
  news: '行业新闻',
};

export const EVENT_TYPE_COLORS: Record<string, string> = {
  announcement: '#f85149',
  listing: '#3fb950',
  delisting: '#f85149',
  campaign: '#58a6ff',
  fee_change: '#d29922',
  product_launch: '#a371f7',
  vip_policy: '#db61a2',
  wallet_issue: '#f85149',
  compliance: '#8b949e',
  partnership: '#39d0d6',
  macro: '#8b949e',
  social_hype: '#a371f7',
  product: '#d29922',
  news: '#39d0d6',
};
