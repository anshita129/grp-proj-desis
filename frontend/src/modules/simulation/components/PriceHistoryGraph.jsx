import React, { useMemo } from 'react';
import { LineChart, Line, ResponsiveContainer, YAxis } from 'recharts';

const PriceHistoryGraph = ({ marketData, currentTick, symbol, isDown }) => {
  const chartData = useMemo(() => {
    // We only want data up to the current tick to avoid showing the "future"
    const relevantData = marketData.slice(0, currentTick + 1);
    return relevantData.map((tick) => ({
      price: tick.prices[symbol] || 0,
    }));
  }, [marketData, currentTick, symbol]);

  if (chartData.length === 0) {
    return null;
  }

  // Determine line color based on isDown (red if down, green if up)
  const strokeColor = isDown ? '#f87171' : '#34d399'; // Tailwind red-400 and emerald-400

  return (
    <div className="w-full h-full min-h-[100px] flex items-center justify-center pointer-events-none">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
          <YAxis domain={['auto', 'auto']} hide />
          <Line
            type="monotone"
            dataKey="price"
            stroke={strokeColor}
            strokeWidth={3}
            dot={false}
            isAnimationActive={false} // Disable animation so it looks instantaneous on hover/tick
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default PriceHistoryGraph;
