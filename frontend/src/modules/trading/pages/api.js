import { getCookie } from "../../users/auth/http";

const BASE = "http://localhost:5173/api/trading";
const headers = () => ({
  "Content-Type": "application/json",
});

// Public
export const fetchStocks = () =>
  fetch(`${BASE}/stocks/`, {
    headers: headers(),
    credentials: "include",
  }).then(r => r.json());

// Auth (via cookies, NOT token)
export const fetchWallet = () =>
  fetch(`${BASE}/wallet/`, {
    headers: headers(),
    credentials: "include",
  }).then(r => r.json());

export const fetchHoldings = () =>
  fetch(`${BASE}/holdings/`, {
    headers: headers(),
    credentials: "include",
  }).then(r => r.json());

export const fetchHistory = () =>
  fetch(`${BASE}/history/`, {
    headers: headers(),
    credentials: "include",
  }).then(r => r.json());

export const fetchPending = () =>
  fetch(`${BASE}/orders/pending/`, {
    headers: headers(),
    credentials: "include",
  }).then(r => r.json());

export const placeBuy = (symbol, quantity, limit_price = null) =>
  fetch(`${BASE}/buy/`, {
    method: "POST", headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken"),
    }, credentials: "include",
    body: JSON.stringify({ symbol, quantity, ...(limit_price && { limit_price }) })
  }).then(r => r.json());

export const placeSell = (symbol, quantity, limit_price = null) =>
  fetch(`${BASE}/sell/`, {
    method: "POST", headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken"),
    }, credentials: "include",
    body: JSON.stringify({ symbol, quantity, ...(limit_price && { limit_price }) })
  }).then(r => r.json());

export const cancelOrder = (orderId) =>
  fetch(`${BASE}/cancel/${orderId}/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken"),
    },
    credentials: "include",
  }).then(r => r.json());