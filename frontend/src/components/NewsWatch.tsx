import type { NewsItem } from '../types';

interface NewsWatchProps {
  news: NewsItem[];
  loading: boolean;
}

const NEWS_TYPE_LABELS: Record<string, string> = {
  macro: '宏观',
  market: '市场',
  industry: '行业',
  hot: '热点',
};

const NEWS_TYPE_COLORS: Record<string, string> = {
  macro: '#8b949e',
  market: '#3fb950',
  industry: '#58a6ff',
  hot: '#a371f7',
};

function formatTime(ts: string | null): string {
  if (!ts) return '-';
  const date = new Date(ts);
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function NewsWatch({ news, loading }: NewsWatchProps) {
  if (loading) {
    return (
      <div className="news-watch">
        <div className="section-title">📰 Market & News Watch</div>
        <div className="news-placeholder">
          <div className="placeholder-content">
            <div className="placeholder-icon">🔔</div>
            <div className="placeholder-title">新闻模块开发中</div>
            <div className="placeholder-desc">
              正在接入新闻数据源，即将支持：
            </div>
            <ul className="placeholder-features">
              <li>热点新闻聚合</li>
              <li>宏观事件追踪</li>
              <li>行业动态监控</li>
              <li>社媒热点分析</li>
            </ul>
          </div>
        </div>
        <div className="news-list">
          {[1, 2, 3].map((i) => (
            <div key={i} className="news-item loading">
              <div className="skeleton skeleton-news"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="news-watch">
      <div className="section-title">📰 Market & News Watch</div>
      
      {news.length === 0 ? (
        <div className="news-placeholder">
          <div className="placeholder-content">
            <div className="placeholder-icon">🔔</div>
            <div className="placeholder-title">暂无新闻数据</div>
            <div className="placeholder-desc">
              新闻模块即将上线，支持宏观、市场、行业、热点追踪
            </div>
          </div>
        </div>
      ) : (
        <div className="news-list">
          {news.slice(0, 10).map((item) => (
            <div key={item.id} className="news-item">
              <div className="news-header">
                <span
                  className="news-type-badge"
                  style={{ backgroundColor: NEWS_TYPE_COLORS[item.news_type] || '#666' }}
                >
                  {NEWS_TYPE_LABELS[item.news_type] || item.news_type}
                </span>
                <span className="news-time">{formatTime(item.published_at)}</span>
              </div>
              <div className="news-title">{item.title}</div>
              {item.summary && (
                <div className="news-summary">{item.summary}</div>
              )}
              <div className="news-footer">
                {item.source && <span className="news-source">{item.source}</span>}
                {item.related_symbols.length > 0 && (
                  <span className="news-symbols">
                    {item.related_symbols.slice(0, 3).join(', ')}
                  </span>
                )}
                {item.importance_score > 0 && (
                  <span className="news-score">
                    重要度: {item.importance_score}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
