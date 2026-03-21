import type { EventItem } from '../types';
import { EVENT_TYPE_LABELS, EVENT_TYPE_COLORS } from '../types';

interface EventTimelineProps {
  events: EventItem[];
  loading: boolean;
  total: number;
  highlightedEventId: string | null;
  onEventClick: (event: EventItem) => void;
  onRefresh?: () => void;
}

const EXCHANGE_COLORS: Record<string, string> = {
  binance: '#F0B90B',
  okx: '#FFFFFF',
  bybit: '#FFAB00',
  bitget: '#00C077',
  hyperliquid: '#E84855',
};

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
}: EventTimelineProps) {
  if (loading && events.length === 0) {
    return (
      <div className="event-timeline">
        <div className="section-title">📋 Event Timeline</div>
        <div className="timeline-loading">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="timeline-item loading">
              <div className="skeleton skeleton-time"></div>
              <div className="skeleton skeleton-content"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="event-timeline">
      <div className="timeline-header">
        <div className="section-title">📋 Event Timeline</div>
        <div className="timeline-stats">
          <span className="total-count">共 {total} 条事件</span>
          {onRefresh && (
            <button className="refresh-btn" onClick={onRefresh}>
              🔄 刷新
            </button>
          )}
        </div>
      </div>

      {events.length === 0 ? (
        <div className="timeline-empty">
          <p>暂无事件数据</p>
        </div>
      ) : (
        <div className="timeline-list">
          {events.map((event) => (
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
                {event.source && (
                  <div className="timeline-source">来源: {event.source}</div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
