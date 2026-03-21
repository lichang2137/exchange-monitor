import { useCallback, useRef } from 'react';
import ReactECharts from 'echarts-for-react';
import type { EChartsOption } from 'echarts';
import type { ChartData, MarketType, Exchange, ChartEvent } from '../types';
import { EVENT_TYPE_COLORS, EVENT_TYPE_LABELS } from '../types';
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

// 交易所颜色（固定）
const EXCHANGE_COLORS: Record<string, string> = {
  binance: '#F0B90B',
  okx: '#1E3A8A',
  bybit: '#F97316',
  bitget: '#38BDF8',
  hyperliquid: '#22C55E',
};

// BTC 颜色（白色/浅灰）
const BTC_COLOR = '#E6EDF3';

// 事件类型标签
const EVENT_TYPE_LABELS_LOCAL: Record<string, string> = {
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

// 风险等级颜色
const RISK_LEVEL_COLORS: Record<string, string> = {
  low: '#3fb950',
  medium: '#d29922',
  high: '#f85149',
};

// 风险等级标签
const RISK_LEVEL_LABELS: Record<string, string> = {
  low: '低风险',
  medium: '中风险',
  high: '高风险',
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

    // 时间轴 - 使用 ts 字段
    const timestamps = data.btc.map(p => 
      dayjs(p.ts).format('MM-DD HH:mm')
    );

    // 创建时间到索引的映射
    const timeToIndexMap = new Map<string, number>();
    data.btc.forEach((p, idx) => {
      const timeKey = dayjs(p.ts).format('MM-DD HH');
      timeToIndexMap.set(timeKey, idx);
    });

    // BTC 价格数据
    const btcData = data.btc.map(p => p.value);
    const maxPrice = Math.max(...btcData);

    // 按交易所分组交易量（平滑处理）
    const volumeSeries: any[] = [];
    
    selectedExchanges.forEach(exchange => {
      // 按时间顺序构建交易量数组
      const volMap = new Map<string, number>();
      data.volumes
        .filter(v => v.exchange === exchange)
        .forEach(v => {
          const timeKey = dayjs(v.ts).format('MM-DD HH');
          if (v.value > 0) {  // 只记录有效值
            volMap.set(timeKey, v.value);
          }
        });
      
      // 与时间轴对齐，缺失值显示为空
      const volData = timestamps.map(t => {
        const val = volMap.get(t.split(' ')[0] + ' ' + t.split(' ')[1].substring(0, 2));
        return val !== undefined ? val : null;  // null 显示为空
      });
      
      const color = EXCHANGE_COLORS[exchange] || '#58a6ff';
      
      volumeSeries.push({
        name: exchange.toUpperCase(),
        type: 'line',
        yAxisIndex: 1,
        data: volData,
        smooth: 0.3,  // 平滑处理
        lineStyle: { width: 2, color },
        itemStyle: { color },
        symbol: 'none',
        connectNulls: false,  // 不连接空值
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: color + '30' },
              { offset: 1, color: color + '05' }
            ]
          }
        }
      });
    });

    // 事件标注点
    const eventMarkers = events.map(event => {
      const eventHour = dayjs(event.ts).format('MM-DD HH');
      let xIndex = timeToIndexMap.get(eventHour);
      
      if (xIndex === undefined) {
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
      
      const color = EXCHANGE_COLORS[event.exchange] || EVENT_TYPE_COLORS[event.event_type] || '#58a6ff';
      const baseSize = 10;
      const finalSize = event.id === highlightedEventId ? baseSize * 1.5 : baseSize;
      
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
        const size = 10;
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
          
          const exColor = EXCHANGE_COLORS[event.exchange] || '#58a6ff';
          const typeLabel = EVENT_TYPE_LABELS_LOCAL[event.event_type] || event.event_type;
          const typeColor = EVENT_TYPE_COLORS[event.event_type] || '#58a6ff';
          
          // 风险等级（从 title 或 event_type 推断）
          let riskLevel = 'medium';
          let riskColor = RISK_LEVEL_COLORS.medium;
          if (event.event_type === 'wallet_issue' || event.event_type === 'compliance') {
            riskLevel = 'high';
            riskColor = RISK_LEVEL_COLORS.high;
          } else if (event.event_type === 'listing' || event.event_type === 'campaign') {
            riskLevel = 'low';
            riskColor = RISK_LEVEL_COLORS.low;
          }
          
          return `
            <div style="font-size:13px;padding:8px;min-width:200px;">
              <div style="font-weight:600;margin-bottom:8px;color:#e6edf3;">${event.title}</div>
              <div style="display:flex;align-items:center;gap:6px;margin-bottom:6px;">
                <span style="width:10px;height:10px;border-radius:50%;background:${exColor};display:inline-block;"></span>
                <span style="color:#e6edf3;">${event.exchange.toUpperCase()}</span>
              </div>
              <div style="display:flex;gap:12px;margin-bottom:6px;">
                <span style="padding:2px 8px;border-radius:4px;font-size:11px;background:${typeColor}20;color:${typeColor};border:1px solid ${typeColor}40;">
                  ${typeLabel}
                </span>
                <span style="padding:2px 8px;border-radius:4px;font-size:11px;background:${riskColor}20;color:${riskColor};border:1px solid ${riskColor}40;">
                  ${RISK_LEVEL_LABELS[riskLevel]}
                </span>
              </div>
              <div style="color:#8b949e;font-size:11px;margin-top:6px;">
                ${dayjs(event.ts).format('MM-DD HH:mm')}
              </div>
            </div>
          `;
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
        data: ['BTC', ...selectedExchanges.map(e => e.toUpperCase())],
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
          axisLine: { lineStyle: { color: BTC_COLOR } },
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
            formatter: (value: number) => {
              if (value >= 1e9) return `${(value/1e9).toFixed(1)}B`;
              if (value >= 1e6) return `${(value/1e6).toFixed(0)}M`;
              if (value >= 1e3) return `${(value/1e3).toFixed(0)}K`;
              return `${value}`;
            } 
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
          name: 'BTC',
          type: 'line',
          yAxisIndex: 0,
          data: btcData,
          smooth: 0.3,
          lineStyle: { width: 3, color: BTC_COLOR },
          itemStyle: { color: BTC_COLOR },
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
