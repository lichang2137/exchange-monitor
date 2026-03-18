import axios from 'axios';
import type { ChartData, EventsResponse, Exchange, Filters, MarketType } from '../types';

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
});

export const chartApi = {
  getChartData: async (
    marketType: MarketType = 'total',
    exchanges?: string[],
    startTime?: string,
    endTime?: string
  ): Promise<ChartData> => {
    const params = new URLSearchParams();
    params.append('market_type', marketType);
    if (exchanges?.length) {
      params.append('exchanges', exchanges.join(','));
    }
    if (startTime) params.append('start_time', startTime);
    if (endTime) params.append('end_time', endTime);
    
    const { data } = await api.get<ChartData>(`/chart?${params}`);
    return data;
  },
};

export const eventsApi = {
  getEvents: async (
    eventType?: string,
    exchange?: string,
    startTime?: string,
    endTime?: string,
    page = 1,
    pageSize = 20
  ): Promise<EventsResponse> => {
    const params = new URLSearchParams();
    if (eventType) params.append('event_type', eventType);
    if (exchange) params.append('exchange', exchange);
    if (startTime) params.append('start_time', startTime);
    if (endTime) params.append('end_time', endTime);
    params.append('page', String(page));
    params.append('page_size', String(pageSize));
    
    const { data } = await api.get<EventsResponse>(`/events?${params}`);
    return data;
  },
};

export const exchangesApi = {
  getExchanges: async (): Promise<Exchange[]> => {
    const { data } = await api.get<Exchange[]>('/exchanges');
    return data;
  },
};

export const filtersApi = {
  getFilters: async (): Promise<Filters> => {
    const { data } = await api.get<Filters>('/filters');
    return data;
  },
};

export default api;
