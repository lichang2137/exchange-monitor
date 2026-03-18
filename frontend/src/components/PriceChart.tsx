import { useCallback, useRef } from 'react';
import ReactECharts from 'echarts-for-react';
import type { EChartsOption } from 'echarts';
import type { ChartData, MarketType, Exchange, ChartEvent } from '../types';
import { EVENT_TYPE_COLORS } from '../types';
import dayjs from 'dayjs';

interface PriceChartProps {
  data: ChartData | null;
  loading: boolean;
  marketType: MarketType;
  selectedExchanges: string[];
  exchanges: Exchange[];
  events: ChartEvent[];
  highlightedEventId: string | null;
  onRefresh: () => void;
  onEventClick: (event: ChartEvent) => void;
}

// 交易所颜色
const EXCHANGE_COLORS: Record<string, string> = {
  binance: '#F0B90B',
  okx: '#1E3A8A',
  bybit: '#F97316',
  bitget: '#38BDF8',
  hyperliquid: '#22C55E',
};

// 重要程度大小映射（从事件ID推断，evt_5=高，evt_3=中，evt_1=低）
const getImportanceFromId = (id: string): number => {
  const num = parseInt(id.replace('evt_', ''));
  if (num >= 15) return 5;  // critical
  if (num >= 10) return 4;  // high
  if (num >= 5) return 3;    // medium
  return 2;                   // low
};

const IMPORTANCE_SIZE: Record<number, number> = {
  5: 18,  // critical
  4: 14,  // high
  3: 10,  // medium
  2: 8,   // low
  1: 6,
};

const IMPORTANCE_LABELS: Record<number, string> = {
  5: 'Critical',
  4: 'High',
  3: 'Medium',
  2: 'Low',
  1: 'Info',
};

const EVENT_TYPE_LABELS: Record<string, string> = {
  announcement: '公告',
  listing: '上币',
  delisting: '下币',
  campaign: '活动',
  fee_change: '费率调整',
  product_launch: '产品上线',
  vip_policy: 'VIP政策',
  wallet_issue: '钱包问题',
  compliance: '合规',
  partnership: '合作',
  macro: '宏观',
  social_hype: '社媒热点',
  product: '产品更新',
  news: '行业新闻',
};

