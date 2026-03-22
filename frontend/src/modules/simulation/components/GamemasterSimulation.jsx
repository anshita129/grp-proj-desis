import React, { useState, useEffect, useRef } from 'react';

const MARKET_DATA_URL = "/api/simulation/market-data/";
const SCENARIOS_URL = "/api/simulation/scenarios/";

const clamp = (min, max, v) => Math.max(min, Math.min(max, v));

const stdev = (values) => {
    if (!values || values.length < 2) return 0;
    const mean = values.reduce((a, b) => a + b, 0) / values.length;
    const varSum = values.reduce((acc, v) => acc + (v - mean) ** 2, 0);
    return Math.sqrt(varSum / (values.length - 1));
};

const parseScenarioToTicks = (rows) => {
    const grouped = new Map(); // ts -> Map(sym -> {close, volume})
    const symbols = new Set();

    for (const row of rows) {
        const ts = (row.timestamp || row.Date || row.date || row.TIME || row.time || "").toString();
        const sym = ((row.symbol || row.Symbol || row.SYMBOL || "") + "").toUpperCase();
        const closeRaw = row.close ?? row.Close ?? row.CLOSE;
        const volumeRaw = row.volume ?? row.Volume ?? row.VOLUME;

        if (!ts || !sym) continue;

        const close = Number.parseFloat(closeRaw);
        const volume = Number.parseFloat(volumeRaw);
        if (!Number.isFinite(close)) continue;

        if (!grouped.has(ts)) grouped.set(ts, new Map());
        grouped.get(ts).set(sym, { close, volume: Number.isFinite(volume) ? volume : null });
        symbols.add(sym);
    }

    const timestamps = Array.from(grouped.keys()).sort(); // ISO timestamps sort lexicographically
    const ticks = timestamps.map(ts => {
        const bars = {};
        grouped.get(ts).forEach((bar, sym) => {
            bars[sym] = bar;
        });
        return { timestamp: ts, bars };
    });

    return { ticks, symbols: Array.from(symbols).sort() };
};

const computeLevelObjective = ({ ticks, symbols, duration, startingCash, difficultyFactor }) => {
    const primary = symbols[0];
    const closes = [];
    for (let i = 0; i < Math.min(duration, ticks.length); i++) {
        const bar = ticks[i]?.bars?.[primary];
        if (bar?.close != null) closes.push(bar.close);
    }

    const returns = [];
    for (let i = 1; i < closes.length; i++) {
        returns.push((closes[i] - closes[i - 1]) / closes[i - 1]);
    }
    const vol = stdev(returns) || 0.02;

    const estLevelVol = vol * Math.sqrt(duration);
    const diff = clamp(0, 1, Number.isFinite(difficultyFactor) ? difficultyFactor : 0);

    // Ramp difficulty gently while keeping targets kid-achievable.
    const passFloor = 0.93 + (0.05 * diff); // 93% -> 98%
    const baseBonus = 0.004 + (0.010 * diff); // 0.4% -> 1.4%
    const volBonus = clamp(0.0, 0.008, estLevelVol * 0.05);
    const bonusReturn = clamp(0.004, 0.02, baseBonus + volBonus);
    const drawdownLimit = clamp(0.55, 0.85, 0.85 - (0.25 * diff)); // 85% -> 60%

    return {
        passNav: startingCash * passFloor,
        bonusNav: startingCash * (1 + bonusReturn),
        drawdownLimit,
        primarySymbol: primary
    };
};

const formatPct = (v) => `${(v * 100).toFixed(2)}%`;

const buildMarketUpdate = ({ ticks, tickIndex, symbols, lookback = 5 }) => {
    const current = ticks[tickIndex];
    const prev = tickIndex > 0 ? ticks[tickIndex - 1] : null;
    const lines = [];

    for (const sym of symbols) {
        const c = current?.bars?.[sym]?.close;
        if (!Number.isFinite(c)) continue;

        const p = prev?.bars?.[sym]?.close;
        const pct = Number.isFinite(p) ? (c - p) / p : null;

        const lbIdx = tickIndex - lookback;
        const lbClose = lbIdx >= 0 ? ticks[lbIdx]?.bars?.[sym]?.close : null;
        const momentum = Number.isFinite(lbClose) ? (c - lbClose) / lbClose : null;

        const parts = [];
        parts.push(`${sym}: $${c.toFixed(2)}`);
        if (pct != null) parts.push(`Δ ${formatPct(pct)}`);
        if (momentum != null) parts.push(`${lookback}d ${formatPct(momentum)}`);

        lines.push(parts.join(" | "));
    }

    return lines;
};

