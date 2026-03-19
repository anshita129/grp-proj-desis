import React, { useState, useEffect, useRef } from 'react';
import PriceHistoryGraph from '../components/PriceHistoryGraph';
import { csrfFetch, readJsonSafe } from "../../users/auth/http";

const MARKET_DATA_URL = "/api/simulation/market-data/";
const SCENARIOS_URL = "/api/simulation/scenarios/";

function SimulationPage() {
  const [scenarios, setScenarios] = useState([]);
  const [selectedScenario, setSelectedScenario] = useState("Loading scenarios...");
  const [simStatus, setSimStatus] = useState("Offline");
  const [isRunning, setIsRunning] = useState(false);

  // History state
  const [showHistory, setShowHistory] = useState(false);
  const [historySessions, setHistorySessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);

  // Core state
  const [marketData, setMarketData] = useState([]);
  const [uniqueSymbols, setUniqueSymbols] = useState([]);
  const [currentTick, setCurrentTick] = useState(0);

  // Display values
  const [currentDate, setCurrentDate] = useState("YYYY-MM-DD HH:MM");
  const [nav, setNav] = useState(10000.00);
  const [navTrend, setNavTrend] = useState("neutral");
  const [prevNavForTrend, setPrevNavForTrend] = useState(10000.00);
  const [cash, setCash] = useState(10000.00);
  const [portfolioPositions, setPortfolioPositions] = useState({});
  const [currentPrices, setCurrentPrices] = useState({});
  const [prevPrices, setPrevPrices] = useState({});
  const [tradeLog, setTradeLog] = useState([]);
  const [logs, setLogs] = useState(["System initialized. Waiting for data feed..."]);

  // Individual inputs per symbol
  const [quantities, setQuantities] = useState({});

  const logsContainerRef = useRef(null);
  const simIntervalRef = useRef(null);

  const fetchScenarios = async () => {
    try {
      const res = await fetch(SCENARIOS_URL);
      const data = await res.json();
      if (data.scenarios && data.scenarios.length > 0) {
        setScenarios(data.scenarios);
        return data.scenarios;
      } else {
        setScenarios(["No scenarios found"]);
        return [];
      }
    } catch (e) {
      console.error("Failed to fetch scenarios", e);
      addLog("Error loading scenarios from backend.");
      return [];
    }
  };

  const fetchHistory = async () => {
    try {
      const res = await fetch('/api/simulation/sessions/', { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        setHistorySessions(data);
      }
    } catch (e) { console.error("History fetch error", e); }
  };

  const saveProgress = async () => {
    const stateToSave = {
      selectedScenario, currentTick, nav,
      navTrend, prevNavForTrend, cash, portfolioPositions,
      currentPrices, prevPrices, tradeLog, logs
    };

    const payload = {
      name: `${selectedScenario} - Tick ${currentTick}`,
      scenario: selectedScenario,
      current_tick: currentTick,
      nav: nav,
      cash: cash,
      state_data: stateToSave
    };

    try {
      const method = currentSessionId ? 'PUT' : 'POST';
      const url = currentSessionId ? `/api/simulation/sessions/${currentSessionId}/` : '/api/simulation/sessions/';

      const res = await csrfFetch(url, {
        method,
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const data = await res.json();
        setCurrentSessionId(data.id);
        addLog(`Progress saved to cloud successfully (ID: ${data.id}).`);
      } else {
        const data = await readJsonSafe(res);
        addLog(`Failed to save progress to cloud: ${data?.detail || 'Unauthorized'}`);
      }
    } catch (e) {
      addLog("Network error saving progress.");
    }
  };

  const loadHistorySession = async (session) => {
    try {
      const savedState = session.state_data;
      if (savedState && savedState.selectedScenario) {
        if (isRunning) stopSim();
        setSelectedScenario(savedState.selectedScenario);
        await fetchMarketData(savedState.selectedScenario, true);

        setCurrentTick(savedState.currentTick || 0);
        setNav(savedState.nav || 10000.00);
        setNavTrend(savedState.navTrend || "neutral");
        setPrevNavForTrend(savedState.prevNavForTrend || 10000.00);
        setCash(savedState.cash || 10000.00);
        setPortfolioPositions(savedState.portfolioPositions || {});
        setCurrentPrices(savedState.currentPrices || {});
        setPrevPrices(savedState.prevPrices || {});
        setTradeLog(savedState.tradeLog || []);
        setLogs(savedState.logs || ["System initialized."]);
        setSimStatus("Paused (Resumed from Cloud)");
        setCurrentSessionId(session.id);
        setShowHistory(false);
        addLog(`Successfully loaded cloud session: ${session.name}`);
      }
    } catch (e) {
      console.error("Load session error", e);
      addLog("Failed to completely resume session from cloud.");
    }
  };

  // Initial load
  useEffect(() => {
    const doInit = async () => {
      const scenariosList = await fetchScenarios();

      // Load the default scenario
      if (scenariosList.length > 0) {
        const defaultScen = scenariosList.includes("market_simulation_data.csv")
          ? "market_simulation_data.csv"
          : scenariosList[0];
        setSelectedScenario(defaultScen);
        resetAndLoadScenario(defaultScen);
      }
    };
    doInit();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Auto-scroll logs
  useEffect(() => {
    if (logsContainerRef.current) {
      logsContainerRef.current.scrollTop = logsContainerRef.current.scrollHeight;
    }
  }, [logs]);

  const addLog = (msg) => {
    const time = new Date().toLocaleTimeString();
    setLogs(prev => [...prev, `[${time}] ${msg}`]);
  };

  const handleScenarioChange = (e) => {
    const newScenario = e.target.value;
    setSelectedScenario(newScenario);
    setCurrentSessionId(null); // Clear cloud ID so it creates a new save branch
    if (newScenario !== "Loading scenarios..." && newScenario !== "No scenarios found") {
      resetAndLoadScenario(newScenario);
    }
  };

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

  const fetchMarketData = async (scenarioName, skipInit = false) => {
    try {
      addLog(`Fetching data feed for scenario: ${scenarioName}...`);
      const res = await fetch(`${MARKET_DATA_URL}?scenario=${encodeURIComponent(scenarioName)}`);
      const data = await res.json();

      if (data.error) {
        addLog(`ERROR: ${data.error}`);
        return false;
      }

      let groupedByTime = {};
      let groupedOhlc = {};
      let times = [];
      let symbolSet = new Set();

      data.data.forEach(row => {
        let ts = row.timestamp || row.Date;
        if (!groupedByTime[ts]) {
          groupedByTime[ts] = {};
          groupedOhlc[ts] = {};
          times.push(ts);
        }
        let sym = (row.symbol || row.Symbol).toUpperCase();
        symbolSet.add(sym);
        groupedByTime[ts][sym] = parseFloat(row.close || row.Close);

        groupedOhlc[ts][sym] = {
          open: parseFloat(row.open || row.Open || row.close || row.Close),
          high: parseFloat(row.high || row.High || row.close || row.Close),
          low: parseFloat(row.low || row.Low || row.close || row.Close),
          close: parseFloat(row.close || row.Close),
        };
      });

      const parsedMarketData = times.map(ts => ({
        timestamp: ts,
        prices: groupedByTime[ts],
        ohlc: groupedOhlc[ts]
      }));
      const parsedSymbols = Array.from(symbolSet).sort();

      setMarketData(parsedMarketData);
      setUniqueSymbols(parsedSymbols);

      // Initialize positions & prices
      if (!skipInit) {
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
      } else {
        // Just initialize quantities for the form inputs
        const initQtys = {};
        parsedSymbols.forEach(sym => { initQtys[sym] = 10; });
        setQuantities(initQtys);
      }

      addLog(`Received ${parsedMarketData.length} unique market time ticks for ${parsedSymbols.length} symbols.`);
      if (!skipInit) setSimStatus("Ready");
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
    const newNav = cash + positionsValue;
    setNav(newNav);

    if (newNav > prevNavForTrend && newNav > 10000.00) {
      setNavTrend("up");
    } else if (newNav < prevNavForTrend || newNav < 10000.00) {
      // Show sad if it dropped on the current tick, or if the overall portfolio is underwater
      setNavTrend(newNav < prevNavForTrend ? "down" : navTrend);
      if (newNav < 10000.00) setNavTrend("down");
    } else {
      setNavTrend("neutral");
    }
    setPrevNavForTrend(newNav);
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
    <div className="p-8 text-slate-100 min-h-screen bg-slate-900 font-sans selection:bg-blue-500/30">
      <div className="max-w-6xl mx-auto space-y-8">

        {/* Header Section */}
        <div className="relative bg-slate-800/80 backdrop-blur-md rounded-2xl p-8 border border-slate-700/50 shadow-2xl overflow-hidden flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="z-10 bg-gradient-to-r from-blue-500 to-indigo-500 absolute top-0 left-0 w-2 h-full"></div>

          <div className="flex-1 pl-4 z-10 flex items-center gap-6">
            <div className="relative group">
              <div className={`absolute -inset-1 rounded-full blur opacity-40 group-hover:opacity-100 transition duration-500 ${navTrend === 'up' ? 'bg-gradient-to-r from-emerald-400 to-green-500' : navTrend === 'down' ? 'bg-gradient-to-r from-red-500 to-rose-400' : 'bg-gradient-to-r from-blue-400 to-indigo-500'}`}></div>
              <img src={navTrend === 'up' ? '/teddy_happy.png' : navTrend === 'down' ? '/teddy_sad.png' : '/teddy_neutral.png'} alt="Mascot" className={`w-28 h-28 object-contain rounded-full relative bg-slate-800 border-4 shadow-xl transform group-hover:scale-105 transition-all duration-300 ${navTrend === 'up' ? 'border-emerald-500 drop-shadow-[0_0_15px_rgba(16,185,129,0.5)]' : navTrend === 'down' ? 'border-red-500 drop-shadow-[0_0_15px_rgba(239,68,68,0.5)]' : 'border-slate-600'}`} />
            </div>
            <div>
              <h1 className="text-4xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 via-blue-400 to-indigo-400 tracking-tight">
                Market Simulator Pro
              </h1>
              <p className="text-slate-400 mt-2 text-lg">Master the markets with our historical time-travel engine.</p>
            </div>
          </div>

          {/* Controls */}
          <div className="z-10 flex flex-col items-end gap-4 bg-slate-900/50 p-4 rounded-xl border border-slate-700 w-full md:w-auto">
            <div className="flex items-center space-x-3 w-full border-b border-slate-700 pb-3 mb-2">
              <button
                onClick={() => {
                  if (confirm("Are you sure you want to completely restart this scenario? Unsaved progress will be lost.")) {
                    resetAndLoadScenario(selectedScenario);
                  }
                }}
                className="px-4 py-2 bg-rose-600/80 hover:bg-rose-500 text-white rounded-lg text-sm font-semibold transition-colors flex-1 w-full text-center" title="Restart Scenario from Day 1">
                Restart
              </button>
              <button onClick={() => { setShowHistory(true); fetchHistory(); }} className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-semibold transition-colors flex-1 w-full text-center">
                History
              </button>
              <button onClick={saveProgress} className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-semibold transition-colors flex-1 w-full text-center shadow-lg shadow-indigo-500/20">
                Save Cloud
              </button>
            </div>
            <div className="flex items-center space-x-3 w-full">
              <label className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Scenario</label>
              <select
                value={selectedScenario}
                onChange={handleScenarioChange}
                className="flex-1 bg-slate-800 border border-slate-600 text-slate-200 text-sm px-4 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all shadow-inner appearance-none min-w-[200px]"
                style={{ backgroundImage: `url("data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22292.4%22%20height%3D%22292.4%22%3E%3Cpath%20fill%3D%22%2394a3b8%22%20d%3D%22M287%2069.4a17.6%2017.6%200%200%200-13-5.4H18.4c-5%200-9.3%201.8-12.9%205.4A17.6%2017.6%200%200%200%200%2082.2c0%205%201.8%209.3%205.4%2012.9l128%20127.9c3.6%203.6%207.8%205.4%2012.8%205.4s9.2-1.8%2012.8-5.4L287%2095c3.5-3.5%205.4-7.8%205.4-12.8%200-5-1.9-9.2-5.5-12.8z%22%2F%3E%3C%2Fsvg%3E")`, backgroundRepeat: 'no-repeat', backgroundPosition: 'right .7rem top 50%', backgroundSize: '.65rem auto' }}
              >
                {scenarios.map(scen => <option key={scen} value={scen}>{scen}</option>)}
              </select>
            </div>

            <div className="flex items-center justify-between w-full">
              <span className={`text-xs px-3 py-1 font-bold rounded-full border ${isRunning ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' : 'bg-slate-700/50 text-slate-400 border-slate-600'}`}>
                {isRunning ? (
                  <span className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span> {simStatus}</span>
                ) : (
                  simStatus
                )}
              </span>
              <div className="text-right text-lg font-mono font-medium text-indigo-300 bg-indigo-900/30 px-3 py-1 rounded-lg border border-indigo-500/30 shadow-inner">
                {currentDate}
              </div>
            </div>
          </div>
        </div>

        {/* Top Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-gradient-to-br from-slate-800 to-slate-800/80 rounded-2xl p-6 border border-slate-700 shadow-xl relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/10 rounded-full blur-3xl -mr-10 -mt-10 transition-transform group-hover:scale-150 duration-700"></div>
            <div className="text-sm font-semibold uppercase tracking-widest text-blue-400 mb-2">Net Asset Value</div>
            <div className="text-4xl font-extrabold font-mono text-white tracking-tight">${nav.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
          </div>

          <div className="bg-gradient-to-br from-slate-800 to-slate-800/80 rounded-2xl p-6 border border-slate-700 shadow-xl relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 rounded-full blur-3xl -mr-10 -mt-10 transition-transform group-hover:scale-150 duration-700"></div>
            <div className="text-sm font-semibold uppercase tracking-widest text-emerald-400 mb-2">Available Cash</div>
            <div className="text-4xl font-extrabold font-mono text-white tracking-tight">${cash.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
          </div>

          {uniqueSymbols.map((sym, idx) => {
            const colors = ['from-purple-500/10', 'from-amber-500/10', 'from-pink-500/10', 'from-cyan-500/10'];
            const textColors = ['text-purple-400', 'text-amber-400', 'text-pink-400', 'text-cyan-400'];
            const c = colors[idx % colors.length];
            const tc = textColors[idx % textColors.length];
            return (
              <div key={`summary-${sym}`} className="bg-gradient-to-br from-slate-800 to-slate-800/80 rounded-2xl p-6 border border-slate-700 shadow-xl relative overflow-hidden group">
                <div className={`absolute top-0 right-0 w-32 h-32 ${c} rounded-full blur-3xl -mr-10 -mt-10 transition-transform group-hover:scale-150 duration-700`}></div>
                <div className={`text-sm font-semibold uppercase tracking-widest ${tc} mb-2`}>{sym} Position</div>
                <div className="text-4xl font-extrabold font-mono text-white tracking-tight">
                  {portfolioPositions[sym] || 0} <span className="text-lg text-slate-500 font-sans tracking-normal">shares</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Global Action Bar */}
        <div className="flex justify-center my-8">
          {!isRunning ? (
            <button
              onClick={startSim}
              disabled={marketData.length === 0}
              className="group relative inline-flex items-center justify-center px-8 py-4 font-bold text-white transition-all duration-300 bg-gradient-to-r from-emerald-500 to-teal-600 rounded-xl hover:from-emerald-400 hover:to-teal-500 focus:outline-none focus:ring-4 focus:ring-emerald-500/50 disabled:opacity-50 disabled:cursor-not-allowed shadow-[0_0_20px_rgba(16,185,129,0.3)] hover:shadow-[0_0_30px_rgba(16,185,129,0.6)] transform hover:-translate-y-1"
            >
              <span className="mr-2 text-xl">{currentTick > 0 ? "▶" : "🚀"}</span>
              {currentTick > 0 ? "Resume Simulation Pipeline" : "Start Simulation Pipeline"}
            </button>
          ) : (
            <button
              onClick={stopSim}
              className="group relative inline-flex items-center justify-center px-8 py-4 font-bold text-white transition-all duration-300 bg-gradient-to-r from-amber-500 to-orange-600 rounded-xl hover:from-amber-400 hover:to-orange-500 focus:outline-none focus:ring-4 focus:ring-amber-500/50 shadow-[0_0_20px_rgba(245,158,11,0.3)] hover:shadow-[0_0_30px_rgba(245,158,11,0.6)] transform hover:-translate-y-1"
            >
              <span className="mr-2 text-xl">⏸</span>
              Pause Simulation
            </button>
          )}
        </div>

        {/* Trading Terminals */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {uniqueSymbols.map(sym => {
            const currentPrice = currentPrices[sym] || 0;
            const prevPrice = prevPrices[sym] || 0;
            const isDown = currentPrice < prevPrice;
            const colorClass = isDown ? 'text-red-400' : 'text-emerald-400';
            const bgGlow = isDown ? 'bg-red-500/5' : 'bg-emerald-500/5';

            return (
              <div key={`trade-${sym}`} className={`relative bg-slate-800 border border-slate-700 rounded-2xl p-6 shadow-xl transition-all duration-300 hover:border-slate-500 overflow-hidden group ${bgGlow}`}>
                {/* Background decorative element */}
                <div className={`absolute -right-20 -top-20 w-64 h-64 rounded-full blur-3xl opacity-20 ${isDown ? 'bg-red-500' : 'bg-emerald-500'}`}></div>

                <div className="relative z-10 flex flex-col sm:flex-row justify-between items-start mb-6 gap-4 transition-opacity duration-300">
                  <div>
                    <h2 className="text-3xl font-black tracking-tight text-white mb-1">{sym}</h2>
                    <div className="flex items-center gap-3">
                      <span className="text-slate-400 text-sm font-medium">Owned:</span>
                      <span className="font-mono text-lg font-bold bg-slate-900 px-3 py-1 rounded-lg border border-slate-700">{portfolioPositions[sym] || 0}</span>
                    </div>
                  </div>
                  <div className="text-left sm:text-right">
                    <div className={`text-4xl font-extrabold font-mono tracking-tighter ${colorClass} drop-shadow-[0_0_10px_rgba(0,0,0,0.5)]`}>
                      ${currentPrice.toFixed(2)}
                    </div>
                    <div className="text-sm font-medium text-slate-400 mt-1">
                      Value: <span className="font-mono text-white">${((portfolioPositions[sym] || 0) * currentPrice).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                    </div>
                  </div>
                </div>

                <div className="relative z-30 bg-slate-900/50 p-4 rounded-xl border border-slate-700/50">
                  <div className="flex flex-col sm:flex-row gap-3">
                    <div className="relative flex-1">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <span className="text-slate-500 font-semibold">Qty</span>
                      </div>
                      <input
                        type="number"
                        min="1"
                        value={quantities[sym] || ''}
                        onChange={(e) => setQuantities(prev => ({ ...prev, [sym]: e.target.value }))}
                        className="w-full bg-slate-900 border border-slate-600 text-white font-mono text-lg pl-12 pr-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all placeholder-slate-600"
                        placeholder="0"
                      />
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleTrade('Buy', sym)}
                        disabled={!isRunning}
                        className="flex-1 sm:flex-none bg-emerald-500/20 text-emerald-400 border border-emerald-500/50 hover:bg-emerald-500 hover:text-white px-6 py-3 rounded-lg font-bold disabled:opacity-30 disabled:hover:bg-emerald-500/20 disabled:hover:text-emerald-400 transition-all shadow-[0_0_10px_rgba(16,185,129,0.1)] hover:shadow-[0_0_15px_rgba(16,185,129,0.4)]"
                      >
                        Buy
                      </button>
                      <button
                        onClick={() => handleTrade('Sell', sym)}
                        disabled={!isRunning}
                        className="flex-1 sm:flex-none bg-red-500/20 text-red-400 border border-red-500/50 hover:bg-red-500 hover:text-white px-6 py-3 rounded-lg font-bold disabled:opacity-30 disabled:hover:bg-red-500/20 disabled:hover:text-red-400 transition-all shadow-[0_0_10px_rgba(239,68,68,0.1)] hover:shadow-[0_0_15px_rgba(239,68,68,0.4)]"
                      >
                        Sell
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Full Candlestick Charts Row */}
        {uniqueSymbols.length > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {uniqueSymbols.map(sym => (
              <PriceHistoryGraph
                key={`chart-${sym}`}
                marketData={marketData}
                currentTick={currentTick}
                symbol={sym}
              />
            ))}
          </div>
        )}

        {/* Terminal / Logs Row */}
        <div className="bg-slate-950 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl relative">
          <div className="bg-slate-900 border-b border-slate-800 px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500/80"></div>
              <div className="w-3 h-3 rounded-full bg-amber-500/80"></div>
              <div className="w-3 h-3 rounded-full bg-emerald-500/80"></div>
              <span className="ml-3 text-xs font-semibold text-slate-500 uppercase tracking-widest">System Output</span>
            </div>
          </div>
          <div ref={logsContainerRef} className="p-4 font-mono text-sm h-48 overflow-y-auto" style={{ color: '#a3e635' }}>
            {logs.map((log, i) => (
              <div key={i} className={`py-1 border-b border-slate-900/50 opacity-90 hover:opacity-100 hover:bg-slate-900 transition-colors ${log.includes('ERROR') || log.includes('DECLINED') ? 'text-red-400' : ''}`}>
                <span className="text-slate-500 select-none mr-3">❯</span>
                {log}
              </div>
            ))}
          </div>
        </div>

        {/* Ledger & Holdings */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-slate-800 border border-slate-700 rounded-2xl flex flex-col shadow-xl overflow-hidden h-[400px]">
            <div className="bg-slate-900/50 border-b border-slate-700 px-6 py-4">
              <h3 className="text-lg font-bold text-blue-400 flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z" />
                </svg>
                Holdings Summary
              </h3>
            </div>
            <div className="flex-1 overflow-auto">
              <table className="w-full text-left text-sm whitespace-nowrap">
                <thead className="text-xs uppercase bg-slate-800/80 text-slate-400 sticky top-0 backdrop-blur-sm z-10 border-b border-slate-700">
                  <tr>
                    <th className="px-6 py-3 font-semibold">Symbol</th>
                    <th className="px-6 py-3 font-semibold text-right">Shares</th>
                    <th className="px-6 py-3 font-semibold text-right">Current Price</th>
                    <th className="px-6 py-3 font-semibold text-right">Total Value</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700/50">
                  {uniqueSymbols.map((sym, idx) => (
                    <tr key={`holding-${sym}`} className={`hover:bg-slate-700/30 transition-colors ${idx % 2 === 0 ? 'bg-slate-800/30' : ''}`}>
                      <td className="px-6 py-4 font-bold text-white tracking-wider">{sym}</td>
                      <td className="px-6 py-4 font-mono text-right text-slate-200">{portfolioPositions[sym] || 0}</td>
                      <td className="px-6 py-4 font-mono text-right text-slate-300">${(currentPrices[sym] || 0).toFixed(2)}</td>
                      <td className="px-6 py-4 font-mono font-bold text-right text-emerald-400">
                        ${((portfolioPositions[sym] || 0) * (currentPrices[sym] || 0)).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </td>
                    </tr>
                  ))}
                  {uniqueSymbols.length === 0 && (
                    <tr>
                      <td colSpan="4" className="px-6 py-8 text-center text-slate-500 italic">No holdings available. Start an engine feed.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="bg-slate-800 border border-slate-700 rounded-2xl flex flex-col shadow-xl overflow-hidden h-[400px]">
            <div className="bg-slate-900/50 border-b border-slate-700 px-6 py-4 flex justify-between items-center">
              <h3 className="text-lg font-bold text-purple-400 flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
                </svg>
                Trade Ledger
              </h3>
              <span className="text-xs bg-slate-700 text-slate-300 px-2 py-1 rounded-full">{tradeLog.length} Executions</span>
            </div>
            <div className="flex-1 overflow-auto">
              <table className="w-full text-left text-sm whitespace-nowrap">
                <thead className="text-xs uppercase bg-slate-800/80 text-slate-400 sticky top-0 backdrop-blur-sm z-10 border-b border-slate-700">
                  <tr>
                    <th className="px-6 py-3 font-semibold">Time</th>
                    <th className="px-4 py-3 font-semibold">Side</th>
                    <th className="px-4 py-3 font-semibold">Symbol</th>
                    <th className="px-4 py-3 font-semibold text-right">Qty</th>
                    <th className="px-4 py-3 font-semibold text-right">Price</th>
                    <th className="px-6 py-3 font-semibold text-right">Value</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700/50">
                  {[...tradeLog].reverse().map((log, i) => (
                    <tr key={i} className="hover:bg-slate-700/30 transition-colors">
                      <td className="px-6 py-3 font-mono text-xs text-slate-400">{log.time.split(' ')[1] || log.time}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded text-xs font-bold ${log.side === 'Buy' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-red-500/20 text-red-400 border border-red-500/30'}`}>
                          {log.side.toUpperCase()}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-bold text-white">{log.symbol}</td>
                      <td className="px-4 py-3 font-mono text-right text-slate-300">{log.qty}</td>
                      <td className="px-4 py-3 font-mono text-right text-slate-300">${log.price.toFixed(2)}</td>
                      <td className="px-6 py-3 font-mono text-right font-medium text-slate-200">${log.cost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                    </tr>
                  ))}
                  {tradeLog.length === 0 && (
                    <tr>
                      <td colSpan="6" className="px-6 py-8 text-center text-slate-500 italic">No trades executed yet.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

      </div>

      {showHistory && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-950/80 backdrop-blur-md p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-3xl shadow-[0_0_50px_rgba(0,0,0,0.5)] flex flex-col max-h-[85vh] animate-in fade-in zoom-in duration-300">
            <div className="bg-gradient-to-r from-slate-800 to-slate-900 p-6 border-b border-slate-700 flex justify-between items-center rounded-t-2xl">
              <h2 className="text-2xl font-black text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-indigo-400 flex items-center gap-3 tracking-tight">
                <span className="text-blue-500 text-3xl">☁️</span> Cloud Sessions
              </h2>
              <button onClick={() => setShowHistory(false)} className="text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 w-10 h-10 rounded-full flex items-center justify-center transition-all shadow-md">
                ✕
              </button>
            </div>
            <div className="p-6 overflow-y-auto flex-1 bg-slate-950/50">
              {historySessions.length === 0 ? (
                <div className="text-center text-slate-500 py-16 flex flex-col items-center">
                  <span className="text-6xl mb-4 opacity-20">📭</span>
                  <p className="text-lg">No cloud sessions found.</p>
                  <p className="text-sm mt-1">Play a scenario and click "Save Cloud" to store your progress forever.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {historySessions.map(sess => (
                    <div key={sess.id} className={`p-5 rounded-2xl border flex flex-col sm:flex-row sm:items-center justify-between gap-5 transition-all outline outline-2 outline-offset-2 hover:-translate-y-1 ${currentSessionId === sess.id ? 'bg-indigo-900/40 border-indigo-500/50 outline-indigo-500/30' : 'bg-slate-800/80 border-slate-700 outline-transparent hover:border-slate-500 hover:shadow-lg'}`}>
                      <div className="flex-1">
                        <div className="font-bold text-white text-lg mb-2 flex items-center gap-2">
                          {sess.name}
                          {currentSessionId === sess.id && <span className="px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-400 text-xs uppercase tracking-widest border border-indigo-500/30">Active</span>}
                        </div>
                        <div className="flex flex-wrap gap-3 text-xs text-slate-300 font-mono">
                          <span className="bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-700 shadow-inner flex flex-col"><span className="text-slate-500 uppercase text-[10px] tracking-wider mb-0.5">Time</span> {new Date(sess.updated_at).toLocaleDateString()} {new Date(sess.updated_at).toLocaleTimeString()}</span>
                          <span className="bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-700 shadow-inner flex flex-col"><span className="text-slate-500 uppercase text-[10px] tracking-wider mb-0.5">NAV</span> <span className="text-blue-400 font-bold">${sess.nav?.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span></span>
                          <span className="bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-700 shadow-inner flex flex-col"><span className="text-slate-500 uppercase text-[10px] tracking-wider mb-0.5">Tick</span> <span className="text-emerald-400 font-bold">{sess.current_tick}</span></span>
                        </div>
                      </div>
                      <button onClick={() => loadHistorySession(sess)} className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white px-6 py-3 rounded-xl font-bold shadow-lg shadow-indigo-600/30 transition-all flex items-center justify-center gap-2 whitespace-nowrap active:scale-95">
                        <span className="text-xl">📥</span> Load Data
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
            {historySessions.length > 0 && (
              <div className="bg-slate-900 border-t border-slate-800 p-4 text-center text-xs text-slate-500 uppercase tracking-widest font-semibold flex justify-center items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span> Cloud Sync Active ({historySessions.length} total)
              </div>
            )}
          </div>
        </div>
      )}

    </div >
  );
}

export default SimulationPage;
