import { useState, useEffect } from "react";
import { fetchStocks, fetchWallet, fetchHistory, fetchPending, cancelOrder, fetchHoldings } from "./api";

// Utility function 
// converts a raw number into Indian-locale currency string (1234567.8  →  "₹12,34,567.80")
const fmt = (n) =>
  `₹${Number(n).toLocaleString("en-IN", { minimumFractionDigits: 2 })}`;


// -----------------------------------------------------
// COMPONENT 1: MarketStatus
// Shows a live clock in IST and a green/red dot indicating whether NSE is currently open.
function MarketStatus() {

  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000); // every second update time 
    return () => clearInterval(t); // clear when the component unmounts to prevent memory leaks
  },
    []);  // [] = run only once when the component first mounts

  // Convert the current UTC time to IST (UTC +5:30)
  const ist = new Date(
    time.toLocaleString("en-US", { timeZone: "Asia/Kolkata" })
  );

  // check if market is open 
  const h = ist.getHours();
  const m = ist.getMinutes();
  const day = ist.getDay();
  const open =
    day >= 1 && day <= 5 &&
    (h > 9 || (h === 9 && m >= 15)) &&
    (h < 15 || (h === 15 && m <= 30));


  return (
    <div className="flex items-center gap-2">
      {/* Pulsing dot — green when open, red when closed */}
      <span className={`w-2 h-2 rounded-full animate-pulse ${open ? "bg-emerald-400" : "bg-red-400"}`} />

      {/* "NSE OPEN" or "NSE CLOSED" label */}
      <span className={`text-xs font-mono font-semibold tracking-widest ${open ? "text-emerald-400" : "text-red-400"}`}>
        NSE {open ? "OPEN" : "CLOSED"}
      </span>

      {/* Live clock — e.g. "14:32:07 IST" */}
      <span className="text-xs font-mono text-slate-500">
        {ist.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false })} IST
      </span>
    </div>
  );
}

