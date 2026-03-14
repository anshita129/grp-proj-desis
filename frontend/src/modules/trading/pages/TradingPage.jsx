import { useState, useEffect } from "react";
import { fetchStocks, fetchWallet, fetchHistory, fetchPending, cancelOrder, fetchHoldings } from "./api";

// ---------- UTILITY HELPERS ------------------
// converts a raw number into Indian-locale currency string (1234567.8  →  "₹12,34,567.80")
const fmt = (n) =>
  `₹${Number(n).toLocaleString("en-IN", { minimumFractionDigits: 2 })}`;

// a reusable style object for monospace font.
const mono = { fontFamily: "'IBM Plex Mono', monospace" };

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
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      {/* Pulsing dot — green when open, red when closed */}
      <div style={{
        width: 7, height: 7, borderRadius: "50%",
        background: open ? "#00d97e" : "#ff4757",
        boxShadow: `0 0 8px ${open ? "#00d97e88" : "#ff475788"}`,
        animation: "pulse 2s infinite",
      }} />

      {/* "NSE OPEN" or "NSE CLOSED" label */}
      <span style={{ ...mono, fontSize: 11, color: open ? "#00d97e" : "#ff4757", letterSpacing: "0.08em" }}>
        NSE {open ? "OPEN" : "CLOSED"}
      </span>

      {/* Live clock — e.g. "14:32:07 IST" */}
      <span style={{ ...mono, fontSize: 10, color: "#4a5568" }}>
        {ist.toLocaleTimeString("en-IN", {
          hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false,
        })} IST
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

  // inp(): returns a reusable style object for <input> / <select> fields.
  const inp = (accent = false) => ({
    width: "100%", padding: "9px 12px", background: "#08080f", border: `1px solid 
    ${accent ? "#4a9eff55" : "#111122"}`, color: accent ? "#4a9eff" : "#e2e8f0",
    ...mono,
    fontSize: 13, borderRadius: 3, outline: "none", boxSizing: "border-box",
  });

  return (
    <div style={{ background: "#0b0b18", border: "1px solid #111122", borderRadius: 6, overflow: "hidden" }}>

      {/* Header: shows the form title and available cash in wallet*/}
      <div style={{ padding: "14px 18px", borderBottom: "1px solid #111122", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ ...mono, fontSize: 10, color: "#4a9eff", letterSpacing: "0.12em" }}>
          ORDER ENTRY
        </span>
        <span style={{ ...mono, fontSize: 10, color: "#4a5568" }}>
          AVAIL <span style={{ color: "#4a9eff" }}>{fmt(wallet.balance)}</span>
        </span>
      </div>

      <div style={{ padding: 18 }}>

        {/* BUY / SELL toggle */}
        <div style={{ display: "flex", border: "1px solid #111122", borderRadius: 4, overflow: "hidden", marginBottom: 14 }}>
          {["BUY", "SELL"].map(s => (
            <button
              key={s}
              onClick={() => { setSide(s); setResult(null); setConfirming(false); }}
              style={{
                flex: 1,
                padding: "9px 0",
                border: "none",
                cursor: "pointer",
                ...mono, fontSize: 11, fontWeight: 700, letterSpacing: "0.1em",
                background: side === s ? (s === "BUY" ? "#00d97e" : "#ff4757") : "#08080f",
                color: side === s ? "#000" : "#4a5568",
                transition: "all 0.15s",
              }}
            >
              {s}
            </button>
          ))}
        </div>

        {/* MARKET / LIMIT toggle */}
        <div style={{ display: "flex", gap: 8, marginBottom: 14 }}>
          {["MARKET", "LIMIT"].map(t => (
            <button
              key={t}
              onClick={() => { setTradeType(t); setResult(null); setConfirming(false); }}
              style={{
                flex: 1,
                padding: "7px 0",
                border: `1px solid ${tradeType === t ? "#4a9eff" : "#111122"}`,
                cursor: "pointer",
                ...mono, fontSize: 10, letterSpacing: "0.08em",
                background: tradeType === t ? "#0d1b3e" : "#08080f",
                color: tradeType === t ? "#4a9eff" : "#4a5568",
                borderRadius: 3,
                transition: "all 0.15s",
              }}
            >
              {t}
            </button>
          ))}
        </div>

        {/* Symbol dropdown */}
        <div style={{ marginBottom: 12 }}>
          <div style={{ ...mono, fontSize: 9, color: "#4a5568", letterSpacing: "0.12em", marginBottom: 6 }}>
            SYMBOL
          </div>
          <select
            value={symbol}
            onChange={e => { setSymbol(e.target.value); setResult(null); setConfirming(false); }}
            style={{ ...inp(), cursor: "pointer" }}
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
          <div style={{
            background: "#08080f", border: "1px solid #111122", borderRadius: 3,
            padding: "6px 12px", marginBottom: 12,
            display: "flex", justifyContent: "space-between",
          }}>
            <span style={{ ...mono, fontSize: 10, color: "#4a5568" }}>Price</span>
            <span style={{ ...mono, fontSize: 13, color: "#e2e8f0", fontWeight: 700 }}>
              {fmt(stock.current_price)}
            </span>
          </div>
        )}

        {/* Quantity input */}
        <div style={{ marginBottom: 12 }}>
          <div style={{ ...mono, fontSize: 9, color: "#4a5568", letterSpacing: "0.12em", marginBottom: 6 }}>
            QUANTITY
          </div>
          <input
            type="number" min="1"
            value={quantity}
            onChange={e => { setQuantity(e.target.value); setResult(null); setConfirming(false); }}
            placeholder="0"
            style={inp()}
          />
        </div>

        {/* Limit price input - only rendered when LIMIT order type is selected */}
        {tradeType === "LIMIT" && (
          <div style={{ marginBottom: 12 }}>
            <div style={{ ...mono, fontSize: 9, color: "#4a9eff", letterSpacing: "0.12em", marginBottom: 6 }}>
              LIMIT PRICE - {" "}
              {side === "BUY"
                ? "order executes when price of stock ≤ entered price"
                : "order executes when price of stock ≥ entered price"}
            </div>
            <input
              type="number" min="0.01" step="0.01"
              value={limitPrice}
              onChange={e => { setLimitPrice(e.target.value); setResult(null); setConfirming(false); }}
              placeholder="0.00"
              style={inp(true)}
            />
          </div>
        )}

        {/* expires at for limit orders */}
        {tradeType === "LIMIT" && (
          <div style={{ marginBottom: 12 }}>
            <div style={{ ...mono, fontSize: 9, color: "#4a9eff", letterSpacing: "0.12em", marginBottom: 6 }}>
              EXPIRY - <span style={{ color: "#4a5568" }}>optional</span>
            </div>
            <input
              type="datetime-local"
              value={expiresAt}
              onChange={e => { setExpiresAt(e.target.value); setConfirming(false); }}
              style={{ ...inp(true), colorScheme: "dark" }}
            />
          </div>
        )}

        {/* Estimated cost / proceeds summary */}
        {estimate > 0 && (
          <div style={{
            background: "#08080f", border: "1px solid #111122", borderRadius: 3,
            padding: "8px 12px", marginBottom: 14,
          }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
              <span style={{ ...mono, fontSize: 9, color: "#4a5568", letterSpacing: "0.1em" }}>
                EST. {side === "BUY" ? "COST" : "PROCEEDS"}
              </span>
              <span style={{ ...mono, fontSize: 13, color: "#e2e8f0", fontWeight: 700 }}>
                {fmt(estimate)}
              </span>
            </div>

            {/* Wallet balance preview - only for BUY orders */}
            {side === "BUY" && (
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ ...mono, fontSize: 9, color: "#4a5568", letterSpacing: "0.1em" }}>
                  WALLET AFTER
                </span>
                <span style={{ ...mono, fontSize: 11, color: canAfford ? "#4a5568" : "#ff4757" }}>
                  {fmt(wallet.balance - estimate)}
                </span>
              </div>
            )}
          </div>
        )}

        {/* Confirm banner */}
        {confirming && (
          <div style={{
            marginBottom: 10, padding: "10px 12px", borderRadius: 3,
            background: "#0d1b3e", border: "1px solid #4a9eff44",
            ...mono, fontSize: 11, color: "#4a9eff",
          }}>
            <div style={{ marginBottom: 6, fontSize: 10, color: "#4a5568", letterSpacing: "0.1em" }}>CONFIRM ORDER</div>
            <div>{side} {quantity} × {symbol} {tradeType === "LIMIT" ? `@ limit ₹${limitPrice}` : "at market price"}</div>
            {estimate > 0 && (
              <div style={{ marginTop: 4, fontSize: 10, color: "#4a5568" }}>
                Est. {side === "BUY" ? "cost" : "proceeds"}: {fmt(estimate)}
              </div>
            )}
          </div>
        )}

        {/* Place order button - first click shows confirm banner, second click submits the order*/}
        <button
          onClick={() => {
            if (!confirming) {
              if (!symbol) return setResult({ ok: false, msg: "Select a stock first" });
              if (!quantity || parseInt(quantity) <= 0) return setResult({ ok: false, msg: "Enter a valid quantity" });
              if (tradeType === "LIMIT" && (!limitPrice || parseFloat(limitPrice) <= 0)) return setResult({ ok: false, msg: "Enter a valid limit price" });
              if (side === "BUY" && !canAfford) return setResult({ ok: false, msg: `Need ${fmt(estimate)}, wallet has ${fmt(wallet.balance)}` });
              if (tradeType === "LIMIT" && expiresAt && new Date(expiresAt) <= new Date()) {
                return setResult({ ok: false, msg: "Expiry time must be in the future" });
              }
              setResult(null);
              setConfirming(true);
            } else {
              handleSubmit();
            }
          }}
          disabled={loading}
          style={{
            width: "100%", padding: "11px 0", border: "none", borderRadius: 3,
            cursor: loading ? "not-allowed" : "pointer",
            background: loading ? "#111122" : confirming ? "#4a9eff" : side === "BUY" ? "#00d97e" : "#ff4757",
            color: loading ? "#4a5568" : confirming ? "#fff" : "#000",
            ...mono, fontSize: 11, fontWeight: 700, letterSpacing: "0.12em",
            transition: "all 0.2s", opacity: loading ? 0.7 : 1,
          }}
        >
          {loading ? "PROCESSING..." : confirming ? `CONFIRM ${tradeType} ${side}` : `PLACE ${tradeType} ${side}`}
        </button>

        {/* Cancel button - only shows when confirming an order */}
        {confirming && (
          <button
            onClick={() => setConfirming(false)}
            style={{
              width: "100%", marginTop: 6, padding: "7px 0",
              border: "1px solid #111122", borderRadius: 3, background: "none",
              color: "#4a5568", cursor: "pointer",
              ...mono, fontSize: 10, letterSpacing: "0.1em",
            }}
          > CANCEL
          </button>
        )}

        {/* Result banner - shows success or error message after placing an order */}
        {result && (
          <div style={{
            marginTop: 10, padding: "9px 12px", borderRadius: 3,
            ...mono, fontSize: 11,
            background: result.ok ? "#001a0d" : "#1a0008",
            border: `1px solid ${result.ok ? "#00d97e44" : "#ff475744"}`,
            color: result.ok ? "#00d97e" : "#ff4757",
          }}>
            <div>{result.msg}</div>
            {result.status && (
              <div style={{ fontSize: 9, marginTop: 4, opacity: 0.7, letterSpacing: "0.08em" }}>
                STATUS: {result.status}
              </div>
            )}
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
    <div style={{ background: "#0b0b18", border: "1px solid #111122", borderRadius: 6, overflow: "hidden" }}>

      {/* Header + search/filter controls */}
      <div style={{ padding: "14px 18px", borderBottom: "1px solid #111122" }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
          <span style={{ ...mono, fontSize: 10, color: "#4a9eff", letterSpacing: "0.12em" }}>
            MARKET — NSE
          </span>
          {/* Live count of visible rows */}
          <span style={{ ...mono, fontSize: 10, color: "#4a5568" }}>
            {filtered.length} stocks
          </span>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {/* Symbol / company search box */}
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search symbol or company..."
            style={{ flex: 1, padding: "7px 10px", background: "#08080f", border: "1px solid #111122", color: "#e2e8f0", ...mono, fontSize: 11, borderRadius: 3, outline: "none" }}
          />
          {/* Sector filter dropdown */}
          <select
            value={sector}
            onChange={e => setSector(e.target.value)}
            style={{ padding: "7px 10px", background: "#08080f", border: "1px solid #111122", color: "#a0aec0", ...mono, fontSize: 11, borderRadius: 3, outline: "none", cursor: "pointer" }}
          >
            {sectors.map(s => <option key={s}>{s}</option>)}
          </select>
        </div>
      </div>

      {/* Data table */}
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ borderBottom: "1px solid #111122" }}>
            {/* Column headers — last column ("") is for the TRADE button */}
            {["Symbol", "Company", "Sector", "Last Traded Price", "Change", ""].map((h, i) => (
              <th
                key={i}
                style={{
                  padding: "8px 16px",
                  textAlign: i < 2 ? "left" : "right",
                  ...mono, fontSize: 9, letterSpacing: "0.1em",
                  color: "#4a5568", textTransform: "uppercase", fontWeight: 500,
                }}
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {filtered.map((s, i) => {
            // chnage in % of stocks 
            const chg = s.prev_close > 0
              ? (((s.current_price - s.prev_close) / s.prev_close) * 100).toFixed(2)
              : "0.00";
            const pos = parseFloat(chg) >= 0;
            return (
              <tr
                key={s.symbol}
                style={{
                  borderBottom: "1px solid #0a0a14",
                  background: i % 2 === 0 ? "transparent" : "#080810",
                  cursor: "pointer",
                }}
                onMouseEnter={e => e.currentTarget.style.background = "#0d1b3e22"}
                onMouseLeave={e => e.currentTarget.style.background = i % 2 === 0 ? "transparent" : "#080810"}
              >
                {/* Ticker symbol */}
                <td style={{ padding: "11px 16px", ...mono, fontSize: 13, fontWeight: 700, color: "#4a9eff" }}>
                  {s.symbol}
                </td>

                {/* Company full name */}
                <td style={{ padding: "11px 16px", ...mono, fontSize: 11, color: "#a0aec0" }}>
                  {s.company}
                </td>

                {/* Sector badge (pill-style) */}
                <td style={{ padding: "11px 16px", textAlign: "right" }}>
                  <span style={{ ...mono, fontSize: 9, color: "#4a5568", background: "#08080f", padding: "2px 7px", borderRadius: 2 }}>
                    {s.sector}
                  </span>
                </td>

                {/* Last traded price */}
                <td style={{ padding: "11px 16px", textAlign: "right", ...mono, fontSize: 13, color: "#e2e8f0", fontWeight: 600 }}>
                  {fmt(s.current_price)}
                </td>

                {/* % change with arrow indicator */}
                <td style={{ padding: "11px 16px", textAlign: "right", ...mono, fontSize: 11, fontWeight: 700, color: pos ? "#00d97e" : "#ff4757" }}>
                  {pos ? "▲" : "▼"} {Math.abs(chg)}%
                </td>

                {/* TRADE button — calls onSelect which switches tab + pre-fills symbol */}
                <td style={{ padding: "11px 16px", textAlign: "right" }}>
                  <button
                    onClick={() => onSelect && onSelect(s)}
                    style={{
                      padding: "4px 10px", border: "1px solid #111122", borderRadius: 2,
                      background: "#08080f", color: "#4a5568", cursor: "pointer",
                      ...mono, fontSize: 9, letterSpacing: "0.08em", transition: "all 0.15s",
                    }}
                    onMouseEnter={e => { e.target.style.borderColor = "#4a9eff"; e.target.style.color = "#4a9eff"; }}
                    onMouseLeave={e => { e.target.style.borderColor = "#111122"; e.target.style.color = "#4a5568"; }}
                  >
                    TRADE
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}



// -------------------------------------------------------------
// COMPONENT 4: TradeHistory
// Read-only table of all past executed trades.
function TradeHistory({ history }) {
  return (
    <div style={{ background: "#0b0b18", border: "1px solid #111122", borderRadius: 6, overflow: "hidden" }}>

      {/* ── Header ── */}
      <div style={{ padding: "14px 18px", borderBottom: "1px solid #111122", display: "flex", justifyContent: "space-between" }}>
        <span style={{ ...mono, fontSize: 10, color: "#4a9eff", letterSpacing: "0.12em" }}>
          TRADE HISTORY
        </span>
        <span style={{ ...mono, fontSize: 10, color: "#4a5568" }}>
          Last {history.length} trades
        </span>
      </div>

      {/* ── Trade History Data table ── */}
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ borderBottom: "1px solid #111122" }}>
            {["Time", "Symbol", "Type", "Quantity", "Price", "Total Value", "Balance After", "Status"].map((h, i) => (
              <th
                key={h}
                style={{
                  padding: "8px 16px",
                  textAlign: i < 2 ? "left" : "right",
                  ...mono, fontSize: 9, letterSpacing: "0.1em",
                  color: "#4a5568", textTransform: "uppercase", fontWeight: 500,
                }}
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {history.map((t, i) => (
            <tr
              key={t.order_id}
              style={{ borderBottom: "1px solid #0a0a14", background: i % 2 === 0 ? "transparent" : "#080810" }}
            >
              {/* Formatted timestamp: "12 Mar, 14:32" */}
              <td style={{ padding: "10px 16px", ...mono, fontSize: 10, color: "#4a5568" }}>
                <div>{new Date(t.time).toLocaleString("en-IN", {
                  day: "numeric", month: "short",
                  hour: "2-digit", minute: "2-digit", hour12: false,
                })}</div>
                {t.is_limit && t.time && t.status !== "CANCELLED" && (
                  <div style={{ ...mono, fontSize: 9, color: "#f59e0b", marginTop: 3 }}>
                    exec {new Date(t.executed_at).toLocaleString("en-IN", {
                      day: "numeric", month: "short",
                      hour: "2-digit", minute: "2-digit", hour12: false,
                    })}
                  </div>
                )}
              </td>


              {/* Stock symbol */}
              <td style={{ padding: "10px 16px", ...mono, fontSize: 12, fontWeight: 700, color: "#e2e8f0" }}>
                {t.symbol}
              </td>

              {/* BUY / SELL badge */}
              <td style={{ padding: "10px 16px", textAlign: "right" }}>
                <span style={{
                  ...mono, fontSize: 10, fontWeight: 700, padding: "2px 7px", borderRadius: 2,
                  color: t.type === "BUY" ? "#00d97e" : "#ff4757",
                  background: t.type === "BUY" ? "#001a0d" : "#1a0008",
                }}>
                  {t.type}{t.is_limit ? " LIMIT" : ""}
                </span>
              </td>

              {/* Quantity */}
              <td style={{
                padding: "10px 16px", textAlign: "right",
                ...mono, fontSize: 12, color: "#a0aec0"
              }}>
                {t.quantity}
              </td>

              {/* Price per share, with optional limit price below */}
              <td style={{ padding: "10px 16px", textAlign: "right" }}>
                <div style={{ ...mono, fontSize: 12, color: "#e2e8f0" }}>{fmt(t.price)}</div>
                {t.is_limit && t.limit_price && (
                  <div style={{ ...mono, fontSize: 9, color: "#f59e0b", marginTop: 3 }}>
                    limit @ {fmt(t.limit_price)}
                  </div>
                )}
              </td>

              {/* Total value of the trade (quantity × price) */}
              <td style={{ padding: "10px 16px", textAlign: "right", ...mono, fontSize: 12, color: "#a0aec0" }}>{fmt(t.total_value)}</td>

              {/* Wallet balance after the trade was executed */}
              <td style={{
                padding: "10px 16px", textAlign: "right",
                ...mono, fontSize: 12, color: "#4a9eff"
              }}>
                {t.balance_after != null ? fmt(t.balance_after) : "—"}
              </td>

              {/* Status badge — green for EXECUTED, amber for anything else */}
              <td style={{ padding: "10px 16px", textAlign: "right" }}>
                <span style={{
                  ...mono, fontSize: 9, padding: "2px 7px", borderRadius: 2,
                  color: t.status === "EXECUTED" ? "#00d97e" : "#f59e0b",
                  background: t.status === "EXECUTED" ? "#001a0d" : "#1a0800",
                }}>
                  {t.status}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
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
    <div style={{ minHeight: "100vh", background: "#070710", color: "#e2e8f0" }}>

      {/* ── Global CSS injected via a <style> tag ── */}
      <style>{`
        /* Load IBM Plex Mono from Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&display=swap');

        /* Box-sizing reset — padding/border included in element width/height */
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        /* Thin, dark scrollbar for webkit browsers (Chrome, Edge, Safari) */
        ::-webkit-scrollbar { width: 4px; height: 4px; }
        ::-webkit-scrollbar-track { background: #050508; }
        ::-webkit-scrollbar-thumb { background: #111122; border-radius: 2px; }

        /* Remove spinner arrows on number inputs */
        input[type=number]::-webkit-outer-spin-button,
        input[type=number]::-webkit-inner-spin-button { -webkit-appearance: none; }

        /* Dark background for <select> option items */
        select option { background: #0b0b18; color: #e2e8f0; }

        /* Keyframe for the pulsing market-status dot */
        @keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.4; } }
      `}</style>

      {/* TOP NAVIGATION BAR: Left side:  Logo + market status indicator, 
       Right side: Wallet balance + user avatar */}
      <div style={{
        background: "#050508", borderBottom: "1px solid #111122",
        height: 50, display: "flex", alignItems: "center",
        justifyContent: "space-between", padding: "0 24px",
      }}>
        {/* Left group */}
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            {/* logo mark */}
            <div style={{
              width: 22, height: 22,
              background: "linear-gradient(135deg, #4a9eff, #0047cc)",
              borderRadius: 4, display: "flex", alignItems: "center", justifyContent: "center",
            }}>
              <span style={{ ...mono, fontSize: 11, fontWeight: 700, color: "#fff" }}>V</span>
            </div>
            <span style={{ ...mono, fontSize: 14, fontWeight: 700, color: "#e2e8f0", letterSpacing: "0.06em" }}>TRADING PAGE</span>
            <span style={{ ...mono, fontSize: 10, color: "#4a5568", letterSpacing: "0.14em" }}></span>
          </div>

          {/* Vertical divider */}
          <div style={{ width: 1, height: 20, background: "#111122", margin: "0 4px" }} />

          {/* Live NSE open/closed indicator + clock */}
          <MarketStatus />
        </div>

        {/* Right group */}
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          {/* Wallet balance display */}
          <div style={{ textAlign: "right" }}>
            <div style={{ ...mono, fontSize: 9, color: "#4a5568", letterSpacing: "0.1em" }}>WALLET</div>
            <div style={{ ...mono, fontSize: 13, fontWeight: 700, color: "#4a9eff" }}>{fmt(wallet.balance)}</div>
          </div>

          {/* User avatar */}
          <div style={{
            width: 30, height: 30, borderRadius: "50%",
            background: "#0d1b3e", border: "1px solid #1e3a6e",
            display: "flex", alignItems: "center", justifyContent: "center",
            ...mono, fontSize: 12, color: "#4a9eff", fontWeight: 700,
          }}>U</div>
        </div>
      </div>

      {/* TAB BAR:: Trade | Market | History | Pending(n) */}
      <div style={{
        background: "#050508", borderBottom: "1px solid #111122",
        padding: "0 24px", display: "flex",
      }}>
        {[
          { key: "trade", label: "Trade" },
          { key: "market", label: "Market" },
          { key: "history", label: "History" },
          { key: "pending", label: `Pending${pending.length > 0 ? ` (${pending.length})` : ""}` },
        ].map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            style={{
              padding: "11px 20px", border: "none", background: "none", cursor: "pointer",
              ...mono, fontSize: 11, letterSpacing: "0.1em",
              color: tab === t.key ? "#4a9eff" : "#4a5568",
              borderBottom: `2px solid ${tab === t.key ? "#4a9eff" : "transparent"}`,
              marginBottom: -1,
              transition: "all 0.15s",
            }}
          >
            {t.label.toUpperCase()}
          </button>
        ))}
      </div>

      {/* MAIN CONTENT AREA: maxWidth + auto margins = centred layout*/}
      <div style={{ padding: 24, maxWidth: 1300, margin: "0 auto" }}>

        {/* TAB: TRADE */}
        {tab === "trade" && (
          <div style={{ display: "flex", gap: 20, alignItems: "flex-start" }}>
            {/* ORDER FORM */}
            <div style={{ width: 320, flexShrink: 0 }}>
              <OrderForm
                stocks={stocks}
                wallet={wallet}
                holdings={holdings}
                selectedSymbol={selectedSymbol}
                onSuccess={handleOrderSuccess}
              />
            </div>

            {/* QUICK REFERENCE GRID */}
            <div style={{
              flex: 1, background: "#0b0b18",
              border: "1px solid #111122", borderRadius: 6, overflow: "hidden",
            }}>
              <div style={{ padding: "14px 18px", borderBottom: "1px solid #111122" }}>
                <span style={{ ...mono, fontSize: 10, color: "#4a9eff", letterSpacing: "0.12em" }}>
                  QUICK REFERENCE — click to trade
                </span>
              </div>

              {/* CSS grid: auto-fill columns of min 190px, 1px gap between cells */}
              <div style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fill, minmax(190px, 1fr))",
                gap: 1,
                background: "#111122",
              }}>
                {stocks.map((s, i) => {
                  const chg = s.prev_close > 0
                    ? (((s.current_price - s.prev_close) / s.prev_close) * 100).toFixed(2)
                    : "0.00";
                  const pos = parseFloat(chg) >= 0;
                  return (
                    <div
                      key={s.symbol}
                      onClick={() => handleSelectStock(s)} // pre-fills OrderForm + switches tab
                      style={{ background: "#0b0b18", padding: "14px 16px", cursor: "pointer", transition: "background 0.1s" }}
                      onMouseEnter={e => e.currentTarget.style.background = "#0d1b3e"}
                      onMouseLeave={e => e.currentTarget.style.background = "#0b0b18"}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <div>
                          <div style={{ ...mono, fontSize: 13, fontWeight: 700, color: "#4a9eff" }}>{s.symbol}</div>
                          <div style={{ ...mono, fontSize: 9, color: "#4a5568", marginTop: 2 }}>{s.sector}</div>
                        </div>
                        <div style={{ textAlign: "right" }}>
                          <div style={{ ...mono, fontSize: 12, color: "#e2e8f0", fontWeight: 600 }}>{fmt(s.current_price)}</div>
                          <div style={{ ...mono, fontSize: 10, color: pos ? "#00d97e" : "#ff4757", marginTop: 2 }}>
                            {pos ? "▲" : "▼"} {Math.abs(chg)}%
                          </div>
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
        {tab === "market" && (
          <StockTable stocks={stocks} onSelect={handleSelectStock} />
        )}

        {/* TAB: HISTORY */}
        {tab === "history" && (
          <TradeHistory history={history} />
        )}

        {/* TAB: PENDING */}
        {tab === "pending" && (
          <div style={{ background: "#0b0b18", border: "1px solid #111122", borderRadius: 6, overflow: "hidden" }}>
            <div style={{ padding: "14px 18px", borderBottom: "1px solid #111122", display: "flex", justifyContent: "space-between" }}>
              <span style={{ ...mono, fontSize: 10, color: "#4a9eff", letterSpacing: "0.12em" }}>
                PENDING LIMIT ORDERS
              </span>
              <span style={{ ...mono, fontSize: 10, color: "#4a5568" }}>
                {pending.length} waiting
              </span>
            </div>

            {/* Empty state message */}
            {pending.length === 0 ? (
              <div style={{ padding: 40, textAlign: "center", ...mono, fontSize: 12, color: "#4a5568" }}>
                No pending orders — place a limit order to see it here
              </div>
            ) : (
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid #111122" }}>
                    {["Symbol", "Side", "Qty", "Limit Price", "Expires At", "Placed At", ""].map((h, i) => (
                      <th
                        key={h}
                        style={{
                          padding: "8px 16px",
                          textAlign: i < 2 ? "left" : "right",
                          ...mono, fontSize: 9, letterSpacing: "0.1em",
                          color: "#4a5568", textTransform: "uppercase", fontWeight: 500,
                        }}
                      >
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {pending.map((o, i) => (
                    <tr
                      key={o.id}
                      style={{ borderBottom: "1px solid #0a0a14", background: i % 2 === 0 ? "transparent" : "#080810" }}
                    >
                      {/* Stock ticker symbol */}
                      <td style={{ padding: "11px 16px", ...mono, fontSize: 13, fontWeight: 700, color: "#4a9eff" }}>
                        {o.stock}
                      </td>

                      {/* BUY / SELL badge */}
                      <td style={{ padding: "11px 16px" }}>
                        <span style={{
                          ...mono, fontSize: 10, fontWeight: 700,
                          padding: "2px 7px", borderRadius: 2,
                          color: o.order_type === "BUY" ? "#00d97e" : "#ff4757",
                          background: o.order_type === "BUY" ? "#001a0d" : "#1a0008",
                        }}>
                          {o.order_type}
                        </span>
                      </td>

                      {/*Quantity*/}
                      <td style={{ padding: "11px 16px", textAlign: "right", ...mono, fontSize: 12, color: "#a0aec0" }}>
                        {o.quantity}
                      </td>

                      {/* The price at which this order will trigger */}
                      <td style={{ padding: "11px 16px", textAlign: "right", ...mono, fontSize: 12, color: "#e2e8f0" }}>
                        ₹{Number(o.price_at_order).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                      </td>

                      {/* When the order was placed */}
                      <td style={{ padding: "11px 16px", textAlign: "right", ...mono, fontSize: 10, color: "#4a5568" }}>
                        {new Date(o.created_at).toLocaleString("en-IN", {
                          day: "numeric", month: "short",
                          hour: "2-digit", minute: "2-digit", hour12: false,
                        })}
                      </td>

                      {/* When the order will expire, if applicable */}
                      <td style={{ padding: "11px 16px", textAlign: "right", ...mono, fontSize: 10, color: "#4a5568" }}>
                        {o.expires_at
                          ? new Date(o.expires_at).toLocaleString("en-IN", {
                            day: "numeric", month: "short",
                            hour: "2-digit", minute: "2-digit", hour12: false,
                          })
                          : <span style={{ color: "#4a5568" }}>—</span>
                        }
                      </td>

                      {/* CANCEL button — calls handleCancel then re-fetches pending list */}
                      <td style={{ padding: "11px 16px", textAlign: "right" }}>
                        <button
                          onClick={() => handleCancel(o.id)}
                          style={{
                            padding: "4px 10px",
                            border: "1px solid #ff475744", borderRadius: 2,
                            background: "#1a0008", color: "#ff4757",
                            cursor: "pointer", ...mono, fontSize: 9, letterSpacing: "0.08em",
                          }}
                        >
                          CANCEL
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </div>
    </div>
  );
}