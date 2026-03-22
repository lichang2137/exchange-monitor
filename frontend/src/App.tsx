import { useState, useCallback } from 'react';
import { Header, ControlPanel, PriceChart, EventsList, EventModal, InsightSummary, EventTimeline, NewsWatch } from './components';
import { useExchangeData, useChartData, useEvents } from './hooks/useData';
import { useDashboardSummary, useExchangeUpdates, useNews } from './hooks/useDashboard';
import type { MarketType, ChartEvent, EventItem } from './types';
import './App.css';

function App() {
  // 状态管理
  const [marketType, setMarketType] = useState<MarketType>('spot');
  const [selectedExchanges, setSelectedExchanges] = useState<string[]>(['binance', 'okx', 'bybit', 'bitget', 'hyperliquid']);
  const [eventTypeFilter, setEventTypeFilter] = useState<string>('');
  const [selectedEvent, setSelectedEvent] = useState<EventItem | null>(null);
  const [highlightedEventId, setHighlightedEventId] = useState<string | null>(null);
  
  // 数据获取
  const { exchanges, filters, loading: dataLoading, error: dataError } = useExchangeData();
  
  const { chartData, loading: chartLoading, refetch: chartRefetch } = useChartData(selectedExchanges, 7);
  
  // Events - 前端按选中交易所过滤
  const { events, total, loading: eventsLoading, refetch: eventsRefetch } = useEvents(
    eventTypeFilter || undefined,
    undefined  // exchange 由前端过滤
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
    const fullEvent = (chartData?.events || []).find(e => e.id === event.id);
    if (fullEvent) {
      setSelectedEvent({
        id: fullEvent.id,
        ts: fullEvent.ts,
        exchange: fullEvent.exchange,
        event_type: fullEvent.event_type,
        title: fullEvent.title,
        summary: null,
        source: null,
        url: null,
      });
    }
  }, [chartData]);

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
      
      {/* 主图 */}
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
      
      {/* Insight Summary */}
      <InsightSummary summary={summary} loading={!summary} selectedExchanges={selectedExchanges} />
      
      {/* Event Timeline - 按选中交易所过滤 */}
      <EventTimeline
        events={events.filter(e => selectedExchanges.includes(e.exchange))}
        loading={eventsLoading}
        total={total}
        highlightedEventId={highlightedEventId}
        onEventClick={handleEventClick}
        onRefresh={eventsRefetch}
        eventTypeFilter={eventTypeFilter}
        onEventTypeChange={handleEventTypeChange}
      />
      
      {/* News Watch */}
      <NewsWatch news={news} loading={newsLoading} />
      
      {/* Event Modal */}
      <EventModal
        event={selectedEvent}
        onClose={() => setSelectedEvent(null)}
      />
    </div>
  );
}

export default App;