// -------------------------------------------------------
// COMPONENT 2: OrderForm - The main buy / sell panel.
function OrderForm({ stocks, wallet, holdings, selectedSymbol, onSuccess }) {

  const [side, setSide] = useState("BUY");                  // "BUY" | "SELL"
  const [tradeType, setTradeType] = useState("MARKET");     // "MARKET" | "LIMIT"
  const [symbol, setSymbol] = useState("");                 // selected ticker
  const [quantity, setQuantity] = useState("");             // number of shares
  const [limitPrice, setLimitPrice] = useState("");         // only used for LIMIT orders
  const [loading, setLoading] = useState(false);            // true while API call is in-flight
  const [result, setResult] = useState(null);               // feedback banner - ok /error
  const [confirming, setConfirming] = useState(false);      // true when placed order but not confirmed 
  const [expiresAt, setExpiresAt] = useState("");           // optional expiry time for limit orders
  const [idempotencyKey, setIdempotencyKey] = useState(() => crypto.randomUUID());

  // to check if the user owns any shares of a stock (for enabling/disabling options in the dropdown)
  const ownedSymbols = new Set(holdings.map(h => h.symbol));

  // find the full stock object matching the selected symbol
  const stock = stocks.find(s => s.symbol === symbol);

  // for market orders use the live price; for limit orders use the user's entered price
  const execPrice =
    tradeType === "LIMIT" && limitPrice
      ? parseFloat(limitPrice)
      : (stock?.current_price ?? 0);

  // total cost (BUY) or proceeds (SELL) for this order
  const estimate = execPrice * (parseInt(quantity) || 0);

  // does the wallet have enough cash?
  const canAfford = wallet.balance >= estimate;

  // When a stock card in the grid is clicked, selectedSymbol changes. This effect syncs the dropdown to match.
  useEffect(() => {
    if (selectedSymbol) setSymbol(selectedSymbol);
  }, [selectedSymbol]);

  // validates inputs → POSTs to backend → shows result
  const handleSubmit = async () => {
    if (!symbol)
      return setResult({ ok: false, msg: "Select a stock first" });

    if (!quantity || parseInt(quantity) <= 0)
      return setResult({ ok: false, msg: "Enter a valid quantity" });

    if (tradeType === "LIMIT" && (!limitPrice || parseFloat(limitPrice) <= 0))
      return setResult({ ok: false, msg: "Enter a valid limit price" });

    if (side === "BUY" && !canAfford)
      return setResult({
        ok: false,
        msg: `Need ${fmt(estimate)}, wallet has ${fmt(wallet.balance)}`,
      });

    setLoading(true);
    setResult(null);

    const url =
      side === "BUY"
        ? "http://127.0.0.1:8000/api/trading/buy/"
        : "http://127.0.0.1:8000/api/trading/sell/";

    // the request body includes symbol, quantity, and optionally limit_price and expires_at
    const body = {
      symbol,
      quantity: parseInt(quantity),
      idempotency_key: idempotencyKey,
      ...(tradeType === "LIMIT" && { limit_price: parseFloat(limitPrice) }),
      ...(tradeType === "LIMIT" && expiresAt && { expires_at: new Date(expiresAt).toISOString() }),
    };

    // place the order by calling the backend API
    try {
      const res = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Idempotency-Key": idempotencyKey,
          "Authorization": `Token ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify(body),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error);

      // confirmed order - show success message and reset form
      setResult({ ok: true, msg: data.message, status: data.order_status });
      setConfirming(false);
      setSymbol("");
      setQuantity("");
      setLimitPrice("");
      setExpiresAt("");
      setIdempotencyKey(crypto.randomUUID());
      if (onSuccess) onSuccess();
    }
    catch (e) {
      setResult({ ok: false, msg: e.message });
    }
    finally {
      setLoading(false);
    }
  };

  const inputCls = "w-full px-3 py-2.5 bg-slate-900/60 border border-slate-700/50 rounded-lg text-sm font-mono text-slate-200 outline-none focus:border-indigo-500 transition-colors";
  const accentInputCls = "w-full px-3 py-2.5 bg-slate-900/60 border border-indigo-500/40 rounded-lg text-sm font-mono text-indigo-300 outline-none focus:border-indigo-500 transition-colors";

  return (
    <div className="rounded-2xl bg-slate-800/50 border border-slate-700/50 backdrop-blur-sm overflow-hidden">

      {/* Header: shows the form title and available cash in wallet*/}
      <div className="px-5 py-4 border-b border-slate-700/50 flex justify-between items-center">
        <span className="text-xs font-mono font-semibold tracking-widest text-indigo-400">ORDER ENTRY</span>
        <span className="text-xs font-mono text-slate-500">
          AVAIL <span className="text-indigo-400 font-semibold">{fmt(wallet.balance)}</span>
        </span>
      </div>

      <div className="p-5 space-y-4">
        {/* BUY / SELL toggle */}
        <div className="grid grid-cols-2 rounded-xl overflow-hidden border border-slate-700/50">
          {["BUY", "SELL"].map(s => (
            <button key={s}
              onClick={() => { setSide(s); setResult(null); setConfirming(false); }}
              className={`py-2.5 text-xs font-mono font-bold tracking-widest transition-all duration-150 ${side === s
                ? s === "BUY" ? "bg-emerald-500 text-slate-900" : "bg-red-500 text-slate-900"
                : "bg-slate-900/50 text-slate-500 hover:text-slate-300"
                }`}
            >{s}</button>
          ))}
        </div>

        {/* MARKET / LIMIT toggle */}
        <div className="grid grid-cols-2 gap-2">
          {["MARKET", "LIMIT"].map(t => (
            <button key={t}
              onClick={() => { setTradeType(t); setResult(null); setConfirming(false); }}
              className={`py-2 text-xs font-mono tracking-widest rounded-lg border transition-all duration-150 ${tradeType === t
                ? "border-indigo-500 bg-indigo-500/10 text-indigo-400"
                : "border-slate-700/50 bg-slate-900/30 text-slate-500 hover:text-slate-300"
                }`}
            >{t}</button>
          ))}
        </div>

        {/* Symbol dropdown */}
        <div>
          <label className="block text-xs font-mono tracking-widest text-slate-500 mb-2">SYMBOL</label>
          <select value={symbol}
            onChange={e => { setSymbol(e.target.value); setResult(null); setConfirming(false); }}
            className={inputCls + " cursor-pointer"}
          >
            <option value="">Select stock...</option>
            {stocks
              .filter(s => side === "BUY" || ownedSymbols.has(s.symbol))
              .map(s => (
                <option key={s.symbol} value={s.symbol}>
                  {s.symbol} — {fmt(s.current_price)}
                  {side === "SELL" && ` (own ${holdings.find(h => h.symbol === s.symbol)?.quantity})`}
                </option>
              ))}
          </select>
        </div>

        {/* Last Traded Price chip — only shows when a stock is selected */}
        {stock && (
          <div className="flex justify-between items-center px-3 py-2 bg-slate-900/40 rounded-lg border border-slate-700/30">
            <span className="text-xs font-mono text-slate-500">PRICE</span>
            <span className="text-sm font-mono font-bold text-slate-200">{fmt(stock.current_price)}</span>
          </div>
        )}

        {/* Quantity */}
        <div>
          <label className="block text-xs font-mono tracking-widest text-slate-500 mb-2">QUANTITY</label>
          <input type="number" min="1" value={quantity} placeholder="0"
            onChange={e => { setQuantity(e.target.value); setResult(null); setConfirming(false); }}
            className={inputCls}
          />
        </div>

        {/* Limit price input - only rendered when LIMIT order type is selected */}
        {tradeType === "LIMIT" && (
          <div>
            <label className="block text-xs font-mono tracking-widest text-indigo-400 mb-2">
              LIMIT PRICE —{" "}
              <span className="text-slate-500">
                {side === "BUY" ? "triggers when price ≤ this" : "triggers when price ≥ this"}
              </span>
            </label>
            <input type="number" min="0.01" step="0.01" value={limitPrice} placeholder="0.00"
              onChange={e => { setLimitPrice(e.target.value); setResult(null); setConfirming(false); }}
              className={accentInputCls}
            />
          </div>
        )}

        {/* Expiry at for limit orders */}
        {tradeType === "LIMIT" && (
          <div>
            <label className="block text-xs font-mono tracking-widest text-indigo-400 mb-2">
              EXPIRY — <span className="text-slate-500">optional</span>
            </label>
            <input type="datetime-local" value={expiresAt}
              onChange={e => { setExpiresAt(e.target.value); setConfirming(false); }}
              style={{ colorScheme: "dark" }}
              className={accentInputCls}
            />
          </div>
        )}

        {/* Estimated cost/proceeds summary*/}
        {estimate > 0 && (
          <div className="px-3 py-3 bg-slate-900/40 rounded-lg border border-slate-700/30 space-y-1.5">
            <div className="flex justify-between items-center">
              <span className="text-xs font-mono tracking-widest text-slate-500">EST. {side === "BUY" ? "COST" : "PROCEEDS"}</span>
              <span className="text-sm font-mono font-bold text-slate-200">{fmt(estimate)}</span>
            </div>

            {/* Wallet balance preview - only for BUY orders */}
            {side === "BUY" && (
              <div className="flex justify-between items-center">
                <span className="text-xs font-mono tracking-widest text-slate-500">WALLET AFTER</span>
                <span className={`text-xs font-mono ${canAfford ? "text-slate-500" : "text-red-400"}`}>
                  {fmt(wallet.balance - estimate)}
                </span>
              </div>
            )}
          </div>
        )}

        {/* Confirm banner */}
        {confirming && (
          <div className="px-4 py-3 rounded-xl bg-indigo-500/10 border border-indigo-500/30">
            <p className="text-xs font-mono tracking-widest text-slate-500 mb-1">CONFIRM ORDER</p>
            <p className="text-sm font-mono text-indigo-300">
              {side} {quantity} × {symbol} {tradeType === "LIMIT" ? `@ limit ₹${limitPrice}` : "at market price"}
            </p>
            {estimate > 0 && (
              <p className="text-xs font-mono text-slate-500 mt-1">
                Est. {side === "BUY" ? "cost" : "proceeds"}: {fmt(estimate)}
              </p>
            )}
          </div>
        )}

        {/* Submit button */}
        <button
          disabled={loading}
          onClick={() => {
            if (!confirming) {
              if (!symbol) return setResult({ ok: false, msg: "Select a stock first" });
              if (!quantity || parseInt(quantity) <= 0) return setResult({ ok: false, msg: "Enter a valid quantity" });
              if (tradeType === "LIMIT" && (!limitPrice || parseFloat(limitPrice) <= 0)) return setResult({ ok: false, msg: "Enter a valid limit price" });
              if (side === "BUY" && !canAfford) return setResult({ ok: false, msg: `Need ${fmt(estimate)}, wallet has ${fmt(wallet.balance)}` });
              if (tradeType === "LIMIT" && expiresAt && new Date(expiresAt) <= new Date()) return setResult({ ok: false, msg: "Expiry time must be in the future" });
              setResult(null);
              setConfirming(true);
            } else {
              handleSubmit();
            }
          }}
          className={`w-full py-3 rounded-xl text-xs font-mono font-bold tracking-widest transition-all duration-200 ${loading ? "bg-slate-700 text-slate-500 cursor-not-allowed"
            : confirming ? "bg-indigo-600 hover:bg-indigo-500 text-white"
              : side === "BUY" ? "bg-emerald-500 hover:bg-emerald-400 text-slate-900"
                : "bg-red-500 hover:bg-red-400 text-slate-900"
            }`}
        >
          {loading ? "PROCESSING..." : confirming ? `CONFIRM ${tradeType} ${side}` : `PLACE ${tradeType} ${side}`}
        </button>

        {/* Cancel confirm */}
        {confirming && (
          <button onClick={() => setConfirming(false)}
            className="w-full py-2 rounded-xl border border-slate-700/50 text-xs font-mono tracking-widest text-slate-500 hover:text-slate-300 transition-colors"
          >CANCEL</button>
        )}

        {/* Result banner */}
        {result && (
          <div className={`px-4 py-3 rounded-xl border text-xs font-mono ${result.ok
            ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
            : "bg-red-500/10 border-red-500/30 text-red-400"
            }`}>
            <p>{result.msg}</p>
            {result.status && <p className="mt-1 opacity-70 tracking-widest">STATUS: {result.status}</p>}
          </div>
        )}
      </div>
    </div>
  );
}


// --------------------------------------------------------------
// COMPONENT 3: StockTable - Full-page searchable, filterable table of all stocks.
function StockTable({ stocks, onSelect }) {
  const [search, setSearch] = useState("");     // text filter
  const [sector, setSector] = useState("ALL");  // sector dropdown filter

  // Build the unique sector list from all stocks, prepend "ALL"
  const sectors = ["ALL", ...new Set(stocks.map(s => s.sector))];

  // Apply both filters simultaneously
  const filtered = stocks.filter(s =>
    (sector === "ALL" || s.sector === sector) &&
    (s.symbol.includes(search.toUpperCase()) || s.company.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="rounded-2xl bg-slate-800/50 border border-slate-700/50 backdrop-blur-sm overflow-hidden">

      {/* Header + search/filter controls */}
      <div className="px-6 py-4 border-b border-slate-700/50">
        <div className="flex justify-between items-center mb-3">
          <span className="text-xs font-mono font-semibold tracking-widest text-indigo-400">MARKET — NSE</span>
          {/* Live count of visible rows */}
          <span className="text-xs font-mono text-slate-500">{filtered.length} stocks</span>
        </div>
        {/* Symbol / company search box */}
        <div className="flex gap-3">
          <input value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Search symbol or company..."
            className="flex-1 px-3 py-2 bg-slate-900/60 border border-slate-700/50 rounded-lg text-sm font-mono text-slate-200 outline-none focus:border-indigo-500 transition-colors placeholder-slate-600"
          />
          {/* Sector filter dropdown */}
          <select value={sector} onChange={e => setSector(e.target.value)}
            className="px-3 py-2 bg-slate-900/60 border border-slate-700/50 rounded-lg text-sm font-mono text-slate-400 outline-none focus:border-indigo-500 transition-colors cursor-pointer"
          >
            {sectors.map(s => <option key={s}>{s}</option>)}
          </select>
        </div>
      </div>

      {/* Data table */}
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b border-slate-700/50">
              {/* Column headers — last column ("") is for the TRADE button */}
              {["Symbol", "Company", "Sector", "Last Traded Price", "Change", ""].map((h, i) => (
                <th key={i} className={`px-4 py-3 text-xs font-mono tracking-widest text-slate-500 font-medium uppercase ${i < 2 ? "text-left" : "text-right"}`}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {/* Change in % of stocks */}
            {filtered.map((s, i) => {
              const chg = s.prev_close > 0
                ? (((s.current_price - s.prev_close) / s.prev_close) * 100).toFixed(2)
                : "0.00";
              const pos = parseFloat(chg) >= 0;
              return (
                <tr key={s.symbol}
                  className={`border-b border-slate-700/20 cursor-pointer transition-colors hover:bg-indigo-500/5 ${i % 2 === 0 ? "" : "bg-slate-900/20"}`}
                >
                  {/* Ticker symbol */}
                  <td className="px-4 py-3 text-sm font-mono font-bold text-indigo-400">{s.symbol}</td>
                  {/* Company full name */}
                  <td className="px-4 py-3 text-sm font-mono text-slate-400">{s.company}</td>
                  {/* Sector badge (pill-style) */}
                  <td className="px-4 py-3 text-right">
                    <span className="px-2 py-0.5 text-xs font-mono text-slate-500 bg-slate-900/60 rounded">{s.sector}</span>
                  </td>
                  {/* Last traded price */}
                  <td className="px-4 py-3 text-right text-sm font-mono font-semibold text-slate-200">{fmt(s.current_price)}</td>

                  {/* % change with arrow indicator */}
                  <td className={`px-4 py-3 text-right text-xs font-mono font-bold ${pos ? "text-emerald-400" : "text-red-400"}`}>
                    {pos ? "▲" : "▼"} {Math.abs(chg)}%
                  </td>

                  {/* TRADE button — calls onSelect which switches tab + pre-fills symbol */}
                  <td className="px-4 py-3 text-right">
                    <button onClick={() => onSelect && onSelect(s)}
                      className="px-3 py-1 text-xs font-mono tracking-widest text-slate-500 border border-slate-700/50 rounded hover:border-indigo-500 hover:text-indigo-400 transition-colors"
                    >TRADE</button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// -------------------------------------------------------------
// COMPONENT 4: TradeHistory
// Read-only table of all past executed trades.
function TradeHistory({ history }) {
  return (
    <div className="rounded-2xl bg-slate-800/50 border border-slate-700/50 backdrop-blur-sm overflow-hidden">

      {/* ── Header ── */}
      <div className="px-6 py-4 border-b border-slate-700/50 flex justify-between items-center">
        <span className="text-xs font-mono font-semibold tracking-widest text-indigo-400">TRADE HISTORY</span>
        <span className="text-xs font-mono text-slate-500">Last {history.length} trades</span>
      </div>

      {/* ── Trade History Data table ── */}
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b border-slate-700/50">
              {["Time", "Symbol", "Type", "Quantity", "Price", "Total Value", "Balance After", "Status"].map((h, i) => (
                <th key={h} className={`px-4 py-3 text-xs font-mono tracking-widest text-slate-500 font-medium uppercase ${i < 2 ? "text-left" : "text-right"}`}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {history.map((t, i) => (
              <tr key={t.order_id} className={`border-b border-slate-700/20 ${i % 2 === 0 ? "" : "bg-slate-900/20"}`}>
                {/* Formatted timestamp: "12 Mar, 14:32" */}
                <td className="px-4 py-3 text-xs font-mono text-slate-500">
                  <div>{new Date(t.time).toLocaleString("en-IN", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", hour12: false })}</div>
                  {t.is_limit && t.time && t.status !== "CANCELLED" && (
                    <div className="text-amber-400 mt-0.5">
                      exec {new Date(t.executed_at).toLocaleString("en-IN", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", hour12: false })}
                    </div>
                  )}
                </td>

                {/* Stock symbol */}
                <td className="px-4 py-3 text-sm font-mono font-bold text-slate-200">{t.symbol}</td>

                {/* BUY / SELL badge */}
                <td className="px-4 py-3 text-right">
                  <span className={`px-2 py-0.5 text-xs font-mono font-bold rounded ${t.type === "BUY" ? "bg-emerald-500/10 text-emerald-400" : "bg-red-500/10 text-red-400"
                    }`}>
                    {t.type}{t.is_limit ? " LIMIT" : ""}
                  </span>
                </td>

                {/* Quantity */}
                <td className="px-4 py-3 text-right text-sm font-mono text-slate-400">{t.quantity}</td>

                {/* Price per share, with optional limit price below */}
                <td className="px-4 py-3 text-right">
                  <div className="text-sm font-mono text-slate-200">{fmt(t.price)}</div>
                  {t.is_limit && t.limit_price && (
                    <div className="text-xs font-mono text-amber-400 mt-0.5">limit @ {fmt(t.limit_price)}</div>
                  )}
                </td>

                {/* Total value of the trade (quantity × price) */}
                <td className="px-4 py-3 text-right text-sm font-mono text-slate-400">{fmt(t.total_value)}</td>

                {/* Wallet balance after the trade was executed */}
                <td className="px-4 py-3 text-right text-sm font-mono text-indigo-400">{t.balance_after != null ? fmt(t.balance_after) : "—"}</td>

                {/* Status badge */}
                <td className="px-4 py-3 text-right">
                  <span className={`px-2 py-0.5 text-xs font-mono rounded ${t.status === "EXECUTED" ? "bg-emerald-500/10 text-emerald-400"
                    : t.status === "CANCELLED" ? "bg-slate-700/50 text-slate-500"
                      : t.status === "EXPIRED" ? "bg-orange-500/10 text-orange-400"
                        : "bg-amber-500/10 text-amber-400"
                    }`}>
                    {t.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}


// ----------------------------------------------------------------
// COMPONENT 5: TradingPage  (root / page component)
export default function TradingPage() {
  const [tab, setTab] = useState("trade");                          // active tab key
  const [stocks, setStocks] = useState([]);                         // all stocks from API
  const [history, setHistory] = useState([]);                       // executed trades
  const [wallet, setWallet] = useState({ balance: 0 });             // cash balance
  const [pending, setPending] = useState([]);                       // open limit orders
  const [loading, setLoading] = useState(true);                     // initial data loading flag
  const [selectedSymbol, setSelectedSymbol] = useState("");         // stock pre-selected for OrderForm
  const [holdings, setHoldings] = useState([]);                     // holdings of the user

  // Initial data load - Runs once on mount, fetch all parallely 
  useEffect(() => {
    Promise.all([
      fetchStocks(),
      fetchWallet(),
      fetchHistory(),
      fetchPending(),
      fetchHoldings(),
    ]).then(([stocks, wallet, history, pending, holdings]) => {
      setStocks(Array.isArray(stocks) ? stocks : []);
      setWallet({ balance: wallet.wallet_balance });
      setHistory(Array.isArray(history) ? history : (history.results ?? []));
      setPending(Array.isArray(pending) ? pending : []);
      setHoldings(Array.isArray(holdings) ? holdings : []);
    }).catch(err => console.error("initial load error:", err))
      .finally(() => setLoading(false));
  }, []);

  // Auto-refresh stock prices every 5 seconds 
  useEffect(() => {
    const interval = setInterval(() => {
      fetchStocks().then(data => setStocks(data)).catch(() => { });
      fetchPending().then(d => setPending(Array.isArray(d) ? d : [])).catch(() => { });
      fetchWallet().then(data => setWallet({ balance: data.wallet_balance })).catch(() => { });
      fetchHistory().then(data => setHistory(Array.isArray(data) ? data : [])).catch(() => { });
      fetchHoldings().then(data => setHoldings(Array.isArray(data) ? data : [])).catch(() => { });
    }, 5000);
    return () => clearInterval(interval);
  }, []);


  // After a successful order: refresh
  const handleOrderSuccess = () => {
    Promise.all([
      fetchWallet(),
      fetchHistory(),
      fetchPending(),
      fetchHoldings(),
    ]).then(([wallet, history, pending, holdings]) => {
      setWallet({ balance: wallet.wallet_balance });
      setHistory(Array.isArray(history) ? history : []);
      setPending(Array.isArray(pending) ? pending : []);
      setHoldings(Array.isArray(holdings) ? holdings : []);
    }).catch(() => { });
  };

  // Stock card / table row clicked -> switch to Trade tab 
  const handleSelectStock = (stock) => {
    setSelectedSymbol(stock.symbol);
    setTab("trade");
  };

  // Cancel a pending limit order
  const handleCancel = (orderId) => {
    cancelOrder(orderId)
      .then(() => {
        fetchPending().then(d => setPending(Array.isArray(d) ? d : []));
        fetchWallet().then(data => setWallet({ balance: data.wallet_balance })).catch(() => { });
        fetchHistory().then(data => setHistory(Array.isArray(data) ? data : [])).catch(() => { });
      })
      .catch(() => { });
  };


  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 text-white">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&display=swap');
        input[type=number]::-webkit-outer-spin-button,
        input[type=number]::-webkit-inner-spin-button { -webkit-appearance: none; }
        select option { background: #1e293b; color: #e2e8f0; }
      `}</style>

      {/* TOP NAVIGATION BAR: Left side:  Logo + market status indicator, 
       Right side: Wallet balance + user avatar */}
      <header className="border-b border-slate-700/50 bg-slate-900/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-screen-xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                <span className="text-xs font-bold text-white font-mono">V</span>
              </div>
              <span className="text-sm font-bold tracking-wide text-white font-mono">TRADING</span>
            </div>
            <div className="w-px h-5 bg-slate-700" />
            <MarketStatus />
          </div>

          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-xs font-mono tracking-widest text-slate-500">WALLET</p>
              <p className="text-sm font-mono font-bold text-indigo-400">{fmt(wallet.balance)}</p>
            </div>
            <div className="w-8 h-8 rounded-full bg-indigo-500/20 border border-indigo-500/40 flex items-center justify-center text-xs font-mono font-bold text-indigo-400">
              U
            </div>
          </div>
        </div>
      </header>

      {/* TAB BAR:: Trade | Market | History | Pending(n) */}
      <div className="border-b border-slate-700/50 bg-slate-900/60 backdrop-blur-sm">
        <div className="max-w-screen-xl mx-auto px-6 flex">
          {[
            { key: "trade", label: "Trade" },
            { key: "market", label: "Market" },
            { key: "history", label: "History" },
            { key: "pending", label: `Pending${pending.length > 0 ? ` (${pending.length})` : ""}` },
          ].map(t => (
            <button key={t.key} onClick={() => setTab(t.key)}
              className={`px-5 py-3.5 text-xs font-mono tracking-widest border-b-2 transition-all duration-150 ${tab === t.key
                ? "border-indigo-500 text-indigo-400"
                : "border-transparent text-slate-500 hover:text-slate-300"
                }`}
            >
              {t.label.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/*  Main Content Area */}
      <main className="max-w-screen-xl mx-auto px-6 py-6">

        {/* TAB: TRADE */}
        {tab === "trade" && (
          <div className="flex gap-5 items-start">
            <div className="w-80 shrink-0">
              <OrderForm stocks={stocks} wallet={wallet} holdings={holdings} selectedSymbol={selectedSymbol} onSuccess={handleOrderSuccess} />
            </div>

            {/* QUICK REFERENCE GRID */}
            <div className="flex-1 rounded-2xl bg-slate-800/50 border border-slate-700/50 backdrop-blur-sm overflow-hidden">
              <div className="px-5 py-4 border-b border-slate-700/50">
                <span className="text-xs font-mono font-semibold tracking-widest text-indigo-400">QUICK REFERENCE — click to trade</span>
              </div>
              <div className="grid gap-px bg-slate-700/20" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(190px, 1fr))" }}>
                {stocks.map(s => {
                  const chg = s.prev_close > 0
                    ? (((s.current_price - s.prev_close) / s.prev_close) * 100).toFixed(2)
                    : "0.00";
                  const pos = parseFloat(chg) >= 0;
                  return (
                    <div key={s.symbol} onClick={() => handleSelectStock(s)}
                      className="bg-slate-800/50 hover:bg-indigo-500/5 p-4 cursor-pointer transition-colors"
                    >
                      <div className="flex justify-between">
                        <div>
                          <p className="text-sm font-mono font-bold text-indigo-400">{s.symbol}</p>
                          <p className="text-xs font-mono text-slate-500 mt-0.5">{s.sector}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-mono font-semibold text-slate-200">{fmt(s.current_price)}</p>
                          <p className={`text-xs font-mono mt-0.5 ${pos ? "text-emerald-400" : "text-red-400"}`}>
                            {pos ? "▲" : "▼"} {Math.abs(chg)}%
                          </p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* TAB: MARKET */}
        {tab === "market" && <StockTable stocks={stocks} onSelect={handleSelectStock} />}

        {/* TAB: HISTORY */}
        {tab === "history" && <TradeHistory history={history} />}

        {/* TAB: PENDING */}
        {tab === "pending" && (
          <div className="rounded-2xl bg-slate-800/50 border border-slate-700/50 backdrop-blur-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-700/50 flex justify-between items-center">
              <span className="text-xs font-mono font-semibold tracking-widest text-indigo-400">PENDING LIMIT ORDERS</span>
              <span className="text-xs font-mono text-slate-500">{pending.length} waiting</span>
            </div>

            {/* Empty state message */}
            {pending.length === 0 ? (
              <div className="py-16 text-center text-sm font-mono text-slate-600">
                No pending orders — place a limit order to see it here
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="border-b border-slate-700/50">
                      {["Symbol", "Side", "Qty", "Limit Price", "Expires At", "Placed At", ""].map((h, i) => (
                        <th key={h} className={`px-4 py-3 text-xs font-mono tracking-widest text-slate-500 font-medium uppercase ${i < 2 ? "text-left" : "text-right"}`}>
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {pending.map((o, i) => (
                      <tr key={o.id} className={`border-b border-slate-700/20 ${i % 2 === 0 ? "" : "bg-slate-900/20"}`}>

                        {/* Stock ticker symbol */}
                        <td className="px-4 py-3 text-sm font-mono font-bold text-indigo-400">{o.stock}</td>

                        {/* BUY / SELL badge */}
                        <td className="px-4 py-3">
                          <span className={`px-2 py-0.5 text-xs font-mono font-bold rounded ${o.order_type === "BUY" ? "bg-emerald-500/10 text-emerald-400" : "bg-red-500/10 text-red-400"
                            }`}>
                            {o.order_type}
                          </span>
                        </td>

                        {/*Quantity*/}
                        <td className="px-4 py-3 text-right text-sm font-mono text-slate-400">{o.quantity}</td>

                        {/* The price at which this order will trigger */}
                        <td className="px-4 py-3 text-right text-sm font-mono text-slate-200">
                          ₹{Number(o.price_at_order).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                        </td>

                        {/* When the order was placed */}
                        <td className="px-4 py-3 text-right text-xs font-mono text-slate-500">
                          {o.expires_at
                            ? new Date(o.expires_at).toLocaleString("en-IN", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", hour12: false })
                            : <span className="text-slate-600">—</span>
                          }
                        </td>

                        {/* When the order will expire, if applicable */}
                        <td className="px-4 py-3 text-right text-xs font-mono text-slate-500">
                          {new Date(o.created_at).toLocaleString("en-IN", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", hour12: false })}
                        </td>

                        {/* CANCEL button — calls handleCancel then re-fetches pending list */}
                        <td className="px-4 py-3 text-right">
                          <button onClick={() => handleCancel(o.id)}
                            className="px-3 py-1 text-xs font-mono tracking-widest text-red-400 border border-red-500/30 bg-red-500/10 rounded hover:bg-red-500/20 transition-colors"
                          >CANCEL</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}