export function PriceChart({ 
  data, 
  loading, 
  marketType, 
  selectedExchanges,
  exchanges,
  events,
  highlightedEventId,
  onRefresh,
  onEventClick,
}: PriceChartProps) {
  const chartRef = useRef<any>(null);

  const getOption = useCallback((): EChartsOption => {
    if (!data) return {};

    // 处理时间轴 - 使用 ts 字段
    const timestamps = data.btc.map(p => 
      dayjs(p.ts).format('MM-DD HH:mm')
    );

    // 创建时间到索引的映射（按小时）
    const timeToIndexMap = new Map<string, number>();
    data.btc.forEach((p, idx) => {
      const timeKey = dayjs(p.ts).format('MM-DD HH');
      timeToIndexMap.set(timeKey, idx);
    });

    // BTC 价格数据
    const btcData = data.btc.map(p => p.value);
    const maxPrice = Math.max(...btcData);

    // 按交易所分组交易量
    const volumeSeries: any[] = [];
    
    selectedExchanges.forEach(exchange => {
      const volData = data.volumes
        .filter(v => v.exchange === exchange)
        .map(v => v.value);
      
      const color = EXCHANGE_COLORS[exchange] || '#58a6ff';
      
      volumeSeries.push({
        name: exchange.toUpperCase(),
        type: 'line',
        yAxisIndex: 1,
        data: volData,
        smooth: true,
        lineStyle: { width: 2, color },
        itemStyle: { color },
        symbol: 'none',
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: color + '40' },
              { offset: 1, color: color + '05' }
            ]
          }
        }
      });
    });

    // 事件标注点 - 按交易所颜色 + 按重要程度大小
    const eventMarkers = events.map(event => {
      // 按小时匹配
      const eventHour = dayjs(event.ts).format('MM-DD HH');
      let xIndex = timeToIndexMap.get(eventHour);
      
      if (xIndex === undefined) {
        // 找最接近的小时
        let closestIdx = 0;
        let minDiff = Infinity;
        const eventTs = dayjs(event.ts).valueOf();
        data.btc.forEach((p, idx) => {
          const diff = Math.abs(eventTs - dayjs(p.ts).valueOf());
          if (diff < minDiff) {
            minDiff = diff;
            closestIdx = idx;
          }
        });
        xIndex = closestIdx;
      }
      
      // 使用交易所颜色
      const color = EXCHANGE_COLORS[event.exchange] || EVENT_TYPE_COLORS[event.event_type] || '#58a6ff';
      // 使用重要程度决定大小
      const importance = getImportanceFromId(event.id);
      const size = IMPORTANCE_SIZE[importance] || 10;
      // 高亮时放大
      const finalSize = event.id === highlightedEventId ? size * 1.5 : size;
      
      return {
        coord: [xIndex!, maxPrice * 1.08],
        value: event.id,
        eventData: event,
        symbolSize: finalSize,
        itemStyle: {
          color: color,
          borderColor: event.id === highlightedEventId ? '#fff' : 'transparent',
          borderWidth: event.id === highlightedEventId ? 2 : 0,
        },
      };
    });

    // 事件系列
    const eventSeries = {
      name: 'Events',
      type: 'scatter',
      symbolSize: (val: string) => {
        const importance = getImportanceFromId(val);
        const size = IMPORTANCE_SIZE[importance] || 10;
        return val === highlightedEventId ? size * 1.5 : size;
      },
      data: eventMarkers,
      tooltip: {
        backgroundColor: '#21262d',
        borderColor: '#30363d',
        textStyle: { color: '#e6edf3' },
        formatter: (params: any) => {
          const event = params.data?.eventData;
          if (!event) return '';
          const importance = getImportanceFromId(event.id);
          const color = EXCHANGE_COLORS[event.exchange] || '#58a6ff';
          return `<div style="font-size:13px;padding:4px;">
            <div style="font-weight:600;margin-bottom:6px;">${event.title}</div>
            <div style="display:flex;align-items:center;gap:6px;">
              <span style="width:10px;height:10px;border-radius:50%;background:${color};display:inline-block;"></span>
              <span>${event.exchange}</span>
            </div>
            <div style="margin-top:4px;color:#8b949e;">
              <span style="color:${EVENT_TYPE_COLORS[event.event_type] || '#58a6ff'}">${EVENT_TYPE_LABELS[event.event_type] || event.event_type}</span>
              <span style="margin-left:8px;">|</span>
              <span style="margin-left:8px;">${IMPORTANCE_LABELS[importance] || 'Medium'}</span>
            </div>
          </div>`;
        }
      },
      z: 10,
    };

    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: '#21262d',
        borderColor: '#30363d',
        textStyle: { color: '#e6edf3' },
        axisPointer: {
          type: 'cross',
          crossStyle: { color: '#8b949e' }
        }
      },
      legend: {
        data: ['BTC Price', ...selectedExchanges.map(e => e.toUpperCase())],
        textStyle: { color: '#8b949e' },
        top: 10
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        top: '15%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: timestamps,
        axisLine: { lineStyle: { color: '#30363d' } },
        axisLabel: { color: '#8b949e' },
        axisTick: { show: false }
      },
      yAxis: [
        {
          type: 'value',
          name: 'BTC Price (USD)',
          position: 'left',
          axisLine: { lineStyle: { color: '#F7931A' } },
          axisLabel: { 
            color: '#8b949e', 
            formatter: (value: number) => `$${value.toLocaleString()}` 
          },
          splitLine: { lineStyle: { color: '#21262d' } }
        },
        {
          type: 'value',
          name: 'Volume (USDT)',
          position: 'right',
          axisLine: { lineStyle: { color: '#58a6ff' } },
          axisLabel: { 
            color: '#8b949e', 
            formatter: (value: number) => `${(value/1000).toFixed(0)}K` 
          },
          splitLine: { show: false }
        }
      ],
      dataZoom: [
        { type: 'inside', start: 0, end: 100 },
        { 
          type: 'slider', 
          start: 0, 
          end: 100, 
          height: 20, 
          bottom: 40, 
          borderColor: '#30363d', 
          backgroundColor: '#161b22',
          fillerColor: 'rgba(88, 166, 255, 0.2)',
          handleStyle: { color: '#58a6ff' },
          textStyle: { color: '#8b949e' }
        }
      ],
      series: [
        {
          name: 'BTC Price',
          type: 'line',
          yAxisIndex: 0,
          data: btcData,
          smooth: true,
          lineStyle: { width: 3, color: '#F7931A' },
          itemStyle: { color: '#F7931A' },
          symbol: 'none'
        },
        ...volumeSeries,
        eventSeries
      ]
    };
  }, [data, selectedExchanges, events, highlightedEventId]);

  // 处理图表点击事件
  const handleChartClick = useCallback((params: any) => {
    if (params.seriesName === 'Events' || params.seriesIndex === selectedExchanges.length + 1) {
      const eventData = params.data?.eventData;
      if (eventData) {
        onEventClick(eventData);
      }
    }
  }, [onEventClick, selectedExchanges.length]);

  if (loading) {
    return (
      <div className="chart-container" style={{ height: 400, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <span style={{ color: '#8b949e' }}>加载中...</span>
      </div>
    );
  }

  return (
    <div className="chart-container">
      <ReactECharts 
        ref={chartRef}
        option={getOption()} 
        style={{ height: 400 }}
        opts={{ renderer: 'canvas' }}
        onEvents={{ 'click': handleChartClick }}
      />
    </div>
  );
}
