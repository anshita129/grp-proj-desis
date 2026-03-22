// PortfolioPage.jsx — SUPERUSER READY
import { useState, useEffect } from 'react'
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts'

const SECTOR_COLORS = {
  'Technology': '#3B82F6',
  'Finance': '#10B981',
  'Healthcare': '#F59E0B',
  'Energy': '#EF4444',
  'Unknown': '#6B7280'
}

export default function PortfolioPage() {
  const [data, setData] = useState({
    username: '',
    totalValue: 0,
    growth: 0,
    pnl: 0,
    investedamount: 0,
    performance: [],
    holdings: [],
    sectors: [],
    tradingBehavior: null,
    orderAnalytics: null,
    risk: null,
    diversification: null,
    behavioralFlags: [], // ← add this
    topGainers: [],
    topLosers: [],
    stockAllocation: []
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = () => {
      fetch('/portfolio/my-portfolio/', {
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
      })
      .then(r => {
        console.log('Status:', r.status)
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then(apiData => {
        console.log('Got data:', apiData)
        setData({
          username: 'Anshita',
          totalValue: apiData.summary.total_value,
          growth: apiData.summary.return_percent,
          pnl: apiData.summary.profit_loss,
          investedamount: apiData.summary.invested_amount,
          performance: (apiData.portfolio_value_history || []).map(p => ({
            date: p.date,
            value: p.total_value
          })),
          holdings: (apiData.holdings || []).map(h => ({
            symbol: h.symbol,
            qty: h.quantity,
            cost: h.avg_buy_price,
            current_value: h.current_value,
            pnl: h.profit_loss,
            avg30: h.avg_30_day,
            aboveTrend: h.above_trend
          })),
          sectors: (apiData.sector_allocation || []).map(s => ({
            name: s.sector,
            value: s.value,
            color: SECTOR_COLORS[s.sector] || '#6B7280'
          })),
          stockAllocation: apiData.stock_allocation || [],
          tradingBehavior: apiData.trading_behavior || null,
          orderAnalytics: apiData.order_analytics || null,
          risk: apiData.risk || null,
          diversification: apiData.diversification || null,
          behavioralFlags: apiData.behavioral_flags?.flags || [],
          topGainers: apiData.top_gainers || [],
          topLosers: apiData.top_losers || []
        })
      })
      .catch(err => console.error('Fetch failed:', err))
      .finally(() => setLoading(false))
    }

    fetchData() // ← run immediately on load
    const interval = setInterval(fetchData, 30000) // ← then every 30 seconds
    return () => clearInterval(interval) // ← cleanup on unmount
  }, [])
      


  // Rest of JSX unchanged — just uses data.totalValue, data.growth, etc.


  if (loading) return <div className="flex items-center justify-center min-h-screen text-white">Loading...</div>

  return (
    
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900 text-white p-6 font-sans">
      <div className="max-w-7xl mx-auto">
        {/* ─── ALERT BANNER ─── */}
        {data.risk?.level === 'HIGH' && (
          <div className="mb-6 p-4 bg-red-500/20 border border-red-500/40 rounded-2xl flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <span className="text-2xl">🚨</span>
              <div>
                <div className="font-bold text-red-400">High Risk Alert!</div>
                <div className="text-sm text-gray-300">
                  Your portfolio risk score is {data.risk.score}/100 — immediate attention needed
                </div>
              </div>
            </div>
            <div className="text-xs text-gray-400">Today</div>
          </div>
        )}

        {/* Diversification warning */}
        {data.diversification?.grade === 'D' && (
          <div className="mb-6 p-4 bg-yellow-500/20 border border-yellow-500/40 rounded-2xl flex items-center space-x-3">
            <span className="text-2xl">⚠️</span>
            <div>
              <div className="font-bold text-yellow-400">Poor Diversification!</div>
              <div className="text-sm text-gray-300">{data.diversification.message}</div>
            </div>
          </div>
        )}

        {/* Behavioral warning */}
        {data.behavioralFlags?.length > 0 && (
          <div className="mb-6 p-4 bg-orange-500/20 border border-orange-500/40 rounded-2xl flex items-center space-x-3">
            <span className="text-2xl">🧠</span>
            <div>
              <div className="font-bold text-orange-400">Behavioral Flags Detected!</div>
              <div className="text-sm text-gray-300">
                {data.behavioralFlags.length} trading pattern issue(s) found — check details below
              </div>
            </div>
          </div>
        )}
        
        {/* TOP NAV — DYNAMIC USERNAME */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center space-x-4">
            <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center font-bold">D</div>
            <div>
              <div className="text-lg font-bold">Desis Portfolio</div>
              <div className="text-sm text-gray-400 flex items-center space-x-2">
                <span className="bg-blue-600 text-xs px-2 py-1 rounded-full">Portfolio</span>
              </div>
            </div>
          </div>
          <div className="flex items-center space-x-4 text-sm">
              <button 
                onClick={() => window.location.reload()}
                className="text-xs bg-blue-600 px-3 py-1 rounded-full hover:bg-blue-700"
              >
                🔄 Refresh
              </button>
            <span className="font-medium">{data.username}</span>  {/* ← DYNAMIC! */}
            <div className="w-8 h-8 bg-gray-700 rounded-full flex items-center justify-center">A</div>
          </div>
        </div>

        {/* STATS — REAL DATA */}
        <div className="grid grid-cols-4 gap-6 mb-12">
          <div>
            <div className="text-3xl font-black">₹{data.totalValue?.toLocaleString()}</div>
            <div className="text-sm text-gray-400">Total Value</div>
          </div>
          <div>
            <div className="text-xl font-bold text-green-400">+{data.growth}%</div>
            <div className="text-sm text-gray-400">Growth</div>
          </div>
          <div>
            <div className="text-xl font-bold">{data.investedamount}</div>
            <div className="text-sm text-gray-400">Invested Amount</div>
          </div>
          <div>
            <div className="text-xl font-bold text-green-400">+₹{data.pnl?.toLocaleString()}</div>
            <div className="text-sm text-gray-400">P&L</div>
          </div>
        </div>

        {/* CHARTS — YOUR REAL DATA */}
        <div className="grid grid-cols-3 gap-8 mb-12">
          <div className="col-span-2 bg-gray-900/50 backdrop-blur-xl rounded-2xl p-8 border border-gray-800">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold">30 Day Performance</h3>
              <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={data.performance}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" vertical={false} />
                <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{fill: 'gray'}} />
                <YAxis axisLine={false} tickLine={false} tick={{fill: 'gray'}} />
                <Tooltip />
                <Line type="monotone" dataKey="value" stroke="#3B82F6" strokeWidth={3} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-gray-900/50 backdrop-blur-xl rounded-2xl p-8 border border-gray-800">
            <h3 className="text-xl font-bold mb-6">Sector Allocation</h3>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie data={data.sectors} dataKey="value" cx="50%" cy="50%" outerRadius={70} innerRadius={40}>
                  {data.sectors.map((entry, index) => <Cell key={`cell-${index}`} fill={entry.color} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>

            {/* ← LEGEND MUST BE INSIDE THIS DIV, not outside */}
            <div className="mt-4 space-y-2">
              {data.sectors.map((sector, i) => (
                <div key={i} className="flex items-center justify-between text-sm">
                  <div className="flex items-center space-x-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: sector.color }}></div>
                    <span className="text-gray-300">{sector.name}</span>
                  </div>
                  <span className="text-gray-400">
                    {((sector.value / data.sectors.reduce((a, b) => a + b.value, 0)) * 100).toFixed(1)}%
                  </span>
                </div>
              ))}
            </div>

          </div>  {/* ← closing tag for the card */}

        </div>

        {/* HOLDINGS TABLE — YOUR REAL DATA */}
        <div className="bg-gray-900/50 backdrop-blur-xl rounded-2xl border border-gray-800 overflow-hidden">
          <div className="p-8 border-b border-gray-800">
            <h3 className="text-2xl font-bold flex items-center">
              All Holdings
              <span className="ml-4 text-sm text-gray-400">({data.holdings?.length || 0})</span>
            </h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-900/50">
                <tr>
                  <th className="p-6 text-left text-sm font-bold text-gray-300">Symbol</th>
                  <th className="p-6 text-right text-sm font-bold text-gray-300">Qty</th>
                  <th className="p-6 text-right text-sm font-bold text-gray-300">Avg Cost</th>
                  <th className="p-6 text-right text-sm font-bold text-gray-300">Market</th>
                  <th className="p-6 text-right text-sm font-bold text-gray-300">P&L %</th>
                  <th className="p-6 text-right text-sm font-bold text-gray-300">Trend</th>
                </tr>
              </thead>
              <tbody>
                {data.holdings.map((holding, i) => (
                  <tr key={i} className="border-t border-gray-800 hover:bg-gray-800/50">
                    <td className="p-6 font-bold">{holding.symbol}</td>
                    <td className="p-6 text-right">{holding.qty}</td>
                    <td className="p-6 text-right">₹{holding.cost?.toLocaleString()}</td>
                    <td className="p-6 text-right">₹{holding.current_value?.toLocaleString()}</td>
                    <td className={`p-6 text-right font-bold ${holding.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {holding.pnl >= 0 ? '+' : ''}₹{holding.pnl?.toLocaleString()}
                    </td>
                    <td className="p-6 text-right">
                      {holding.aboveTrend === null ? (
                        <span className="text-gray-500 text-sm">No data</span>
                      ) : holding.aboveTrend ? (
                        <div className="text-right">
                          <span className="text-green-400 font-bold text-sm">📈 Above</span>
                          <div className="text-xs text-gray-400">30d avg ₹{holding.avg30?.toLocaleString()}</div>
                        </div>
                      ) : (
                        <div className="text-right">
                          <span className="text-red-400 font-bold text-sm">📉 Below</span>
                          <div className="text-xs text-gray-400">30d avg ₹{holding.avg30?.toLocaleString()}</div>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* STOCK ALLOCATION */}
        <div className="bg-gray-900/50 backdrop-blur-xl rounded-2xl p-8 border border-gray-800 mt-8">
          <h3 className="text-xl font-bold mb-6">Stock Allocation</h3>
          <div className="space-y-4">
            {data.stockAllocation.map((stock, i) => (
              <div key={i}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="font-bold">{stock.symbol}</span>
                  <span className="text-gray-400">{stock.percent?.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-800 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full"
                    style={{ width: `${stock.percent}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* TOP GAINERS & LOSERS */}
        <div className="grid grid-cols-2 gap-6 mt-8">

          {/* GAINERS */}
          <div className="bg-gray-900/50 backdrop-blur-xl rounded-2xl p-8 border border-gray-800">
            <h3 className="text-xl font-bold mb-6 flex items-center">
              <span className="text-green-400 mr-2">▲</span> Top Gainers
            </h3>
            <div className="space-y-4">
              {data.topGainers.map((stock, i) => (
                <div key={i} className="flex items-center justify-between p-4 bg-green-500/10 border border-green-500/20 rounded-xl">
                  <div>
                    <div className="font-bold">{stock.symbol}</div>
                    <div className="text-xs text-gray-400">Qty: {stock.quantity}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-green-400 font-bold">+{stock.return_percent?.toFixed(2)}%</div>
                    <div className="text-xs text-gray-400">+₹{stock.profit_loss?.toLocaleString()}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* LOSERS */}
          <div className="bg-gray-900/50 backdrop-blur-xl rounded-2xl p-8 border border-gray-800">
            <h3 className="text-xl font-bold mb-6 flex items-center">
              <span className="text-red-400 mr-2">▼</span> Top Losers
            </h3>
            <div className="space-y-4">
              {data.topLosers.map((stock, i) => (
                <div key={i} className="flex items-center justify-between p-4 bg-red-500/10 border border-red-500/20 rounded-xl">
                  <div>
                    <div className="font-bold">{stock.symbol}</div>
                    <div className="text-xs text-gray-400">Qty: {stock.quantity}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-red-400 font-bold">{stock.return_percent?.toFixed(2)}%</div>
                    <div className="text-xs text-gray-400">-₹{Math.abs(stock.profit_loss)?.toLocaleString()}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>


              {/* ─── RISK & INTELLIGENCE SECTION ─── */}

        {/* ROW 1 — Risk Score + Diversification side by side */}
        <div className="grid grid-cols-2 gap-6 mt-8">

          {/* RISK SCORE */}
          {data.risk && (
            <div className="bg-gray-900/50 backdrop-blur-xl rounded-2xl p-8 border border-gray-800">
              <h3 className="text-xl font-bold mb-6">Risk Score</h3>
              
              {/* Score circle */}
              <div className="flex items-center space-x-6 mb-6">
                <div className={`w-24 h-24 rounded-full flex flex-col items-center justify-center border-4 ${
                  data.risk.level === 'HIGH' ? 'border-red-500 text-red-400' :
                  data.risk.level === 'MEDIUM' ? 'border-yellow-500 text-yellow-400' :
                  'border-green-500 text-green-400'
                }`}>
                  <div className="text-3xl font-black">{data.risk.score}</div>
                  <div className="text-xs">/100</div>
                </div>
                <div>
                  <div className={`text-2xl font-bold ${
                    data.risk.level === 'HIGH' ? 'text-red-400' :
                    data.risk.level === 'MEDIUM' ? 'text-yellow-400' :
                    'text-green-400'
                  }`}>{data.risk.level} RISK</div>
                  <div className="text-sm text-gray-400 mt-1">Based on your portfolio</div>
                </div>
              </div>

              {/* Risk Flags */}
              {data.risk.flags?.length > 0 && (
                <div className="space-y-3">
                  {data.risk.flags.map((flag, i) => (
                    <div key={i} className={`flex items-start space-x-3 p-3 rounded-xl ${
                      flag.severity === 'HIGH' ? 'bg-red-500/10 border border-red-500/20' :
                      'bg-yellow-500/10 border border-yellow-500/20'
                    }`}>
                      <span className="text-lg">{flag.severity === 'HIGH' ? '🔴' : '🟡'}</span>
                      <div>
                        <div className="text-xs font-bold text-gray-400">{flag.type.replace('_', ' ')}</div>
                        <div className="text-sm text-gray-200">{flag.message}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {data.risk.flags?.length === 0 && (
                <div className="flex items-center space-x-2 text-green-400">
                  <span>✅</span>
                  <span className="text-sm">No risk flags detected</span>
                </div>
              )}
            </div>
          )}

          {/* DIVERSIFICATION INDEX */}
          {data.diversification && (
            <div className="bg-gray-900/50 backdrop-blur-xl rounded-2xl p-8 border border-gray-800">
              <h3 className="text-xl font-bold mb-6">Diversification Index</h3>

              {/* Grade circle */}
              <div className="flex items-center space-x-6 mb-6">
                <div className={`w-24 h-24 rounded-full flex flex-col items-center justify-center border-4 ${
                  data.diversification.grade === 'A' ? 'border-green-500 text-green-400' :
                  data.diversification.grade === 'B' ? 'border-blue-500 text-blue-400' :
                  data.diversification.grade === 'C' ? 'border-yellow-500 text-yellow-400' :
                  'border-red-500 text-red-400'
                }`}>
                  <div className="text-3xl font-black">{data.diversification.grade}</div>
                  <div className="text-xs">{data.diversification.score}/100</div>
                </div>
                <div>
                  <div className="text-lg font-bold text-gray-200">{data.diversification.message}</div>
                  <div className="text-sm text-gray-400 mt-1">
                    {data.diversification.num_stocks} stocks · {data.diversification.num_sectors} sectors
                  </div>
                </div>
              </div>

              {/* Stats */}
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Dominant Sector</span>
                  <span className="font-bold">{data.diversification.dominant_sector}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Sector Exposure</span>
                  <span className={`font-bold ${
                    data.diversification.dominant_sector_percent > 60 ? 'text-red-400' :
                    data.diversification.dominant_sector_percent > 40 ? 'text-yellow-400' :
                    'text-green-400'
                  }`}>{data.diversification.dominant_sector_percent}%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Number of Stocks</span>
                  <span className="font-bold">{data.diversification.num_stocks}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Number of Sectors</span>
                  <span className="font-bold">{data.diversification.num_sectors}</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* ROW 2 — Behavioral Flags */}
        {data.behavioralFlags?.length > 0 && (
          <div className="mt-6 bg-gray-900/50 backdrop-blur-xl rounded-2xl p-8 border border-gray-800">
            <h3 className="text-xl font-bold mb-6">
              🧠 Behavioral Flags
              <span className="ml-3 text-sm text-gray-400">({data.behavioralFlags.length} detected)</span>
            </h3>
            <div className="grid grid-cols-2 gap-4">
              {data.behavioralFlags.map((flag, i) => (
                <div key={i} className={`p-4 rounded-xl border ${
                  flag.severity === 'HIGH' 
                    ? 'bg-red-500/10 border-red-500/20' 
                    : 'bg-yellow-500/10 border-yellow-500/20'
                }`}>
                  <div className="flex items-center space-x-2 mb-1">
                    <span>{flag.severity === 'HIGH' ? '🔴' : '🟡'}</span>
                    <span className="text-xs font-bold text-gray-400">
                      {flag.type.replace(/_/g, ' ')}
                    </span>
                    {flag.date && (
                      <span className="text-xs text-gray-500 ml-auto">{flag.date}</span>
                    )}
                  </div>
                  <div className="text-sm text-gray-200">{flag.message}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* No flags message */}
        {data.behavioralFlags?.length === 0 && (
          <div className="mt-6 bg-gray-900/50 rounded-2xl p-6 border border-gray-800 flex items-center space-x-3">
            <span className="text-2xl">🧠</span>
            <div>
              <div className="font-bold">Behavioral Flags</div>
              <div className="text-sm text-green-400">No behavioral anomalies detected — clean trading pattern! ✅</div>
            </div>
          </div>
        )}

        {/* TRADING BEHAVIOR */}
        {data.tradingBehavior && !data.tradingBehavior.error && (
          <div className="grid grid-cols-4 gap-6 mt-8">
            
            <div className="bg-gray-900/50 rounded-2xl p-6 border border-gray-800">
              <div className="text-sm text-gray-400 mb-1">Total Trades</div>
              <div className="text-2xl font-bold">{data.tradingBehavior.trading_frequency.total_trades}</div>
              <div className="text-xs text-gray-500 mt-1">Last 90 days</div>
            </div>

            <div className="bg-gray-900/50 rounded-2xl p-6 border border-gray-800">
              <div className="text-sm text-gray-400 mb-1">Buy / Sell Ratio</div>
              <div className="text-2xl font-bold">{data.tradingBehavior.buy_sell_ratio}</div>
              <div className="text-xs text-gray-500 mt-1">Trades split</div>
            </div>

            <div className="bg-gray-900/50 rounded-2xl p-6 border border-gray-800">
              <div className="text-sm text-gray-400 mb-1">Avg Daily Spend</div>
              <div className="text-2xl font-bold">₹{data.tradingBehavior.spending_patterns.avg_daily_spend?.toLocaleString()}</div>
              <div className="text-xs text-gray-500 mt-1">On buy days</div>
            </div>

            <div className="bg-gray-900/50 rounded-2xl p-6 border border-gray-800">
              <div className="text-sm text-gray-400 mb-1">Most Active Stock</div>
              <div className="text-2xl font-bold">{data.tradingBehavior.trading_frequency.most_active_stock?.stock_symbol || '—'}</div>
              <div className="text-xs text-gray-500 mt-1">{data.tradingBehavior.trading_frequency.most_active_stock?.trades} trades</div>
            </div>

          </div>
        )}


        {/* ORDER ANALYTICS */}
        {data.orderAnalytics && (
          <div className="mt-8">
            
            {/* 3 stat cards */}
            <div className="grid grid-cols-3 gap-6 mb-6">
              <div className="bg-gray-900/50 rounded-2xl p-6 border border-gray-800">
                <div className="text-sm text-gray-400 mb-1">Total Orders</div>
                <div className="text-2xl font-bold">{data.orderAnalytics.total_orders}</div>
              </div>

              <div className="bg-gray-900/50 rounded-2xl p-6 border border-gray-800">
                <div className="text-sm text-gray-400 mb-1">Success Rate</div>
                <div className="text-2xl font-bold text-green-400">{data.orderAnalytics.success_rate}%</div>
              </div>

              <div className="bg-gray-900/50 rounded-2xl p-6 border border-gray-800">
                <div className="text-sm text-gray-400 mb-1">Cancellation Rate</div>
                <div className="text-2xl font-bold text-red-400">{data.orderAnalytics.cancellation_rate}%</div>
              </div>
            </div>

            {/* Pending orders table — only show if there are pending orders */}
            {data.orderAnalytics.pending_limit_orders?.length > 0 && (
              <div className="bg-gray-900/50 rounded-2xl border border-gray-800 overflow-hidden">
                <div className="p-6 border-b border-gray-800">
                  <h3 className="text-lg font-bold">
                    Pending Orders
                    <span className="ml-3 text-sm text-gray-400">({data.orderAnalytics.pending_limit_orders.length})</span>
                  </h3>
                </div>
                <table className="w-full">
                  <thead className="bg-gray-900/50">
                    <tr>
                      <th className="p-4 text-left text-sm font-bold text-gray-300">Symbol</th>
                      <th className="p-4 text-right text-sm font-bold text-gray-300">Type</th>
                      <th className="p-4 text-right text-sm font-bold text-gray-300">Qty</th>
                      <th className="p-4 text-right text-sm font-bold text-gray-300">Price</th>
                      <th className="p-4 text-right text-sm font-bold text-gray-300">Days Pending</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.orderAnalytics.pending_limit_orders.map((order, i) => (
                      <tr key={i} className="border-t border-gray-800 hover:bg-gray-800/50">
                        <td className="p-4 font-bold">{order.symbol}</td>
                        <td className={`p-4 text-right font-bold ${order.type === 'BUY' ? 'text-green-400' : 'text-red-400'}`}>
                          {order.type}
                        </td>
                        <td className="p-4 text-right">{order.quantity}</td>
                        <td className="p-4 text-right">₹{order.price?.toLocaleString()}</td>
                        <td className="p-4 text-right text-yellow-400">{order.days_pending}d</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

          </div>
        )}
      
      
      </div>
    </div>
  )
}
