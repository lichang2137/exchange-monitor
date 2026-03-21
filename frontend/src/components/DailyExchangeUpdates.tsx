import type { ExchangeUpdate } from '../types';
import { ExchangeUpdateCard } from './ExchangeUpdateCard';

interface DailyExchangeUpdatesProps {
  updates: ExchangeUpdate[];
  loading: boolean;
}

export function DailyExchangeUpdates({ updates, loading }: DailyExchangeUpdatesProps) {
  if (loading) {
    return (
      <div className="daily-updates">
        <div className="section-title">🏛️ Daily Exchange Updates</div>
        <div className="exchange-cards-grid">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="exchange-card loading">
              <div className="skeleton skeleton-header"></div>
              <div className="skeleton skeleton-text"></div>
              <div className="skeleton skeleton-text"></div>
              <div className="skeleton skeleton-text short"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="daily-updates">
      <div className="section-title">🏛️ Daily Exchange Updates</div>
      <div className="exchange-cards-grid">
        {updates.map((update) => (
          <ExchangeUpdateCard key={update.exchange} update={update} />
        ))}
      </div>
    </div>
  );
}
