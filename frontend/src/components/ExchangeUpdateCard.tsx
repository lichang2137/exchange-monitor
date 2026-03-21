import type { ExchangeUpdate } from '../types';
import { EVENT_TYPE_LABELS, EVENT_TYPE_COLORS } from '../types';

interface ExchangeUpdateCardProps {
  update: ExchangeUpdate;
}

const EXCHANGE_COLORS: Record<string, string> = {
  binance: '#F0B90B',
  okx: '#1E3A8A',
  bybit: '#F97316',
  bitget: '#38BDF8',
  hyperliquid: '#22C55E',
};

const EXCHANGE_NAMES: Record<string, string> = {
  binance: 'Binance',
  okx: 'OKX',
  bybit: 'Bybit',
  bitget: 'Bitget',
  hyperliquid: 'Hyperliquid',
};

function formatVolume(volume: number | null): string {
  if (volume === null || volume === 0) return '-';
  if (volume >= 1e9) return `$${(volume / 1e9).toFixed(1)}B`;
  if (volume >= 1e6) return `$${(volume / 1e6).toFixed(1)}M`;
  if (volume >= 1e3) return `$${(volume / 1e3).toFixed(1)}K`;
  return `$${volume.toFixed(0)}`;
}

function formatChange(pct: number | null): string {
  if (pct === null || pct === 0) return '-';
  return `${pct >= 0 ? '+' : ''}${pct.toFixed(1)}%`;
}

function getChangeClass(pct: number | null): string {
  if (pct === null || pct === 0) return 'neutral';
  return pct > 0 ? 'up' : 'down';
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

export function ExchangeUpdateCard({ update }: ExchangeUpdateCardProps) {
  const color = EXCHANGE_COLORS[update.exchange] || '#666';
  const name = EXCHANGE_NAMES[update.exchange] || update.exchange;
  const isActive = update.event_count > 0;

  return (
    <div className="exchange-card" style={{ borderTopColor: color }}>
      {/* Header */}
      <div className="exchange-header">
        <div className="exchange-title">
          <span className="exchange-name" style={{ color }}>
            {name}
          </span>
          <span className={`status-badge ${isActive ? 'active' : 'inactive'}`}>
            {isActive ? '● Active' : '○ Inactive'}
          </span>
        </div>
        <div className="event-count">
          {update.event_count} events today
        </div>
      </div>

      {/* Volume Stats */}
      <div className="volume-stats">
        <div className="stat-row">
          <span className="stat-label">Total Vol</span>
          <span className="stat-value">{formatVolume(update.total_volume)}</span>
          <span className={`stat-change ${getChangeClass(update.total_change_pct)}`}>
            {formatChange(update.total_change_pct)}
          </span>
        </div>
        <div className="stat-row">
          <span className="stat-label">Spot Vol</span>
          <span className="stat-value">{formatVolume(update.spot_volume)}</span>
          <span className={`stat-change ${getChangeClass(update.spot_change_pct)}`}>
            {formatChange(update.spot_change_pct)}
          </span>
        </div>
        <div className="stat-row">
          <span className="stat-label">Futures Vol</span>
          <span className="stat-value">{formatVolume(update.futures_volume)}</span>
          <span className={`stat-change ${getChangeClass(update.futures_change_pct)}`}>
            {formatChange(update.futures_change_pct)}
          </span>
        </div>
        <div className="stat-row">
          <span className="stat-label">Futures OI</span>
          <span className="stat-value">{formatVolume(update.futures_oi)}</span>
          <span className={`stat-change ${getChangeClass(update.oi_change_pct)}`}>
            {formatChange(update.oi_change_pct)}
          </span>
        </div>
      </div>

      {/* Top Events */}
      <div className="top-events-section">
        <div className="section-label">Top Events</div>
        {update.top_events.length > 0 ? (
          <div className="events-list">
            {update.top_events.slice(0, 3).map((event) => (
              <div key={event.id} className="event-row">
                <span
                  className="event-type-badge"
                  style={{
                    backgroundColor: EVENT_TYPE_COLORS[event.event_type] || '#666',
                  }}
                >
                  {EVENT_TYPE_LABELS[event.event_type] || event.event_type}
                </span>
                <span className="event-title" title={event.title}>
                  {event.title}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <div className="no-events">No events today</div>
        )}
      </div>

      {/* Summary */}
      {update.summary_line && (
        <div className="summary-section">
          <div className="section-label">Summary</div>
          <div className="summary-text">{update.summary_line}</div>
        </div>
      )}

      {/* Risk Warning */}
      {update.high_priority_event_count > 0 && (
        <div className="risk-warning">
          ⚠️ {update.high_priority_event_count} high priority events
        </div>
      )}
    </div>
  );
}
