import { useState, useEffect } from 'react';
import { dashboardApi, newsApi } from '../services/api';
import type { DashboardSummary, ExchangeUpdate, NewsItem } from '../types';

interface UseDashboardSummaryReturn {
  summary: DashboardSummary | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useDashboardSummary(date?: string): UseDashboardSummaryReturn {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refetchIndex, setRefetchIndex] = useState(0);

  const refetch = () => setRefetchIndex(prev => prev + 1);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const data = await dashboardApi.getSummary(date);
        setSummary(data);
        setError(null);
      } catch (err) {
        setError('获取摘要失败');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [date, refetchIndex]);

  return { summary, loading, error, refetch };
}

interface UseExchangeUpdatesReturn {
  updates: ExchangeUpdate[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useExchangeUpdates(date?: string): UseExchangeUpdatesReturn {
  const [updates, setUpdates] = useState<ExchangeUpdate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refetchIndex, setRefetchIndex] = useState(0);

  const refetch = () => setRefetchIndex(prev => prev + 1);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const data = await dashboardApi.getExchangeUpdates(date);
        setUpdates(data);
        setError(null);
      } catch (err) {
        setError('获取交易所动态失败');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [date, refetchIndex]);

  return { updates, loading, error, refetch };
}

interface UseNewsReturn {
  news: NewsItem[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useNews(newsType?: string, range: string = '7d'): UseNewsReturn {
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refetchIndex, setRefetchIndex] = useState(0);

  const refetch = () => setRefetchIndex(prev => prev + 1);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const data = await newsApi.getNews(newsType, range);
        setNews(data);
        setError(null);
      } catch (err) {
        setError('获取新闻失败');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [newsType, range, refetchIndex]);

  return { news, loading, error, refetch };
}
