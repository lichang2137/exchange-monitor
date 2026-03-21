import { DashboardSummary } from '../types';

interface InsightSummaryProps {
  summary: DashboardSummary | null;
  loading: boolean;
}

export function InsightSummary({ summary, loading }: InsightSummaryProps) {
  if (loading) {
    return (
      <div className="insight-summary">
        <div className="section-title">📊 Insight Summary</div>
        <div className="insight-cards">
          {[1, 2, 3].map((i) => (
            <div key={i} className="insight-card loading">
              <div className="skeleton skeleton-title"></div>
              <div className="skeleton skeleton-text"></div>
              <div className="skeleton skeleton-text short"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!summary) return null;

  const { top_takeaways, top_movers, risk_summary } = summary;

  return (
    <div className="insight-summary">
      <div className="section-title">📊 Insight Summary</div>
      <div className="insight-cards">
        {/* 今日重点结论 */}
        <div className="insight-card">
          <div className="insight-card-title">💡 今日重点结论</div>
          <ul className="insight-list">
            {top_takeaways.length > 0 ? (
              top_takeaways.map((item, index) => (
                <li key={index}>{item}</li>
              ))
            ) : (
              <li>暂无数据</li>
            )}
          </ul>
        </div>

        {/* 业务线异动 */}
        <div className="insight-card">
          <div className="insight-card-title">📈 业务线异动</div>
          <div className="movers-grid">
            <div className="mover-item">
              <span className="mover-label">总量变化最大</span>
              <span className={`mover-value ${top_movers.total.change_pct >= 0 ? 'up' : 'down'}`}>
                {top_movers.total.exchange?.toUpperCase() || '-'}
                <span className="change-pct">
                  {top_movers.total.change_pct >= 0 ? '+' : ''}
                  {top_movers.total.change_pct.toFixed(1)}%
                </span>
              </span>
            </div>
            <div className="mover-item">
              <span className="mover-label">现货变化最大</span>
              <span className={`mover-value ${top_movers.spot.change_pct >= 0 ? 'up' : 'down'}`}>
                {top_movers.spot.exchange?.toUpperCase() || '-'}
                <span className="change-pct">
                  {top_movers.spot.change_pct >= 0 ? '+' : ''}
                  {top_movers.spot.change_pct.toFixed(1)}%
                </span>
              </span>
            </div>
            <div className="mover-item">
              <span className="mover-label">合约变化最大</span>
              <span className={`mover-value ${top_movers.futures.change_pct >= 0 ? 'up' : 'down'}`}>
                {top_movers.futures.exchange?.toUpperCase() || '-'}
                <span className="change-pct">
                  {top_movers.futures.change_pct >= 0 ? '+' : ''}
                  {top_movers.futures.change_pct.toFixed(1)}%
                </span>
              </span>
            </div>
          </div>
        </div>

        {/* 重点风险 */}
        <div className="insight-card risk">
          <div className="insight-card-title">⚠️ 重点风险</div>
          <div className="risk-stats">
            <div className="risk-stat">
              <span className="risk-value">{risk_summary.high_risk_events}</span>
              <span className="risk-label">高风险事件</span>
            </div>
            <div className="risk-stat">
              <span className="risk-value">{risk_summary.wallet_issues}</span>
              <span className="risk-label">钱包问题</span>
            </div>
            <div className="risk-stat">
              <span className="risk-value">{risk_summary.compliance_events}</span>
              <span className="risk-label">合规事件</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