const makeLogEntry = (msg, type = 'normal') => ({ msg, type, id: Date.now() + Math.random() });

const makeIntroLogs = () => ([
    makeLogEntry("Welcome! You’re the trader in a replay of real market data.", "system"),
    makeLogEntry("Your score is called NAV: NAV = Cash + (Shares × Price).", "info"),
    makeLogEntry("PASS means you finished the level safely. BONUS means you finished extra well.", "info"),
    makeLogEntry("Peak NAV = your best score so far. Max DD = biggest drop from your best score.", "info"),
    makeLogEntry("On each turn: Δ is change since last turn. 5d is change over the last 5 turns.", "info"),
    makeLogEntry("A +% means up, a -% means down. No spoilers — you only see what’s happened so far.", "info"),
    makeLogEntry("Commands: BUY [qty] [SYMBOL], SELL [qty] [SYMBOL], HOLD", "info")
]);

const computeMaxDrawdownFromCloses = (closes) => {
    let peak = -Infinity;
    let maxDd = 0;
    for (const c of closes) {
        if (!Number.isFinite(c)) continue;
        peak = Math.max(peak, c);
        if (peak > 0) maxDd = Math.max(maxDd, (peak - c) / peak);
    }
    return maxDd;
};

const scoreScenarioDifficulty = ({ ticks, symbols, duration }) => {
    const primary = symbols[0];
    const closes = [];
    for (let i = 0; i < Math.min(duration, ticks.length); i++) {
        const c = ticks[i]?.bars?.[primary]?.close;
        if (Number.isFinite(c)) closes.push(c);
    }
    if (closes.length < 3) return 1e9;

    const returns = [];
    for (let i = 1; i < closes.length; i++) returns.push((closes[i] - closes[i - 1]) / closes[i - 1]);

    const vol = stdev(returns);
    const maxDd = computeMaxDrawdownFromCloses(closes);

    // Higher vol + bigger drawdowns = harder. Small nudge for multi-symbol datasets.
    return (vol * 120) + (maxDd * 8) + (Math.max(0, symbols.length - 1) * 0.05);
};

const difficultyStars = (rank01) => {
    if (!Number.isFinite(rank01)) return 1;
    return clamp(1, 5, Math.round(1 + rank01 * 4));
};

const buildCoachTip = ({ ticks, tickIndex, primarySymbol, lookback = 5 }) => {
    const now = ticks[tickIndex]?.bars?.[primarySymbol]?.close;
    const prev = tickIndex > 0 ? ticks[tickIndex - 1]?.bars?.[primarySymbol]?.close : null;
    const lbIdx = tickIndex - lookback;
    const lb = lbIdx >= 0 ? ticks[lbIdx]?.bars?.[primarySymbol]?.close : null;

    const one = Number.isFinite(now) && Number.isFinite(prev) ? (now - prev) / prev : null;
    const five = Number.isFinite(now) && Number.isFinite(lb) ? (now - lb) / lb : null;

    if (one != null && one > 0.01) return `Coach: ${primarySymbol} went up since last turn. That’s good info — but you still choose what to do next.`;
    if (one != null && one < -0.01) return `Coach: ${primarySymbol} went down since last turn. Staying calm and keeping some cash can help.`;
    if (five != null && five > 0.02) return `Coach: Over the last ${lookback} turns, ${primarySymbol} has been trending up so far.`;
    if (five != null && five < -0.02) return `Coach: Over the last ${lookback} turns, ${primarySymbol} has been trending down so far.`;
    return `Coach: Try to read the Δ and 5d numbers — they tell you what just happened.`;
};

