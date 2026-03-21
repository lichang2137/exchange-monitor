import type { ExchangeUpdate } from '../types';
import { EVENT_TYPE_LABELS } from '../types';

interface DailyExchangeUpdatesProps {
  updates: ExchangeUpdate[];
  loading: boolean;
}

const EXCHANGE_COLORS: Record<string, string> = {
  binance: '#F0B90B',
  okx: '#FFFFFF',
  bybit: '#FFAB00',
  bitget: '#00C077',
  hyperliquid: '#E84855',
};

const EXCHANGE_NAMES: Record<string, string> = {
  binance: 'Binance',
  okx: 'OKX',
  bybit: 'Bybit',
  bitget: 'Bitget',
  hyperliquid: 'Hyperliquid',
};

function formatVolume(volume: number): string {
  if (volume >= 1e9) {
    return `$${(volume / 1e9).toFixed(1)}B`;
  } else if (volume >= 1e6) {
    return `$${(volume / 1e6).toFixed(1)}M`;
  } else if (volume >= 1e3) {
    return `$${(volume / 1e3).toFixed(1)}K`;
  }
  return `$${volume.toFixed(0)}`;
}

export function DailyExchangeUpdates({ updates, loading }: DailyExchangeUpdatesProps) {
  if (loading) {
    return (
      <div className="daily-updates">
        <div className="section-title">🏛️ Daily Exchange Updates</div>
        <div className="exchange-cards">
          {[1, 2, 3].map((i) => (
            <div key={i} className="exchange-card loading">
              <div className="skeleton skeleton-header"></div>
              <div className="skeleton skeleton-text"></div>
              <div className="skeleton skeleton-text"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="daily-updates">
      <div className="section-title">🏛️ Daily Exchange Updates</div>
      <div className="exchange-cards">
        {updates.map((update) => (
          <div
            key={update.exchange}
            className="exchange-card"
            style={{ borderTopColor: EXCHANGE_COLORS[update.exchange] || '#666' }}
          >
            <div className="exchange-header">
              <span
                className="exchange-name"
                style={{ color: EXCHANGE_COLORS[update.exchange] || '#fff' }}
              >
                {EXCHANGE_NAMES[update.exchange] || update.exchange}
              </span>
              <span className="event-count">{update.event_count} 事件</span>
            </div>

            <div className="volume-summary">
              <div className="volume-item">
                <span className="volume-label">总量</span>
                <span className="volume-value">{formatVolume(update.total_volume)}</span>
                <span className={`change ${update.total_change_pct >= 0 ? 'up' : 'down'}`}>
                  {update.total_change_pct >= 0 ? '+' : ''}{update.total_change_pct.toFixed(1)}%
                </span>
              </div>
              <div className="volume-item">
                <span className="volume-label">现货</span>
                <span className="volume-value">{formatVolume(update.spot_volume)}</span>
                <span className={`change ${update.spot_change_pct >= 0 ? 'up' : 'down'}`}>
                  {update.spot_change_pct >= 0 ? '+' : ''}{update.spot_change_pct.toFixed(1)}%
                </span>
              </div>
              <div className="volume-item">
                <span className="volume-label">合约</span>
                <span className="volume-value">{formatVolume(update.futures_volume)}</span>
                <span className={`change ${update.futures_change_pct >= 0 ? 'up' : 'down'}`}>
                  {update.futures_change_pct >= 0 ? '+' : ''}{update.futures_change_pct.toFixed(1)}%
                </span>
              </div>
            </div>

            {update.top_events.length > 0 ? (
              <div className="top-events">
                <div className="top-events-title">📌 重点事件</div>
                {update.top_events.slice(0, 3).map((event) => (
                  <div key={event.id} className="event-item">
                    <span className="event-type-badge">
                      {EVENT_TYPE_LABELS[event.event_type] || event.event_type}
                    </span>
                    <span className="event-title">{event.title}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="no-events">暂无重点事件</div>
            )}

            {update.high_risk_event_count > 0 && (
              <div className="risk-warning">
                ⚠️ {update.high_risk_event_count} 条高风险事件
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
