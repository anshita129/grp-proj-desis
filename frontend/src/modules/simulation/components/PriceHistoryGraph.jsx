import React, { useMemo } from 'react';
import { ComposedChart, Bar, ResponsiveContainer, YAxis, XAxis, CartesianGrid, Tooltip } from 'recharts';

const CandlestickRender = (props) => {
  const { x, y, width, height, payload } = props;
  const { open, high, low, close } = payload;

  if (high === undefined || low === undefined || open === undefined || close === undefined) {
    return null;
  }

  const isGrowing = close >= open;
  const color = isGrowing ? '#10b981' : '#f43f5e'; // emerald-500 : rose-500

  const valueDelta = high - low;
  const scale = valueDelta > 0 ? height / valueDelta : 0;

  const yOpen = y + (high - open) * scale;
  const yClose = y + (high - close) * scale;

  const bodyTop = Math.min(yOpen, yClose);
  const bodyBottom = Math.max(yOpen, yClose);
  const bodyHeight = Math.max(bodyBottom - bodyTop, 1);

  const centerX = x + width / 2;

  return (
    <g>
      <line x1={centerX} y1={y} x2={centerX} y2={y + height} stroke={color} strokeWidth={1} />
      <rect x={x} y={bodyTop} width={width} height={bodyHeight} fill={color} stroke={color} strokeWidth={1} />
    </g>
  );
};

const PriceHistoryGraph = ({ marketData, currentTick, symbol }) => {
  const chartData = useMemo(() => {
    const startIdx = Math.max(0, currentTick - 99);
    const relevantData = marketData.slice(startIdx, currentTick + 1);
    return relevantData.map((tick) => {
      const ohlc = tick.ohlc?.[symbol] || { open: 0, high: 0, low: 0, close: 0 };
      const timeStr = typeof tick.timestamp === 'string'
        ? tick.timestamp.split(' ')[1] || tick.timestamp
        : new Date(tick.timestamp).toLocaleTimeString([], { timeStyle: 'short' });

      return {
        timestamp: timeStr,
        ...ohlc,
        range: [ohlc.low, ohlc.high]
      };
    });
  }, [marketData, currentTick, symbol]);

  if (chartData.length === 0) return null;

  return (
    <div className="w-full h-[300px] bg-slate-900/80 rounded-xl p-4 border border-slate-700 shadow-inner flex flex-col">
      <h3 className="text-slate-300 font-semibold mb-2">{symbol} Chart Data</h3>
      <div className="flex-1 w-full relative">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 10, right: 30, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
            <XAxis dataKey="timestamp" stroke="#94a3b8" tick={{ fontSize: 12 }} tickMargin={10} minTickGap={30} />
            <YAxis domain={['auto', 'auto']} stroke="#94a3b8" tick={{ fontSize: 12 }} width={80} />
            <Tooltip
              contentStyle={{ backgroundColor: '#1e293b', borderColor: '#475569', color: '#f8fafc' }}
              itemStyle={{ color: '#e2e8f0' }}
              formatter={(value, name, props) => {
                if (name === 'range') return [`O: ${props.payload.open.toFixed(2)} | C: ${props.payload.close.toFixed(2)}`, 'Market Value'];
                return [value, name];
              }}
            />
            <Bar
              dataKey="range"
              shape={<CandlestickRender />}
              isAnimationActive={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default PriceHistoryGraph;
