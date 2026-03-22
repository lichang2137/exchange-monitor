import type { MarketType, Exchange, Filters } from '../types';

// 事件类型选项
export const EVENT_TYPE_OPTIONS = [
  { id: '', label: '全部', color: '#58a6ff' },
  { id: 'announcement', label: '公告', color: '#f85149' },
  { id: 'listing', label: '上币', color: '#3fb950' },
  { id: 'delisting', label: '下币', color: '#f85149' },
  { id: 'campaign', label: '活动', color: '#58a6ff' },
  { id: 'fee_change', label: '费率调整', color: '#d29922' },
  { id: 'product_launch', label: '产品上线', color: '#a371f7' },
  { id: 'vip_policy', label: 'VIP政策', color: '#db61a2' },
  { id: 'wallet_issue', label: '钱包问题', color: '#f85149' },
  { id: 'compliance', label: '合规', color: '#8b949e' },
  { id: 'partnership', label: '合作', color: '#39d0d6' },
  { id: 'macro', label: '宏观', color: '#8b949e' },
  { id: 'social_hype', label: '社媒热点', color: '#a371f7' },
  { id: 'product', label: '产品更新', color: '#d29922' },
  { id: 'news', label: '行业新闻', color: '#39d0d6' },
];

interface ControlPanelProps {
  marketType: MarketType;
  onMarketTypeChange: (type: MarketType) => void;
  selectedExchanges: string[];
  onExchangeToggle: (exchange: string) => void;
  eventTypeFilter: string;
  onEventTypeChange: (type: string) => void;
  exchanges: Exchange[];
  filters: Filters | null;
  onRefresh: () => void;
}

export function ControlPanel({
  marketType,
  onMarketTypeChange,
  selectedExchanges,
  onExchangeToggle,
  eventTypeFilter,
  onEventTypeChange,
  exchanges,
  filters,
  onRefresh,
}: ControlPanelProps) {
  const marketTypes = [
    { key: 'spot', label: '现货' },
    { key: 'futures', label: '合约' },

  ];

  return (
    <div className="controls">
      {/* 市场类型切换 */}
      <div className="control-group">
        <span className="control-label">市场类型</span>
        <div className="toggle-group">
          {marketTypes.map(t => (
            <button
              key={t.key}
              className={`toggle-btn ${marketType === t.key ? 'active' : ''}`}
              onClick={() => onMarketTypeChange(t.key as MarketType)}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* 交易所选择 */}
      <div className="control-group">
        <span className="control-label">交易所</span>
        <div className="checkbox-group">
          {exchanges.map(ex => (
            <label key={ex.id} className="checkbox-item">
              <input
                type="checkbox"
                checked={selectedExchanges.includes(ex.id)}
                onChange={() => onExchangeToggle(ex.id)}
              />
              <span 
                className="exchange-badge" 
                style={{ 
                  background: ex.id === 'okx' ? '#1E3A8A' : 
                             ex.id === 'bybit' ? '#F97316' : 
                             ex.id === 'bitget' ? '#38BDF8' : 
                             ex.id === 'hyperliquid' ? '#22C55E' : 
                             ex.color 
                }}
              />
              {ex.name}
            </label>
          ))}
        </div>
      </div>

      {/* 事件类型筛选 - 在控制面板中也保留 */}
      <div className="control-group">
        <span className="control-label">事件类型</span>
        <select 
          className="filter-select"
          value={eventTypeFilter}
          onChange={(e) => onEventTypeChange(e.target.value)}
        >
          {EVENT_TYPE_OPTIONS.map(option => (
            <option key={option.id} value={option.id}>{option.label}</option>
          ))}
        </select>
      </div>

      {/* 刷新按钮 */}
      <div className="control-group" style={{ marginLeft: 'auto' }}>
        <button className="refresh-btn" onClick={onRefresh}>
          🔄 刷新数据
        </button>
      </div>
    </div>
  );
}
