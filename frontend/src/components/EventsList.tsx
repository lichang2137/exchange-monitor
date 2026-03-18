import { useState, useRef, useEffect } from 'react';
import type { ChartEvent, EventItem } from '../types';
import { EVENT_TYPE_COLORS, EVENT_TYPE_LABELS } from '../types';
import dayjs from 'dayjs';

interface EventsListProps {
  events: EventItem[];
  loading: boolean;
  total: number;
  highlightedEventId: string | null;
  onEventClick: (event: EventItem) => void;
}

// 事件类型选项
const EVENT_TYPE_OPTIONS = [
  { id: '', label: '全部' },
  { id: 'announcement', label: '公告' },
  { id: 'listing', label: '上币' },
  { id: 'delisting', label: '下币' },
  { id: 'campaign', label: '活动' },
  { id: 'fee_change', label: '费率调整' },
  { id: 'product_launch', label: '产品上线' },
  { id: 'vip_policy', label: 'VIP政策' },
  { id: 'wallet_issue', label: '钱包问题' },
  { id: 'compliance', label: '合规' },
  { id: 'partnership', label: '合作' },
  { id: 'macro', label: '宏观' },
  { id: 'social_hype', label: '社媒热点' },
  { id: 'product', label: '产品更新' },
  { id: 'news', label: '行业新闻' },
];

export function EventsList({ events, loading, total, highlightedEventId, onEventClick }: EventsListProps) {
  const listRef = useRef<HTMLDivElement>(null);
  const eventItemRefs = useRef<Map<string, HTMLDivElement>>(new Map());

  // 当高亮事件变化时，自动滚动到对应位置
  useEffect(() => {
    if (highlightedEventId) {
      const element = eventItemRefs.current.get(highlightedEventId);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  }, [highlightedEventId]);

  if (loading) {
    return (
      <div className="events-section">
        <div className="events-header">
          <h2>📊 事件时间流</h2>
        </div>
        <div className="events-list" style={{ padding: '40px', textAlign: 'center' }}>
          <span style={{ color: '#8b949e' }}>加载中...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="events-section">
      <div className="events-header">
        <h2>📊 事件时间流</h2>
        <span style={{ color: '#8b949e', fontSize: '14px' }}>
          共 {total} 条
        </span>
      </div>

      <div className="events-list" ref={listRef}>
        {events.length === 0 ? (
          <div style={{ padding: '40px', textAlign: 'center', color: '#8b949e' }}>
            暂无事件数据
          </div>
        ) : (
          events.map(event => (
            <div 
              key={event.id}
              ref={(el) => {
                if (el) eventItemRefs.current.set(event.id, el);
              }}
              className={`event-item ${highlightedEventId === event.id ? 'highlighted' : ''}`}
              onClick={() => onEventClick(event)}
              id={`event-item-${event.id}`}
            >
              <span className="event-time">
                {dayjs(event.ts).format('YYYY-MM-DD HH:mm')}
              </span>
              <span 
                className="event-type"
                style={{ 
                  backgroundColor: `${EVENT_TYPE_COLORS[event.event_type] || '#58a6ff'}20`,
                  color: EVENT_TYPE_COLORS[event.event_type] || '#58a6ff'
                }}
              >
                {EVENT_TYPE_LABELS[event.event_type] || event.event_type}
              </span>
              <div className="event-content">
                <div className="event-title">{event.title}</div>
                <div className="event-exchange">{event.exchange}</div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

// 独立的筛选组件（供外部使用）
export { EVENT_TYPE_OPTIONS };
