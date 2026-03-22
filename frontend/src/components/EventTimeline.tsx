import type { EventItem } from '../types';
import { EVENT_TYPE_LABELS, EVENT_TYPE_COLORS } from '../types';

interface EventTimelineProps {
  events: EventItem[];
  loading: boolean;
  total: number;
  highlightedEventId: string | null;
  onEventClick: (event: EventItem) => void;
  onRefresh?: () => void;
  eventTypeFilter?: string;
  onEventTypeChange?: (type: string) => void;
}

const EXCHANGE_COLORS: Record<string, string> = {
  binance: '#F0B90B',
  okx: '#FFFFFF',
  bybit: '#FFAB00',
  bitget: '#00C077',
  hyperliquid: '#E84855',
};

const EVENT_TABS = [
  { id: '', label: '全部' },
  { id: 'announcement', label: '公告' },
  { id: 'listing', label: '上币' },
  { id: 'delisting', label: '下币' },
  { id: 'campaign', label: '活动' },
  { id: 'fee_change', label: '费率' },
  { id: 'product_launch', label: '产品' },
  { id: 'vip_policy', label: 'VIP' },
  { id: 'wallet_issue', label: '钱包' },
  { id: 'compliance', label: '合规' },
  { id: 'macro', label: '宏观' },
  { id: 'news', label: '行业' },
];

// 来源映射：内部标识 → 可读名称
const SOURCE_DISPLAY_NAMES: Record<string, string> = {
  migrated: '',  // 已废弃，由 exchange 推断
  // 其他已知来源直接映射
  binance: 'Binance 公告',
  okx: 'OKX 公告',
  bybit: 'Bybit 公告',
  bitget: 'Bitget 公告',
  hyperliquid: 'Hyperliquid 公告',
  coinglass: 'CoinGlass',
  binance_announcement: 'Binance 公告',
  okx_announcement: 'OKX 公告',
  bybit_announcement: 'Bybit 公告',
};

function getSourceDisplay(source: string | null | undefined, exchange: string): string {
  if (!source) return '';
  if (source === 'migrated') {
    // migrated = 来自交易所官方公告
    const exMap: Record<string, string> = {
      binance: 'Binance 公告',
      okx: 'OKX 公告',
      bybit: 'Bybit 公告',
      bitget: 'Bitget 公告',
      hyperliquid: 'Hyperliquid 公告',
    };
    return exMap[exchange] || '';
  }
  return SOURCE_DISPLAY_NAMES[source] || source;
}

function formatTime(ts: string): string {
  const date = new Date(ts);
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function EventTimeline({
  events,
  loading,
  total,
  highlightedEventId,
  onEventClick,
  onRefresh,
  eventTypeFilter = '',
  onEventTypeChange,
}: EventTimelineProps) {
  // 前端筛选 events（已由 App.tsx 按交易所筛选后传入）
  const filteredEvents = eventTypeFilter
    ? events.filter(e => e.event_type === eventTypeFilter)
    : events;

  return (
    <div className="event-timeline">
      <div className="timeline-header">
        <div className="section-title">📋 Event Timeline</div>
        <div className="timeline-stats">
          <span className="total-count">共 {total} 条</span>
          {onRefresh && (
            <button className="refresh-btn" onClick={onRefresh}>
              🔄 刷新
            </button>
          )}
        </div>
      </div>

      {/* Event Type Filter Tabs */}
      {onEventTypeChange && (
        <div className="event-type-tabs">
          {EVENT_TABS.map(tab => (
            <button
              key={tab.id}
              className={`event-tab ${eventTypeFilter === tab.id ? 'active' : ''}`}
              onClick={() => onEventTypeChange(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>
      )}

      {loading && filteredEvents.length === 0 ? (
        <div className="timeline-loading">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="timeline-item loading">
              <div className="skeleton skeleton-time"></div>
              <div className="skeleton skeleton-content"></div>
            </div>
          ))}
        </div>
      ) : filteredEvents.length === 0 ? (
        <div className="timeline-empty">
          <p>暂无事件数据</p>
        </div>
      ) : (
        <div className="timeline-list">
          {filteredEvents.map((event) => (
            <div
              key={event.id}
              className={`timeline-item ${highlightedEventId === event.id ? 'highlighted' : ''}`}
              onClick={() => onEventClick(event)}
            >
              <div className="timeline-time">{formatTime(event.ts)}</div>
              <div className="timeline-content">
                <div className="timeline-header-row">
                  <span
                    className="event-type-badge"
                    style={{
                      backgroundColor: EVENT_TYPE_COLORS[event.event_type] || '#666',
                    }}
                  >
                    {EVENT_TYPE_LABELS[event.event_type] || event.event_type}
                  </span>
                  <span
                    className="exchange-badge"
                    style={{ color: EXCHANGE_COLORS[event.exchange] || '#fff' }}
                  >
                    {event.exchange.toUpperCase()}
                  </span>
                </div>
                <div className="timeline-title">{event.title}</div>
                {event.summary && (
                  <div className="timeline-summary">{event.summary}</div>
                )}
                {(() => {
                  const displaySrc = getSourceDisplay(event.source, event.exchange);
                  return displaySrc ? (
                    <div className="timeline-source">来源: {displaySrc}</div>
                  ) : null;
                })()}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
