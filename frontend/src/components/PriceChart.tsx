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

const EXCHANGE_COLORS: Record<string, string> = {
  binance: '#F0B90B',
  okx: '#1E3A8A',
  bybit: '#F97316',
  bitget: '#38BDF8',
  hyperliquid: '#22C55E',
};

const BTC_COLOR = '#E6EDF3';

// 成交量格式化 B/M
function formatVol(val: number | null | undefined): string {
  if (val == null || val === 0) return '—';
  if (Math.abs(val) >= 1e9) return `${(val / 1e9).toFixed(1)}B`;
  if (Math.abs(val) >= 1e6) return `${(val / 1e6).toFixed(1)}M`;
  if (Math.abs(val) >= 1e3) return `${(val / 1e3).toFixed(0)}K`;
  return String(val);
}

// 成交额格式化（带 USD 单位）
function formatVolWithUnit(val: number | null | undefined, isEst: boolean = false): string {
  if (val == null || val === 0) return '—';
  const unit = isEst ? 'est. ' : '';
  if (Math.abs(val) >= 1e9) return `${unit}${formatVol(val)} USD`;
  if (Math.abs(val) >= 1e6) return `${unit}${formatVol(val)} USD`;
  return `${unit}${formatVol(val)} USD`;
}

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
    if (!data || !data.dates || data.dates.length === 0) return {};

    // xAxis 显示标签（MM-DD 格式）
    const timestamps = data.dates.map(d => dayjs(d).format('MM-DD'));

    // 日期到索引映射（d 格式为 YYYY-MM-DD，与 event_date 对齐）
    const dateToIndexMap = new Map<string, number>();
    data.dates.forEach((d, idx) => {
      dateToIndexMap.set(d, idx);
    });

    // 日期到 BTC 价格映射（用于事件点 y 坐标）
    const dateToBtcMap = new Map<string, number>();
    data.dates.forEach((d, idx) => {
      const price = data.price['BTC']?.[idx];
      if (price != null) dateToBtcMap.set(d, price);
    });

    // BTC 价格 series 数据
    const btcPrices = data.price['BTC'] || [];

    // 市场类型语义
    const isSpot = marketType === 'spot';
    const volData = isSpot ? data.spot_volumes : data.futures_volumes;
    const volUnit = isSpot ? 'BTC Spot Volume (24h)' : 'BTC Futures Volume (24h)';

    // 数据来源方法
    const methods = data.volume_methods || {};

    // 交易量 series
    // - name: "Binance BTC Spot" / "Binance BTC Futures"
    // - 带 method 信息用于 tooltip
    const volumeSeries: any[] = [];

    selectedExchanges.forEach(exchange => {
      const series = volData[exchange] || [];
      const color = EXCHANGE_COLORS[exchange] || '#58a6ff';
      const marketLabel = isSpot ? 'BTC Spot' : 'BTC Futures';
      const exchangeLabel = exchange.charAt(0).toUpperCase() + exchange.slice(1);
      const seriesName = `${exchangeLabel} ${marketLabel}`;
      const methodKey = `${exchange}_${marketType}`;
      const isEstimated = (methods[methodKey] || methods[exchange] || '') === 'estimated';

      volumeSeries.push({
        name: seriesName,
        type: 'line' as const,
        yAxisIndex: 1,
        data: series,
        smooth: 0.3,
        lineStyle: { width: 2, color },
        itemStyle: { color },
        symbol: 'none',
        connectNulls: false,
        areaStyle: {
          color: {
            type: 'linear' as const,
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: color + '30' },
              { offset: 1, color: color + '05' }
            ]
          }
        },
        // 携带 method 信息供 tooltip 使用
        _isEstimated: isEstimated,
        _exchange: exchange,
        _marketType: marketType,
      });
    });

    // ── 事件标注 ──────────────────────────────────────────────
    const eventMarkPointData = events
      .filter(e => selectedExchanges.includes(e.exchange))
      .map(event => {
        const eventDay = event.event_date || dayjs(event.ts).format('YYYY-MM-DD');
        const xIndex = dateToIndexMap.get(eventDay);
        if (xIndex === undefined) return null;

        const btcPrice = dateToBtcMap.get(eventDay) || 0;
        const yCoord = btcPrice * 1.03;
        const typeColor = EVENT_TYPE_COLORS[event.event_type] || '#58a6ff';

        return {
          coord: [xIndex, yCoord] as [number, number],
          eventData: event,
          symbol: 'circle',
          symbolSize: event.id === highlightedEventId ? 14 : 10,
          itemStyle: {
            color: typeColor,
            borderColor: event.id === highlightedEventId ? '#fff' : 'transparent',
            borderWidth: event.id === highlightedEventId ? 2 : 0,
          },
          tooltip: {
            trigger: 'item' as const,
            backgroundColor: '#21262d',
            borderColor: '#30363d',
            textStyle: { color: '#e6edf3' },
            formatter: (params: any) => {
              const ev = params.data.eventData;
              const exColor = EXCHANGE_COLORS[ev.exchange] || '#58a6ff';
              return `
                <div style="font-size:12px;padding:8px;min-width:180px;">
                  <div style="font-weight:600;margin-bottom:6px;color:#e6edf3;">${ev.title}</div>
                  <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px;">
                    <span style="width:8px;height:8px;border-radius:50%;background:${exColor};display:inline-block;"></span>
                    <span style="color:#e6edf3;">${ev.exchange.toUpperCase()}</span>
                    <span style="color:#8b949e;margin-left:8px;">${dayjs(ev.ts).format('MM-DD HH:mm')}</span>
                  </div>
                  <div style="color:#8b949e;font-size:11px;">${ev.event_type}</div>
                </div>
              `;
            }
          },
        };
      })
      .filter((item): item is NonNullable<typeof item> => item !== null);

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
        },
        formatter: (params: any[]) => {
          let result = '';
          params.forEach(p => {
            if (!p.value && p.value !== 0) return;
            let val = p.value;
            let label = p.seriesName || '';
            let unit = '';
            const isBtc = label === 'BTC';
            const isVolumeSeries = !isBtc && label.includes('BTC');

            if (isBtc) {
              unit = '$' + (typeof val === 'number' ? val.toLocaleString() : val);
            } else if (isVolumeSeries) {
              // 格式: "Binance BTC Spot: 1.1B USD" 或 "Binance BTC Spot: 1.1B est. USD"
              const isEst = p.data?._isEstimated || false;
              unit = formatVolWithUnit(val, isEst);
            } else {
              unit = formatVol(val);
            }
            const dot = p.seriesIndex === 0 ? '' : ' · ';
            result += `${dot}${label}: <b>${unit}</b><br/>`;
          });
          return result || '';
        }
      },
      legend: {
        data: ['BTC', ...selectedExchanges.map(e => {
          const m = isSpot ? 'BTC Spot' : 'BTC Futures';
          return `${e.charAt(0).toUpperCase() + e.slice(1)} ${m}`;
        })],
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
          scale: true,
          min: (value: number) => value.min * 0.98,
          max: (value: number) => value.max * 1.02,
          axisLine: { lineStyle: { color: BTC_COLOR } },
          axisLabel: {
            color: '#8b949e',
            formatter: (value: number) => {
              if (value >= 1e6) return `${(value/1e6).toFixed(1)}M`;
              if (value >= 1e3) return `${(value/1e3).toFixed(0)}K`;
              return `$${value.toLocaleString()}`;
            }
          },
          splitLine: { lineStyle: { color: '#21262d' } }
        },
        {
          type: 'value',
          name: volUnit,
          position: 'right',
          scale: true,
          axisLine: { lineStyle: { color: '#58a6ff' } },
          axisLabel: {
            color: '#8b949e',
            formatter: (value: number) => formatVol(value)
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
          data: btcPrices,
          smooth: 0.3,
          lineStyle: { width: 3, color: BTC_COLOR },
          itemStyle: { color: BTC_COLOR },
          symbol: 'none',
          markPoint: eventMarkPointData.length > 0 ? {
            symbol: 'circle',
            data: eventMarkPointData,
            tooltip: { trigger: 'item' },
          } : undefined,
        },
        ...volumeSeries,
      ]
    };
  }, [data, selectedExchanges, marketType, events, highlightedEventId]);

  const handleChartClick = useCallback((params: any) => {
    const eventData = params.data?.eventData;
    if (eventData) {
      onEventClick(eventData);
    }
  }, [onEventClick]);

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
