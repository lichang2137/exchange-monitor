// 类型定义 - API v2

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
  ts: string;
  exchange: string;
  event_type: string;
  title: string;
}

export interface ChartData {
  btc: BtcPrice[];
  volumes: ExchangeVolume[];
  events: ChartEvent[];
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
export type MarketType = 'spot' | 'futures' | 'total';

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
