import { useState, useCallback } from 'react';
import { Header, ControlPanel, PriceChart, EventsList, EventModal, InsightSummary, DailyExchangeUpdates, EventTimeline, NewsWatch } from './components';
import { useExchangeData, useChartData, useEvents } from './hooks/useData';
import { useDashboardSummary, useExchangeUpdates, useNews } from './hooks/useDashboard';
import type { MarketType, ChartEvent, EventItem } from './types';
import './App.css';

function App() {
  // 状态管理
  const [marketType, setMarketType] = useState<MarketType>('total');
  const [selectedExchanges, setSelectedExchanges] = useState<string[]>(['binance', 'okx', 'bybit']);
  const [eventTypeFilter, setEventTypeFilter] = useState<string>('');
  const [selectedEvent, setSelectedEvent] = useState<EventItem | null>(null);
  const [highlightedEventId, setHighlightedEventId] = useState<string | null>(null);
  
  // 数据获取
  const { exchanges, filters, loading: dataLoading, error: dataError } = useExchangeData();
  
  // 时间范围计算（默认7天）
  const endTime = new Date().toISOString();
  const startTime = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString();
  
  const { chartData, loading: chartLoading, refetch: chartRefetch } = useChartData(
    marketType, 
    selectedExchanges,
    startTime,
    endTime
  );
  
  const { events, total, loading: eventsLoading, refetch: eventsRefetch } = useEvents(
    eventTypeFilter || undefined,
    undefined,
    startTime,
    endTime
  );

  // Dashboard 数据
  const { summary, refetch: summaryRefetch } = useDashboardSummary();
  const { updates, refetch: updatesRefetch } = useExchangeUpdates();
  const { news, loading: newsLoading } = useNews();

  // 处理器
  const handleExchangeToggle = useCallback((exchange: string) => {
    setSelectedExchanges(prev => {
      if (prev.includes(exchange)) {
        return prev.length > 1 ? prev.filter(e => e !== exchange) : prev;
      }
      return [...prev, exchange];
    });
  }, []);

  const handleRefresh = useCallback(() => {
    chartRefetch();
    eventsRefetch();
    summaryRefetch();
    updatesRefetch();
  }, [chartRefetch, eventsRefetch, summaryRefetch, updatesRefetch]);

  const handleChartEventClick = useCallback((event: ChartEvent) => {
    setHighlightedEventId(event.id);
    const fullEvent = events.find(e => e.id === event.id);
    if (fullEvent) {
      setSelectedEvent(fullEvent);
    }
  }, [events]);

  const handleEventClick = useCallback((event: EventItem) => {
    setSelectedEvent(event);
    setHighlightedEventId(event.id);
  }, []);

  const handleEventTypeChange = useCallback((type: string) => {
    setEventTypeFilter(type);
    setHighlightedEventId(null);
  }, []);

  if (dataError) {
    return (
      <div className="dashboard">
        <div style={{ padding: '40px', textAlign: 'center' }}>
          <h2 style={{ color: '#f85149' }}>❌ 错误</h2>
          <p style={{ color: '#8b949e', marginTop: '12px' }}>{dataError}</p>
          <p style={{ color: '#8b949e', marginTop: '8px' }}>
            请确保后端服务已启动：<code>uvicorn app.main:app --reload</code>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <Header />
      
      <ControlPanel
        marketType={marketType}
        onMarketTypeChange={setMarketType}
        selectedExchanges={selectedExchanges}
        onExchangeToggle={handleExchangeToggle}
        eventTypeFilter={eventTypeFilter}
        onEventTypeChange={handleEventTypeChange}
        exchanges={exchanges}
        filters={filters}
        onRefresh={handleRefresh}
      />
      
      {/* 主图区域 - 保持不变 */}
      <PriceChart
        data={chartData}
        loading={chartLoading}
        marketType={marketType}
        selectedExchanges={selectedExchanges}
        exchanges={exchanges}
        events={chartData?.events || []}
        highlightedEventId={highlightedEventId}
        onRefresh={handleRefresh}
        onEventClick={handleChartEventClick}
      />
      
      {/* 新增: Insight Summary */}
      <InsightSummary summary={summary} loading={!summary} />
      
      {/* 新增: Daily Exchange Updates */}
      <DailyExchangeUpdates updates={updates} loading={updates.length === 0 && !summary} />
      
      {/* 新增: Event Timeline */}
      <EventTimeline
        events={events}
        loading={eventsLoading}
        total={total}
        highlightedEventId={highlightedEventId}
        onEventClick={handleEventClick}
        onRefresh={eventsRefetch}
      />
      
      {/* 新增: News Watch (占位版) */}
      <NewsWatch news={news} loading={newsLoading} />
      
      {/* 保留: Event Modal */}
      <EventModal
        event={selectedEvent}
        onClose={() => setSelectedEvent(null)}
      />
    </div>
  );
}

export default App;
