import type { EventItem } from '../types';
import { EVENT_TYPE_COLORS, EVENT_TYPE_LABELS } from '../types';
import dayjs from 'dayjs';

interface EventModalProps {
  event: EventItem | null;
  onClose: () => void;
}

export function EventModal({ event, onClose }: EventModalProps) {
  if (!event) return null;

  return (
    <div className="event-modal" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <span 
            className="event-type"
            style={{ 
              backgroundColor: `${EVENT_TYPE_COLORS[event.event_type]}20`,
              color: EVENT_TYPE_COLORS[event.event_type]
            }}
          >
            {EVENT_TYPE_LABELS[event.event_type] || event.event_type}
          </span>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>
        
        <h3 style={{ marginBottom: '12px', color: '#e6edf3' }}>{event.title}</h3>
        
        <div className="modal-body">
          <p style={{ marginBottom: '8px' }}>
            <strong style={{ color: '#8b949e' }}>时间：</strong>
            <span style={{ color: '#e6edf3' }}>
              {dayjs(event.ts).format('YYYY-MM-DD HH:mm')}
            </span>
          </p>
          <p style={{ marginBottom: '8px' }}>
            <strong style={{ color: '#8b949e' }}>来源：</strong>
            <span style={{ color: '#e6edf3' }}>{event.exchange}</span>
          </p>
          {event.summary && (
            <p style={{ marginTop: '16px', color: '#e6edf3', lineHeight: 1.6 }}>
              {event.summary}
            </p>
          )}
          {event.url && (
            <p style={{ marginTop: '12px' }}>
              <a href={event.url} target="_blank" rel="noopener noreferrer" style={{ color: '#58a6ff' }}>
                查看原文 →
              </a>
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
