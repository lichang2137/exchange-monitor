import { DashboardSummary } from '../types';
import type { OIData } from '../types';

interface InsightSummaryProps {
  summary: DashboardSummary | null;
  loading: boolean;
  selectedExchanges?: string[];
  oiData?: OIData[];
  latestPrice?: number;
  priceChange?: number;
}

function formatUSD(val: number | undefined | null): string {
  if (!val) return 'N/A';
  if (val >= 1e9) return `$${(val/1e9).toFixed(2)}B`;
  if (val >= 1e6) return `$${(val/1e6).toFixed(2)}M`;
  return `$${val.toFixed(0)}`;
}

function generateInsights(
  oiData: OIData[] | undefined,
  selectedExchanges: string[]
): string[] {
  const insights: string[] = [];

  if (!oiData || oiData.length === 0) {
    insights.push('暂无显著异动');
    return insights;
  }

  // 1. 全网 OI 概览
  const totalOI = oiData.reduce((sum, ex) => sum + (ex.oi_usd || 0), 0);
  const topOI = [...oiData].sort((a, b) => (b.oi_usd || 0) - (a.oi_usd || 0));
  if (topOI[0]) {
    insights.push(`全网 BTC 合约 OI：${formatUSD(totalOI)}`);
    insights.push(`最大持仓交易所：${topOI[0].exchange.toUpperCase()}（${formatUSD(topOI[0].oi_usd)}）`);
  }

  // 2. 资金费率异动（> 0.01% 或 < -0.01%）
  const fundingAlerts = oiData.filter(ex => ex.funding_rate !== null && Math.abs(ex.funding_rate) > 0.0001);
  if (fundingAlerts.length > 0) {
    fundingAlerts.forEach(ex => {
      const rate = (ex.funding_rate! * 100).toFixed(4);
      insights.push(`${ex.exchange.toUpperCase()} 资金费率：${rate}%`);
    });
  } else {
    insights.push('各所资金费率整体平稳（±0.01% 内）');
  }

  // 3. OI 分布异常（最大所 vs 最小所比值）
  if (topOI.length >= 2) {
    const ratio = topOI[0].oi_usd / topOI[topOI.length - 1].oi_usd;
    if (ratio > 5) {
      insights.push(`${topOI[0].exchange.toUpperCase()} OI 集中度偏高（比其他所高 ${ratio.toFixed(1)} 倍）`);
    }
  }

  return insights.length > 0 ? insights : ['暂无显著异动'];
}

export function InsightSummary({ 
  summary, 
  loading, 
  selectedExchanges = [],
  oiData,
  latestPrice,
  priceChange,
}: InsightSummaryProps) {
  const insights = generateInsights(oiData, selectedExchanges);

  if (loading) {
    return (
      <div className="insight-summary">
        <div className="section-title">📊 Insight Summary</div>
        <div className="skeleton-text" style={{ height: 80 }} />
      </div>
    );
  }

  return (
    <div className="insight-summary">
      <div className="section-title">📊 Insight Summary</div>
      <div className="insight-content">
        {insights.map((insight, idx) => (
          <div key={idx} className="insight-item">
            {insight}
          </div>
        ))}
      </div>
    </div>
  );
}
