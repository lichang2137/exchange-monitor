import { useState, useEffect } from 'react';
import type { MarketType, Exchange, Filters, ChartData, EventItem } from '../types';
import { exchangesApi, filtersApi, chartApi, eventsApi } from '../services/api';

interface UseExchangeDataReturn {
  exchanges: Exchange[];
  filters: Filters | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useExchangeData(): UseExchangeDataReturn {
  const [exchanges, setExchanges] = useState<Exchange[]>([]);
  const [filters, setFilters] = useState<Filters | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refetchIndex, setRefetchIndex] = useState(0);

  const refetch = () => setRefetchIndex(prev => prev + 1);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [exchangesData, filtersData] = await Promise.all([
          exchangesApi.getExchanges(),
          filtersApi.getFilters(),
        ]);
        setExchanges(exchangesData);
        setFilters(filtersData);
        setError(null);
      } catch (err) {
        setError('获取数据失败，请检查后端服务是否启动');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [refetchIndex]);

  return { exchanges, filters, loading, error, refetch };
}

interface UseChartDataReturn {
  chartData: ChartData | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useChartData(
  marketType: MarketType,
  selectedExchanges: string[],
  startTime?: string,
  endTime?: string
): UseChartDataReturn {
  const [chartData, setChartData] = useState<ChartData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refetchIndex, setRefetchIndex] = useState(0);

  const refetch = () => setRefetchIndex(prev => prev + 1);

  useEffect(() => {
    const fetchData = async () => {
      if (selectedExchanges.length === 0) return;
      
      try {
        setLoading(true);
        const data = await chartApi.getChartData(marketType, selectedExchanges, startTime, endTime);
        setChartData(data);
        setError(null);
      } catch (err) {
        setError('获取图表数据失败');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [marketType, selectedExchanges.join(','), startTime, endTime, refetchIndex]);

  return { chartData, loading, error, refetch };
}

interface UseEventsReturn {
  events: EventItem[];
  total: number;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useEvents(
  eventType?: string,
  exchange?: string,
  startTime?: string,
  endTime?: string
): UseEventsReturn {
  const [events, setEvents] = useState<EventItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refetchIndex, setRefetchIndex] = useState(0);

  const refetch = () => setRefetchIndex(prev => prev + 1);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const data = await eventsApi.getEvents(eventType, exchange, startTime, endTime);
        setEvents(data.events);
        setTotal(data.total);
        setError(null);
      } catch (err) {
        setError('获取事件失败');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [eventType, exchange, startTime, endTime, refetchIndex]);

  return { events, total, loading, error, refetch };
}
