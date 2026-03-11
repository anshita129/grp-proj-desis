import React, { useState, useEffect, useRef } from 'react';

const MARKET_DATA_URL = "http://127.0.0.1:8003/api/simulation/market-data/";
const SCENARIOS_URL = "http://127.0.0.1:8003/api/simulation/scenarios/";

function SimulationPage() {
  const [scenarios, setScenarios] = useState([]);
  const [selectedScenario, setSelectedScenario] = useState("Loading scenarios...");
  const [simStatus, setSimStatus] = useState("Offline");
  const [isRunning, setIsRunning] = useState(false);

  // Core state
  const [marketData, setMarketData] = useState([]);
  const [uniqueSymbols, setUniqueSymbols] = useState([]);
  const [currentTick, setCurrentTick] = useState(0);

  // Display values
  const [currentDate, setCurrentDate] = useState("YYYY-MM-DD HH:MM");
  const [nav, setNav] = useState(10000.00);
  const [cash, setCash] = useState(10000.00);
  const [portfolioPositions, setPortfolioPositions] = useState({});
  const [currentPrices, setCurrentPrices] = useState({});
  const [prevPrices, setPrevPrices] = useState({});
  const [tradeLog, setTradeLog] = useState([]);
  const [logs, setLogs] = useState(["System initialized. Waiting for data feed..."]);

  // Individual inputs per symbol
  const [quantities, setQuantities] = useState({});

  const logsEndRef = useRef(null);
  const simIntervalRef = useRef(null);

  // Initial load
  useEffect(() => {
    fetchScenarios();
  }, []);

  // Auto-scroll logs
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  const addLog = (msg) => {
    const time = new Date().toLocaleTimeString();
    setLogs(prev => [...prev, `[${time}] ${msg}`]);
  };

  const fetchScenarios = async () => {
    try {
      const res = await fetch(SCENARIOS_URL);
      const data = await res.json();
      if (data.scenarios && data.scenarios.length > 0) {
        setScenarios(data.scenarios);
        const defaultScen = data.scenarios.includes("market_simulation_data.csv")
          ? "market_simulation_data.csv"
          : data.scenarios[0];
        setSelectedScenario(defaultScen);
      } else {
        setScenarios(["No scenarios found"]);
      }
    } catch (e) {
      console.error("Failed to fetch scenarios", e);
      addLog("Error loading scenarios from backend.");
    }
  };

  // When scenario changes, load it
  useEffect(() => {
    if (selectedScenario !== "Loading scenarios..." && selectedScenario !== "No scenarios found") {
      resetAndLoadScenario(selectedScenario);
    }
  }, [selectedScenario]);

  const resetAndLoadScenario = async (scenarioName) => {
    if (isRunning) stopSim();

    setSimStatus("Loading");

    // Reset full state for new scenario
    setMarketData([]);
    setUniqueSymbols([]);
    setCurrentTick(0);
    setCurrentDate("YYYY-MM-DD HH:MM");
    setNav(10000.00);
    setCash(10000.00);
    setPortfolioPositions({});
    setCurrentPrices({});
    setPrevPrices({});
    setTradeLog([]);

    await fetchMarketData(scenarioName);
  };

  const fetchMarketData = async (scenarioName) => {
    try {
      addLog(`Fetching data feed for scenario: ${scenarioName}...`);
      const res = await fetch(`${MARKET_DATA_URL}?scenario=${encodeURIComponent(scenarioName)}`);
      const data = await res.json();

      if (data.error) {
        addLog(`ERROR: ${data.error}`);
        return false;
      }

      let groupedByTime = {};
      let times = [];
      let symbolSet = new Set();

      data.data.forEach(row => {
        let ts = row.timestamp || row.Date;
        if (!groupedByTime[ts]) {
          groupedByTime[ts] = {};
          times.push(ts);
        }
        let sym = (row.symbol || row.Symbol).toUpperCase();
        symbolSet.add(sym);
        groupedByTime[ts][sym] = parseFloat(row.close || row.Close);
      });

      const parsedMarketData = times.map(ts => ({ timestamp: ts, prices: groupedByTime[ts] }));
      const parsedSymbols = Array.from(symbolSet).sort();

      setMarketData(parsedMarketData);
      setUniqueSymbols(parsedSymbols);

      // Initialize positions & prices
      const initPos = {};
      const initPrices = {};
      const initQtys = {};
      parsedSymbols.forEach(sym => {
        initPos[sym] = 0;
        initPrices[sym] = 0;
        initQtys[sym] = 10;
      });
      setPortfolioPositions(initPos);
      setCurrentPrices(initPrices);
      setPrevPrices(initPrices);
      setQuantities(initQtys);

      addLog(`Received ${parsedMarketData.length} unique market time ticks for ${parsedSymbols.length} symbols.`);
      setSimStatus("Ready");
      return true;
    } catch (e) {
      addLog(`Network Error: Make sure the Django API is running on port 8003.`);
      console.error(e);
      return false;
    }
  };

  // The core tick logic
  const engineTick = () => {
    setCurrentTick(prevTick => {
      // Need to use refs or functional state update to see latest marketData length
      return prevTick + 1;
    });
  };

  // Update UI whenever currentTick changes
  useEffect(() => {
    if (marketData.length === 0 || currentTick >= marketData.length) {
      if (currentTick > 0 && isRunning) {
        stopSim();
        addLog("End of market data reached.");
        setSimStatus("Completed");
      }
      return;
    }

    const tick = marketData[currentTick];
    setCurrentDate(tick.timestamp || `Tick ${currentTick}`);

    setCurrentPrices(prevCurrent => {
      const newPrev = { ...prevCurrent };
      const newCurrent = { ...prevCurrent };

      uniqueSymbols.forEach(sym => {
        if (tick.prices[sym] !== undefined) {
          newCurrent[sym] = tick.prices[sym];
        }
      });
      setPrevPrices(newPrev);
      return newCurrent;
    });
  }, [currentTick, marketData, isRunning]);

  // Update NAV right after prices change
  useEffect(() => {
    let positionsValue = 0;
    uniqueSymbols.forEach(sym => {
      positionsValue += (portfolioPositions[sym] || 0) * (currentPrices[sym] || 0);
    });
    setNav(cash + positionsValue);
  }, [currentPrices, portfolioPositions, cash, uniqueSymbols]);

  const startSim = async () => {
    if (marketData.length === 0) {
      const success = await fetchMarketData(selectedScenario);
      if (!success) return;
    }

    if (currentTick >= marketData.length - 1) {
      addLog("Simulation already at the end of data. Refresh or switch scenarios to restart.");
      return;
    }

    addLog("Starting High-Frequency Engine...");
    setIsRunning(true);
    setSimStatus("LIVE STREAM");

    simIntervalRef.current = setInterval(engineTick, 100);
  };

  const stopSim = () => {
    clearInterval(simIntervalRef.current);
    setIsRunning(false);
    setSimStatus(currentTick >= (marketData.length - 1) ? "Completed" : "Paused");
    addLog("Simulation Paused.");
  };

  const handleTrade = (side, symbol) => {
    const qty = parseInt(quantities[symbol] || 0, 10);

    if (isNaN(qty) || qty <= 0) {
      addLog(`Invalid quantity: ${quantities[symbol]}`);
      return;
    }

    const price = currentPrices[symbol];
    const cost = qty * price;

    if (side === 'Buy') {
      if (cash < cost) {
        addLog(`[DECLINED] Insufficient cash for ${qty}x ${symbol} @ $${price.toFixed(2)}. Need $${cost.toFixed(2)}`);
        return;
      }
      setCash(prev => prev - cost);
      setPortfolioPositions(prev => ({ ...prev, [symbol]: prev[symbol] + qty }));
      setTradeLog(prev => [...prev, { time: marketData[currentTick].timestamp, side: 'Buy', symbol, qty, price, cost }]);
      addLog(`[FILLED] BUY ${qty} ${symbol} @ $${price.toFixed(2)} (-$${cost.toFixed(2)})`);
    } else if (side === 'Sell') {
      if (portfolioPositions[symbol] < qty) {
        addLog(`[DECLINED] Insufficient shares. Own ${portfolioPositions[symbol]}x ${symbol}, tried to sell ${qty}.`);
        return;
      }
      setCash(prev => prev + cost);
      setPortfolioPositions(prev => ({ ...prev, [symbol]: prev[symbol] - qty }));
      setTradeLog(prev => [...prev, { time: marketData[currentTick].timestamp, side: 'Sell', symbol, qty, price, cost }]);
      addLog(`[FILLED] SELL ${qty} ${symbol} @ $${price.toFixed(2)} (+$${cost.toFixed(2)})`);
    }
  };

  return (
    <div className="p-8 text-white min-h-screen" style={{ backgroundColor: '#0f172a' }}>
      <div className="max-w-5xl mx-auto" style={{ background: '#1e293b', padding: '2rem', borderRadius: '12px', boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)' }}>
        <h1 className="text-3xl font-bold flex justify-between items-center mb-6" style={{ color: '#38bdf8' }}>
          Real-Time Market Simulator
          <div className="flex items-center space-x-4">
            <select
              value={selectedScenario}
              onChange={(e) => setSelectedScenario(e.target.value)}
              className="text-sm px-3 py-1.5 rounded-full"
              style={{ background: '#1e293b', border: '1px solid #475569', color: 'white', cursor: 'pointer' }}
            >
              {scenarios.map(scen => <option key={scen} value={scen}>{scen}</option>)}
            </select>
            <span className={`text-sm px-3 py-1.5 rounded-full ${isRunning ? 'animate-pulse' : ''}`}
              style={{ background: isRunning ? '#10b981' : '#475569', color: '#f8fafc' }}>
              {simStatus}
            </span>
          </div>
        </h1>

        <div className="text-center text-xl mb-8 font-mono" style={{ color: '#94a3b8' }}>
          {currentDate}
        </div>

        <div className="grid grid-cols-4 gap-4 mb-8">
          <div className="col-span-2 p-6 rounded-lg text-center border-l-4" style={{ background: '#334155', borderColor: '#38bdf8' }}>
            <div className="text-sm uppercase tracking-wider text-slate-300">Net Asset Value</div>
            <div className="text-3xl font-bold mt-2 font-mono">${nav.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
          </div>
          <div className="col-span-2 p-6 rounded-lg text-center border-l-4" style={{ background: '#334155', borderColor: '#10b981' }}>
            <div className="text-sm uppercase tracking-wider text-slate-300">Available Cash</div>
            <div className="text-3xl font-bold mt-2 font-mono">${cash.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
          </div>
          {/* Position Summary Cards */}
          {uniqueSymbols.map(sym => (
            <div key={`summary-${sym}`} className="p-4 rounded-lg text-center border-l-4" style={{ background: '#334155', borderColor: '#475569' }}>
              <div className="text-sm uppercase tracking-wider text-slate-300">{sym} Shares</div>
              <div className="text-2xl font-bold mt-2 font-mono">{portfolioPositions[sym] || 0}</div>
            </div>
          ))}
        </div>

        <div className="flex justify-center space-x-4 mb-8">
          {!isRunning ? (
            <button
              onClick={startSim}
              disabled={marketData.length === 0}
              className="bg-blue-500 hover:bg-blue-600 text-white px-8 py-3 rounded-lg text-lg font-bold disabled:opacity-50 transition-colors"
            >
              {currentTick > 0 ? "▶ Resume Simulation Pipeline" : "▶ Start Simulation Pipeline"}
            </button>
          ) : (
            <button
              onClick={stopSim}
              className="bg-amber-500 hover:bg-amber-600 text-white px-8 py-3 rounded-lg text-lg font-bold transition-colors"
            >
              ⏸ Pause Simulation
            </button>
          )}
        </div>

        <div className="grid grid-cols-2 gap-4 mb-8">
          {uniqueSymbols.map(sym => {
            const currentPrice = currentPrices[sym] || 0;
            const prevPrice = prevPrices[sym] || 0;
            const isDown = currentPrice < prevPrice;

            return (
              <div key={`trade-${sym}`} className="p-6 rounded-lg border" style={{ background: '#0f172a', borderColor: '#334155' }}>
                <div className="flex justify-between items-center mb-4">
                  <div className="text-2xl font-bold text-slate-100">{sym}</div>
                  <div className={`text-3xl font-bold font-mono ${isDown ? 'text-red-500' : 'text-emerald-500'}`}>
                    ${currentPrice.toFixed(2)}
                  </div>
                </div>
                <div className="text-slate-300 mb-4">
                  Owned: <span className="font-mono">{portfolioPositions[sym] || 0}</span> | Value: <span className="font-mono">${((portfolioPositions[sym] || 0) * currentPrice).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                </div>
                <div className="flex space-x-2">
                  <input
                    type="number"
                    min="1"
                    value={quantities[sym] || ''}
                    onChange={(e) => setQuantities(prev => ({ ...prev, [sym]: e.target.value }))}
                    className="flex-1 px-3 py-2 rounded-lg text-white"
                    style={{ background: '#1e293b', border: '1px solid #475569' }}
                  />
                  <button
                    onClick={() => handleTrade('Buy', sym)}
                    disabled={!isRunning}
                    className="bg-emerald-500 hover:bg-emerald-600 text-white px-4 py-2 rounded-lg font-bold disabled:opacity-50 transition-colors"
                  >
                    Buy
                  </button>
                  <button
                    onClick={() => handleTrade('Sell', sym)}
                    disabled={!isRunning}
                    className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg font-bold disabled:opacity-50 transition-colors"
                  >
                    Sell
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        <div className="p-4 rounded-lg font-mono text-sm h-40 overflow-y-auto mb-8" style={{ background: '#000', color: '#a3e635' }}>
          {logs.map((log, i) => <div key={i}>{log}</div>)}
          <div ref={logsEndRef} />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 rounded-lg border" style={{ background: '#1e293b', borderColor: '#334155', maxHeight: '300px', overflowY: 'auto' }}>
            <h3 className="text-xl font-bold mb-4 pb-2 border-b" style={{ color: '#38bdf8', borderColor: '#334155' }}>Holdings Summary</h3>
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="text-xs uppercase bg-slate-800 text-slate-100">
                <tr>
                  <th className="px-2 py-2">Symbol</th>
                  <th className="px-2 py-2">Shares</th>
                  <th className="px-2 py-2">Price</th>
                  <th className="px-2 py-2">Total Value</th>
                </tr>
              </thead>
              <tbody>
                {uniqueSymbols.map(sym => (
                  <tr key={`holding-${sym}`} className="border-b" style={{ borderColor: '#334155' }}>
                    <td className="px-2 py-2">{sym}</td>
                    <td className="px-2 py-2 font-mono">{portfolioPositions[sym] || 0}</td>
                    <td className="px-2 py-2 font-mono">${(currentPrices[sym] || 0).toFixed(2)}</td>
                    <td className="px-2 py-2 font-mono">${((portfolioPositions[sym] || 0) * (currentPrices[sym] || 0)).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="p-4 rounded-lg border" style={{ background: '#1e293b', borderColor: '#334155', maxHeight: '300px', overflowY: 'auto' }}>
            <h3 className="text-xl font-bold mb-4 pb-2 border-b" style={{ color: '#38bdf8', borderColor: '#334155' }}>Trade Ledger</h3>
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="text-xs uppercase bg-slate-800 text-slate-100">
                <tr>
                  <th className="px-2 py-2">Time</th>
                  <th className="px-2 py-2">Side</th>
                  <th className="px-2 py-2">Symbol</th>
                  <th className="px-2 py-2">Qty</th>
                  <th className="px-2 py-2">Price</th>
                  <th className="px-2 py-2">Cost/Proceeds</th>
                </tr>
              </thead>
              <tbody>
                {[...tradeLog].reverse().map((log, i) => (
                  <tr key={i} className="border-b" style={{ borderColor: '#334155' }}>
                    <td className="px-2 py-2 font-mono text-xs">{log.time}</td>
                    <td className={`px-2 py-2 font-bold ${log.side === 'Buy' ? 'text-emerald-500' : 'text-red-500'}`}>{log.side}</td>
                    <td className="px-2 py-2">{log.symbol}</td>
                    <td className="px-2 py-2 font-mono">{log.qty}</td>
                    <td className="px-2 py-2 font-mono">${log.price.toFixed(2)}</td>
                    <td className="px-2 py-2 font-mono">${log.cost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SimulationPage;