// backend URL
const BASE = "http://127.0.0.1:8000/api/trading";

// returns the default headers for every request
const headers = () => ({
  "Content-Type": "application/json",
});
const authHeaders = () => ({
  "Content-Type": "application/json",
  "Authorization": `Token ${localStorage.getItem("token")}`
});

// Public endpoint, anyone can see the stock list
export const fetchStocks = () =>
  fetch(`${BASE}/stocks/`, { headers: headers() }).then(r => r.json());

// needs auth
export const fetchHoldings = () =>
  fetch(`${BASE}/holdings/`, { headers: authHeaders() }).then(r => r.json());

export const fetchWallet = () =>
  fetch(`${BASE}/wallet/`, { headers: authHeaders() }).then(r => r.json());

export const fetchHistory = () =>
  fetch(`${BASE}/history/`, { headers: authHeaders() }).then(r => r.json());

export const fetchPending = () =>
  fetch(`${BASE}/orders/pending/`, { headers: authHeaders() }).then(r => r.json());

export const placeBuy = (symbol, quantity, limit_price = null) =>
  fetch(`${BASE}/buy/`, {
    method: "POST", headers: authHeaders(),
    body: JSON.stringify({ symbol, quantity, ...(limit_price && { limit_price }) })
  }).then(r => r.json());

export const placeSell = (symbol, quantity, limit_price = null) =>
  fetch(`${BASE}/sell/`, {
    method: "POST", headers: authHeaders(),
    body: JSON.stringify({ symbol, quantity, ...(limit_price && { limit_price }) })
  }).then(r => r.json());

export const cancelOrder = (orderId) =>
  fetch(`${BASE}/cancel/${orderId}/`, { method: "POST", headers: authHeaders() }).then(r => r.json());