function GamemasterSimulation() {
    const STARTING_CASH = 10000;

    const [scenarioFiles, setScenarioFiles] = useState([]);
    const [scenarioMeta, setScenarioMeta] = useState({}); // filename -> {difficultyStars, difficultyScore, symbols}
    const [levelIdx, setLevelIdx] = useState(0);
    const [levelScenario, setLevelScenario] = useState(null);
    const [highestUnlocked, setHighestUnlocked] = useState(0);
    const [totalStars, setTotalStars] = useState(0);
    const [stickers, setStickers] = useState(0);

    const [ticks, setTicks] = useState([]); // [{timestamp, bars:{SYM:{close,volume}}}]
    const [symbols, setSymbols] = useState([]);
    const [duration, setDuration] = useState(0);

    const [cash, setCash] = useState(STARTING_CASH);
    const [shares, setShares] = useState({});
    const [prices, setPrices] = useState({});
    const [tickIndex, setTickIndex] = useState(0); // 0-based into ticks

    const [objective, setObjective] = useState(null); // {passNav, bonusNav, drawdownLimit, primarySymbol}
    const [peakNav, setPeakNav] = useState(STARTING_CASH);
    const [maxDrawdown, setMaxDrawdown] = useState(0);
    const [runState, setRunState] = useState("loading"); // loading | ready | running | success | failed

    const [logs, setLogs] = useState(() => makeIntroLogs());
    const [inputValue, setInputValue] = useState('');
    const [showHelp, setShowHelp] = useState(true);
    const [levelFirstTradeSticker, setLevelFirstTradeSticker] = useState(false);
    const [levelNavUpSticker, setLevelNavUpSticker] = useState(false);

    const logsEndRef = useRef(null);

    const addLog = (msg, type = 'normal') => {
        setLogs(prev => [...prev, makeLogEntry(msg, type)]);
    };

    const loadLevel = async (idx, filesOverride = null) => {
        const files = filesOverride || scenarioFiles;
        const scenario = files[idx];
        if (!scenario) return;
        if (idx > highestUnlocked) {
            addLog("That level is locked. Finish the previous level to unlock it.", "error");
            return;
        }

        setRunState("loading");
        setLevelScenario(scenario);
        setTicks([]);
        setSymbols([]);
        setDuration(0);
        setTickIndex(0);
        setCash(STARTING_CASH);
        setShares({});
        setPrices({});
        setPeakNav(STARTING_CASH);
        setMaxDrawdown(0);
        setObjective(null);
        setLevelFirstTradeSticker(false);
        setLevelNavUpSticker(false);
        setLogs([
            ...makeIntroLogs(),
            makeLogEntry(`--- LEVEL ${idx + 1}/${files.length}: ${scenario} ---`, "system"),
            makeLogEntry(`Fetching market data...`, "info")
        ]);

        try {
            const res = await fetch(`${MARKET_DATA_URL}?scenario=${encodeURIComponent(scenario)}`);
            const data = await res.json();
            if (data?.error) {
                setRunState("failed");
                addLog(`ERROR: ${data.error}`, "error");
                return;
            }

            const { ticks: parsedTicks, symbols: parsedSymbols } = parseScenarioToTicks(data?.data || []);
            if (parsedTicks.length < 2 || parsedSymbols.length === 0) {
                setRunState("failed");
                addLog(`Dataset ${scenario} has insufficient rows to play.`, "error");
                return;
            }

            const levelDuration = Math.min(60, parsedTicks.length);
            const initTick = parsedTicks[0];
            const diffFactor = files.length > 1 ? idx / (files.length - 1) : 0;

            const initShares = {};
            const initPrices = {};
            for (const sym of parsedSymbols) {
                initShares[sym] = 0;
                const close = initTick?.bars?.[sym]?.close;
                initPrices[sym] = Number.isFinite(close) ? close : 0;
            }

            const obj = computeLevelObjective({
                ticks: parsedTicks,
                symbols: parsedSymbols,
                duration: levelDuration,
                startingCash: STARTING_CASH,
                difficultyFactor: diffFactor
            });

            setTicks(parsedTicks);
            setSymbols(parsedSymbols);
            setDuration(levelDuration);
            setShares(initShares);
            setPrices(initPrices);
            setObjective(obj);
            setRunState("running");

            addLog(`Level loaded: ${parsedSymbols.join(", ")} | ${levelDuration} turns`, "system");
            addLog(`Objective: PASS NAV ≥ $${obj.passNav.toFixed(2)} | BONUS NAV ≥ $${obj.bonusNav.toFixed(2)} | Max DD ≤ ${(obj.drawdownLimit * 100).toFixed(1)}%`, "goal");
            addLog(`TURN 1/${levelDuration} — ${initTick.timestamp}`, "system");
            for (const line of buildMarketUpdate({ ticks: parsedTicks, tickIndex: 0, symbols: parsedSymbols })) {
                addLog(`Market: ${line}`, "news");
            }
            addLog(buildCoachTip({ ticks: parsedTicks, tickIndex: 0, primarySymbol: obj.primarySymbol }), "info");
        } catch (e) {
            console.error(e);
            setRunState("failed");
            addLog(`Network Error: could not fetch ${scenario}.`, "error");
        }
    };

    const fetchScenarioFiles = async () => {
        try {
            const res = await fetch(SCENARIOS_URL);
            const data = await res.json();
            const files = Array.isArray(data?.scenarios) ? data.scenarios.slice() : [];

            if (files.length === 0) {
                setRunState("failed");
                addLog("No datasets found from backend. Is the Django API running?", "error");
                return;
            }

            const scored = await Promise.all(files.map(async (fname) => {
                try {
                    const r = await fetch(`${MARKET_DATA_URL}?scenario=${encodeURIComponent(fname)}`);
                    const j = await r.json();
                    const { ticks: t, symbols: syms } = parseScenarioToTicks(j?.data || []);
                    const dur = Math.min(80, t.length);
                    const score = scoreScenarioDifficulty({ ticks: t, symbols: syms, duration: dur });
                    return { fname, score, symbols: syms };
                } catch {
                    return { fname, score: 1e9, symbols: [] };
                }
            }));

            scored.sort((a, b) => a.score - b.score);
            const ordered = scored.map(s => s.fname);

            const meta = {};
            const denom = Math.max(1, ordered.length - 1);
            for (let i = 0; i < scored.length; i++) {
                const rank01 = i / denom;
                meta[scored[i].fname] = {
                    difficultyScore: scored[i].score,
                    difficultyStars: difficultyStars(rank01),
                    symbols: scored[i].symbols
                };
            }

            setScenarioFiles(ordered);
            setScenarioMeta(meta);
            setHighestUnlocked(0);

            setLevelIdx(0);
            await loadLevel(0, ordered);
        } catch (e) {
            console.error(e);
            setRunState("failed");
            addLog("Failed to load datasets from backend. Make sure the Django API is running on port 8003.", "error");
        }
    };

    useEffect(() => {
        const t = setTimeout(() => {
            fetchScenarioFiles();
        }, 0);
        return () => clearTimeout(t);
    }, []);

    useEffect(() => {
        logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [logs]);

    const computeNav = (cashValue, sharesObj, pricesObj) => {
        let total = cashValue;
        for (const sym of Object.keys(sharesObj)) {
            total += (sharesObj[sym] || 0) * (pricesObj[sym] || 0);
        }
        return total;
    };

    const advanceTurn = ({ nextCash, nextShares }) => {
        if (runState !== "running") return;
        if (!ticks.length || duration <= 0) return;

        const nextIndex = tickIndex + 1;
        if (nextIndex >= duration) return;

        const nextTick = ticks[nextIndex];
        const nextPrices = { ...prices };
        for (const sym of symbols) {
            const close = nextTick?.bars?.[sym]?.close;
            if (Number.isFinite(close)) nextPrices[sym] = close;
        }

        const nav = computeNav(nextCash, nextShares, nextPrices);
        const nextPeak = Math.max(peakNav, nav);
        const dd = nextPeak > 0 ? (nextPeak - nav) / nextPeak : 0;
        const nextMaxDd = Math.max(maxDrawdown, dd);

        setCash(nextCash);
        setShares(nextShares);
        setPrices(nextPrices);
        setTickIndex(nextIndex);
        setPeakNav(nextPeak);
        setMaxDrawdown(nextMaxDd);

        const humanTurn = nextIndex + 1;
        addLog(`TURN ${humanTurn}/${duration} — ${nextTick.timestamp}`, "system");
        for (const line of buildMarketUpdate({ ticks, tickIndex: nextIndex, symbols })) {
            addLog(`Market: ${line}`, "news");
        }
        if (objective?.primarySymbol) {
            addLog(buildCoachTip({ ticks, tickIndex: nextIndex, primarySymbol: objective.primarySymbol }), "info");
        }

        if (!levelNavUpSticker && nav > STARTING_CASH) {
            setLevelNavUpSticker(true);
            setStickers(prev => prev + 1);
            addLog("Sticker earned: You went above your starting score (+1)", "success");
        }

        // End-of-level check (only when we land on the final tick)
        if (humanTurn === duration) {
            const passedNav = objective ? nav >= objective.passNav : true;
            const passedDd = objective ? nextMaxDd <= objective.drawdownLimit : true;
            const earnedBonus = objective ? nav >= objective.bonusNav : false;

            if (passedNav && passedDd) {
                setRunState("success");
                setTotalStars(prev => prev + (earnedBonus ? 2 : 1));
                setHighestUnlocked(prev => Math.max(prev, levelIdx + 1));
                addLog(`LEVEL COMPLETE: ${levelScenario}`, "success");
                addLog(`Final NAV: $${nav.toFixed(2)} | Max drawdown: ${(nextMaxDd * 100).toFixed(2)}%${earnedBonus ? " | BONUS achieved" : ""}`, "success");
                addLog(earnedBonus ? "You earned 2 stars for this level." : "You earned 1 star for this level.", "success");
                if (earnedBonus) {
                    setStickers(prev => prev + 1);
                    addLog("Sticker earned: BONUS finish (+1)", "success");
                }
                if (levelIdx + 1 < scenarioFiles.length) addLog("Next level unlocked!", "success");
            } else {
                setRunState("failed");
                addLog(`LEVEL FAILED: ${levelScenario}`, "error");
                addLog(`Final NAV: $${nav.toFixed(2)} (pass $${objective?.passNav?.toFixed(2)})`, "error");
                addLog(`Max drawdown: ${(nextMaxDd * 100).toFixed(2)}% (limit ${(objective?.drawdownLimit * 100).toFixed(1)}%)`, "error");
            }
        }
    };

    const tryNextLevel = async () => {
        if (runState !== "success") {
            addLog("Finish this level first to unlock the next one.", "error");
            return;
        }
        const next = levelIdx + 1;
        if (next >= scenarioFiles.length) {
            addLog("All datasets completed.", "success");
            return;
        }
        if (next > highestUnlocked) {
            addLog("That level is still locked. Complete the current level first.", "error");
            return;
        }
        setLevelIdx(next);
        await loadLevel(next);
    };

    const retryLevel = async () => {
        await loadLevel(levelIdx);
    };

    const handleCommand = (e) => {
        e.preventDefault();
        const cmdStr = inputValue.trim().toUpperCase();
        setInputValue('');

        if (!cmdStr) return;
        if (runState !== "running") {
            addLog("Game is not running. Use Retry/Next to continue.", "error");
            return;
        }
        if (!symbols.length) {
            addLog("No symbols loaded for this dataset.", "error");
            return;
        }
        if (tickIndex >= duration - 1) {
            addLog("End of dataset window reached. No more turns left.", "error");
            return;
        }

        addLog(`> ${cmdStr}`, 'command');

        if (cmdStr === 'HOLD') {
            addLog('Action: HOLD', 'normal');
            advanceTurn({ nextCash: cash, nextShares: shares });
            return;
        }

        const parts = cmdStr.split(' ');
        if (parts.length !== 3 || (parts[0] !== 'BUY' && parts[0] !== 'SELL')) {
            addLog('Invalid command. Use: BUY [qty] [SYMBOL], SELL [qty] [SYMBOL], or HOLD', 'error');
            return;
        }

        const action = parts[0];
        const qty = parseInt(parts[1]);
        const sym = parts[2];

        if (isNaN(qty) || qty <= 0 || !symbols.includes(sym)) {
            addLog('Invalid quantity or symbol.', 'error');
            return;
        }

        const price = prices[sym];
        if (!Number.isFinite(price) || price <= 0) {
            addLog(`No valid price for ${sym} on this tick.`, 'error');
            return;
        }
        const cost = price * qty;
        const nextShares = { ...shares };
        let nextCash = cash;

        if (action === 'BUY') {
            if (nextCash < cost) {
                addLog(`Insufficient funds. Need $${cost.toFixed(2)}`, 'error');
            } else {
                nextCash = nextCash - cost;
                nextShares[sym] = (nextShares[sym] || 0) + qty;
                addLog(`Bought ${qty} ${sym} for $${cost.toFixed(2)}`);
                if (!levelFirstTradeSticker) {
                    setLevelFirstTradeSticker(true);
                    setStickers(prev => prev + 1);
                    addLog("Sticker earned: First trade (+1)", "success");
                }
                advanceTurn({ nextCash, nextShares });
            }
        } else if (action === 'SELL') {
            if ((nextShares[sym] || 0) < qty) {
                addLog(`Insufficient shares. You only have ${nextShares[sym] || 0}.`, 'error');
            } else {
                nextCash = nextCash + cost;
                nextShares[sym] = (nextShares[sym] || 0) - qty;
                addLog(`Sold ${qty} ${sym} for $${cost.toFixed(2)}`);
                if (!levelFirstTradeSticker) {
                    setLevelFirstTradeSticker(true);
                    setStickers(prev => prev + 1);
                    addLog("Sticker earned: First trade (+1)", "success");
                }
                advanceTurn({ nextCash, nextShares });
            }
        }
    };

    const totalValue = computeNav(cash, shares, prices);
    const levelLabel = levelScenario ? `${levelIdx + 1} - ${levelScenario}` : "Loading...";

    return (
        <div className="flex flex-col bg-slate-900 border border-slate-700 rounded-xl overflow-hidden h-full shadow-2xl font-mono text-sm max-h-[800px]">

            <div className="bg-slate-800 p-4 border-b border-slate-700 flex justify-between items-center text-teal-400">
                <h2 className="font-bold text-lg tracking-widest">&gt;&gt; GAME_MASTER_OS_v1.0</h2>
                <span className="text-slate-400">TURN [{Math.min(tickIndex + 1, Math.max(duration, 1))}/{Math.max(duration, 1)}]</span>
            </div>

            {/* Main Terminal Area */}
            <div className="flex flex-1 overflow-hidden">

                {/* Dashboard sidebar */}
                <div className="w-1/3 bg-slate-950 p-4 border-r border-slate-800 flex flex-col gap-6 overflow-y-auto">

                    <div>
                        <div className="flex items-center justify-between">
                            <h3 className="text-slate-500 mb-2 underline decoration-slate-700">HELP</h3>
                            <button
                                type="button"
                                onClick={() => setShowHelp(v => !v)}
                                className="text-xs px-2 py-1 rounded border border-slate-700 text-slate-400 hover:text-slate-200 hover:border-slate-500"
                            >
                                {showHelp ? "Hide" : "Show"}
                            </button>
                        </div>
                        {showHelp && (
                            <div className="text-slate-300 text-xs space-y-2">
                                <div>
                                    <span className="text-slate-400">NAV (score):</span> Cash + (Shares × Price)
                                </div>
                                <div>
                                    <span className="text-slate-400">PASS:</span> hit the safe score by the end
                                </div>
                                <div>
                                    <span className="text-slate-400">BONUS:</span> hit the extra-good score by the end
                                </div>
                                <div>
                                    <span className="text-slate-400">Peak NAV:</span> best score you’ve had
                                </div>
                                <div>
                                    <span className="text-slate-400">Max DD:</span> biggest drop from your best score
                                </div>
                                <div>
                                    <span className="text-slate-400">Market line:</span> <span className="text-slate-200">Δ</span> = since last turn, <span className="text-slate-200">5d</span> = last 5 turns
                                </div>
                                <div className="text-slate-400">
                                    +% is up, -% is down. You only learn from past/current turns.
                                </div>
                            </div>
                        )}
                    </div>

                    <div>
                        <h3 className="text-slate-500 mb-2 underline decoration-slate-700">PROFILE</h3>
                        <div className="text-white">Level: <span className="text-amber-400 font-bold">{levelLabel}</span></div>
                        <div className="text-emerald-400 font-bold mt-1 text-lg">Total Value: ${totalValue.toFixed(2)}</div>
                        <div className="text-slate-300">Cash: ${cash.toFixed(2)}</div>
                        <div className="text-slate-300">Stars: {totalStars}</div>
                        <div className="text-slate-300">Stickers: {stickers}</div>
                        <div className="text-slate-400 text-xs mt-2">Peak NAV: ${peakNav.toFixed(2)} | Max DD: {(maxDrawdown * 100).toFixed(2)}%</div>
                    </div>

                    <div>
                        <h3 className="text-slate-500 mb-2 underline decoration-slate-700">PORTFOLIO</h3>
                        {symbols.map(sym => (
                            <div key={sym} className="flex justify-between text-slate-300">
                                <span>{sym}:</span>
                                <span>{shares[sym] || 0} shrs @ <span className="text-blue-400">${Number.isFinite(prices[sym]) ? prices[sym].toFixed(2) : "—"}</span></span>
                            </div>
                        ))}
                    </div>

                    <div>
                        <h3 className="text-slate-500 mb-2 underline decoration-slate-700">MISSION</h3>
                        <div className="text-purple-400 italic font-sans text-xs">
                            {objective
                                ? `PASS: NAV ≥ $${objective.passNav.toFixed(2)} | BONUS: NAV ≥ $${objective.bonusNav.toFixed(2)} | Max DD ≤ ${(objective.drawdownLimit * 100).toFixed(1)}%.`
                                : "Loading objective..."}
                        </div>
                        <div className="text-xs text-amber-500 mt-2">Progress: {Math.min(tickIndex + 1, Math.max(duration, 1))}/{Math.max(duration, 1)} turns</div>
                        {(runState === "failed" || runState === "success") && (
                            <div className="flex gap-2 mt-3">
                                <button
                                    type="button"
                                    onClick={retryLevel}
                                    className="flex-1 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-600 rounded-lg px-3 py-2 text-xs font-bold"
                                >
                                    Retry
                                </button>
                                {runState === "success" && levelIdx + 1 < scenarioFiles.length && (
                                    <button
                                        type="button"
                                        onClick={tryNextLevel}
                                        className="flex-1 bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 rounded-lg px-3 py-2 text-xs font-bold"
                                    >
                                        Next
                                    </button>
                                )}
                            </div>
                        )}
                    </div>

                    <div>
                        <h3 className="text-slate-500 mb-2 underline decoration-slate-700">LEVELS</h3>
                        <div className="flex flex-col gap-2">
                            {scenarioFiles.map((fname, i) => {
                                const locked = i > highestUnlocked;
                                const starsCount = scenarioMeta?.[fname]?.difficultyStars ?? 1;
                                const starsStr = "★".repeat(starsCount);
                                return (
                                <button
                                    key={fname}
                                    type="button"
                                    disabled={runState === "loading"}
                                    onClick={async () => {
                                        if (i === levelIdx) return;
                                        if (locked) {
                                            addLog("Locked. Beat the previous level to unlock this one.", "error");
                                            return;
                                        }
                                        setLevelIdx(i);
                                        await loadLevel(i);
                                    }}
                                    className={`text-left px-3 py-2 rounded-lg border text-xs transition-colors ${
                                        i === levelIdx
                                            ? "bg-slate-800 border-slate-600 text-amber-300"
                                            : locked
                                                ? "bg-slate-950 border-slate-900 text-slate-600"
                                                : "bg-slate-950 border-slate-800 text-slate-300 hover:bg-slate-900"
                                    } ${runState === "loading" ? "opacity-50 cursor-not-allowed" : ""}`}
                                    title={fname}
                                >
                                    <div className="flex items-center justify-between gap-2">
                                        <span>{i + 1}. {fname}{locked ? " [LOCKED]" : ""}</span>
                                        <span className="text-slate-500">{starsStr}</span>
                                    </div>
                                </button>
                                );
                            })}
                        </div>
                    </div>

                </div>

                {/* Console Log output */}
                <div className="w-2/3 p-4 bg-black overflow-y-auto flex flex-col gap-1">
                    {logs.map(log => {
                        let colorClass = "text-slate-300";
                        if (log.type === 'system') colorClass = "text-blue-500 font-bold";
                        if (log.type === 'news') colorClass = "text-amber-300 italic";
                        if (log.type === 'error') colorClass = "text-red-500";
                        if (log.type === 'success') colorClass = "text-emerald-500 font-bold";
                        if (log.type === 'goal') colorClass = "text-purple-400";
                        if (log.type === 'command') colorClass = "text-white opacity-50";
                        if (log.type === 'info') colorClass = "text-slate-400";

                        return <div key={log.id} className={colorClass}>{log.msg}</div>;
                    })}
                    <div ref={logsEndRef} />
                </div>
            </div>

            {/* Input row */}
            <form onSubmit={handleCommand} className="bg-slate-900 border-t border-slate-700 p-3 flex">
                <span className="text-emerald-500 font-bold px-2 py-2">&gt;</span>
                <input
                    type="text"
                    value={inputValue}
                    onChange={e => setInputValue(e.target.value)}
                    placeholder={symbols.length ? `BUY 5 ${symbols[0]} | SELL 2 ${symbols[0]} | HOLD` : "BUY 5 SYMBOL | SELL 2 SYMBOL | HOLD"}
                    className="flex-1 bg-transparent text-white outline-none focus:ring-0 placeholder-slate-700 border-none px-2"
                    autoFocus
                    disabled={runState !== "running"}
                />
                <button type="submit" className="hidden">Send</button>
            </form>

        </div>
    );
}

export default GamemasterSimulation;
