import { useEffect, useMemo, useState } from "react";

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

function AIPage() {
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [user, setUser] = useState(null);
  const [error, setError] = useState("");

  const [chatLoading, setChatLoading] = useState(false);
  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState([
    {
      role: "assistant",
      text: "Hi! I’m your AI trading assistant. Ask me about your risk profile, trader type, anomaly detection, or suggestions.",
    },
  ]);

  const fetchCSRF = async () => {
    try {
      await fetch("http://localhost:8000/api/csrf/", {
        method: "GET",
        credentials: "include",
      });
    } catch (err) {
      console.log("CSRF fetch failed:", err);
    }
  };

  const fetchMe = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/users/me/", {
        method: "GET",
        credentials: "include",
      });
      const data = await res.json();
      if (res.ok) setUser(data);
    } catch (err) {
      console.log("Fetch user failed:", err);
    }
  };

  const fetchHistory = async () => {
    setHistoryLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/ai/history/", {
        method: "GET",
        credentials: "include",
      });
      const data = await res.json();
      if (res.ok && Array.isArray(data)) {
        setHistory(data);
      }
    } catch (err) {
      console.log("Fetch history failed:", err);
    }
    setHistoryLoading(false);
  };

  useEffect(() => {
    fetchCSRF();
    fetchMe();
    fetchHistory();
  }, []);

  const handleAskAI = async () => {
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const res = await fetch("http://localhost:8000/api/ai/feedback/", {
        method: "GET",
        credentials: "include",
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.error || "Something went wrong while generating feedback.");
      } else {
        setResult(data);
        fetchHistory();
      }
    } catch (err) {
      setError(`Request failed: ${err.message}`);
    }

    setLoading(false);
  };

  const handleSendChat = async () => {
    if (!chatInput.trim()) return;

    const userMsg = { role: "user", text: chatInput };
    setChatMessages((prev) => [...prev, userMsg]);

    const currentMessage = chatInput;
    setChatInput("");
    setChatLoading(true);

    try {
      const csrftoken = getCookie("csrftoken");

      const res = await fetch("http://localhost:8000/api/ai/chat/", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrftoken,
        },
        body: JSON.stringify({ message: currentMessage }),
      });

      const data = await res.json();

      if (!res.ok) {
        setChatMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            text: data.error || "Something went wrong while generating chatbot reply.",
          },
        ]);
      } else {
        setChatMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            text: data.reply || "No reply received.",
          },
        ]);
      }
    } catch (err) {
      setChatMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: `Request failed: ${err.message}`,
        },
      ]);
    }

    setChatLoading(false);
  };

  const handleChatKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendChat();
    }
  };

  const summaryCards = useMemo(() => {
    if (!result) return [];

    const rule = result.rule_based || {};
    const ml = result.ml_based || {};

    return [
      {
        title: "Risk Profile",
        value: rule.risk_profile || "Not available",
        sub: "Derived from portfolio and trading behavior",
      },
      {
        title: "Trader Type",
        value: ml.ml_available ? ml.trader_type || "Unknown" : "ML unavailable",
        sub: "Predicted using behavioral signals",
      },
      {
        title: "Anomaly Detection",
        value: ml.ml_available ? (ml.is_anomaly ? "Detected" : "Normal") : "Unavailable",
        sub: ml.ml_available ? "Behavior consistency check" : "No ML output found",
      },
      {
        title: "Insight ID",
        value: result.insight_id || "—",
        sub: "Stored analysis record",
      },
    ];
  }, [result]);

  const renderValue = (v) => {
    if (v === null || v === undefined) return "—";
    if (typeof v === "boolean") return v ? "Yes" : "No";
    if (typeof v === "number") return Number.isInteger(v) ? v : v.toFixed(4);
    if (Array.isArray(v)) return v.join(", ");
    if (typeof v === "object") return JSON.stringify(v, null, 2);
    return String(v);
  };

  const renderObjectGrid = (obj) => {
    if (!obj || typeof obj !== "object") {
      return <p className="text-slate-300">No data available.</p>;
    }

    const entries = Object.entries(obj);

    if (!entries.length) {
      return <p className="text-slate-300">No data available.</p>;
    }

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {entries.map(([k, v]) => (
          <div
            key={k}
            className="rounded-2xl border border-blue-900/70 bg-[#101a43] p-4"
          >
            <p className="text-xs uppercase tracking-wide text-sky-300 mb-2">
              {k.replaceAll("_", " ")}
            </p>
            {typeof v === "object" && v !== null ? (
              <pre className="text-sm text-slate-200 whitespace-pre-wrap break-words">
                {JSON.stringify(v, null, 2)}
              </pre>
            ) : (
              <p className="text-base text-white">{renderValue(v)}</p>
            )}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-[#020b2d] text-white p-6 md:p-8">
      <div className="max-w-7xl mx-auto">
        <div className="rounded-3xl border border-blue-900/60 bg-gradient-to-r from-[#08133b] to-[#0d1d56] p-6 md:p-8 shadow-2xl mb-8">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
            <div>
              <p className="text-sky-300 text-sm uppercase tracking-[0.2em] mb-2">
                AI Engine
              </p>
              <h1 className="text-3xl md:text-5xl font-bold mb-3">
                Intelligent Trading Insight Dashboard
              </h1>
              <p className="text-slate-300 max-w-3xl leading-7">
                Generate detailed AI-driven feedback based on portfolio state,
                trading activity, behavioral patterns, and anomaly signals.
                This module combines rule-based reasoning with ML-based user
                profiling to produce actionable recommendations.
              </p>
            </div>

            <div className="min-w-[260px] rounded-2xl bg-white/5 border border-white/10 p-5">
              <p className="text-sm text-slate-300 mb-2">Active Session</p>
              <p className="text-2xl font-semibold text-white">
                {user?.username || "Not detected"}
              </p>
              <p className="text-sm text-slate-400 mt-2">
                Authenticated user context is used to generate personalized AI insights.
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
          <div className="xl:col-span-2 space-y-8">
            <div className="rounded-3xl border border-blue-900/60 bg-[#08133b] p-6 shadow-xl">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
                <div>
                  <h2 className="text-2xl font-semibold mb-2">
                    Generate New AI Feedback
                  </h2>
                  <p className="text-slate-300">
                    Click below to run the current feedback pipeline on the logged-in user profile.
                  </p>
                </div>

                <button
                  onClick={handleAskAI}
                  disabled={loading}
                  className="px-6 py-3 rounded-2xl bg-blue-600 hover:bg-blue-700 transition disabled:opacity-60 disabled:cursor-not-allowed shadow-lg"
                >
                  {loading ? "Analyzing..." : "Generate AI Feedback"}
                </button>
              </div>

              {loading && (
                <div className="rounded-2xl border border-blue-800 bg-[#101a43] p-5">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="h-4 w-4 rounded-full bg-sky-400 animate-pulse" />
                    <p className="text-sky-300 font-medium">
                      Running rule-based and ML analysis...
                    </p>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="h-24 rounded-2xl bg-white/5 animate-pulse" />
                    <div className="h-24 rounded-2xl bg-white/5 animate-pulse" />
                    <div className="h-24 rounded-2xl bg-white/5 animate-pulse" />
                  </div>
                </div>
              )}

              {error && (
                <div className="mt-4 rounded-2xl border border-red-500/30 bg-red-500/10 p-4 text-red-300">
                  {error}
                </div>
              )}
            </div>

            {result && (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 2xl:grid-cols-4 gap-4">
                  {summaryCards.map((card) => (
                    <div
                      key={card.title}
                      className="rounded-3xl border border-blue-900/60 bg-[#08133b] p-5 shadow-lg"
                    >
                      <p className="text-sm text-sky-300 mb-2">{card.title}</p>
                      <p className="text-2xl font-bold text-white break-words">
                        {card.value}
                      </p>
                      <p className="text-sm text-slate-400 mt-2">{card.sub}</p>
                    </div>
                  ))}
                </div>

                <div className="rounded-3xl border border-blue-900/60 bg-[#08133b] p-6 shadow-xl">
                  <h2 className="text-2xl font-semibold mb-4">
                    Final Recommendations
                  </h2>

                  {result.final_tips?.length ? (
                    <div className="space-y-3">
                      {result.final_tips.map((tip, idx) => (
                        <div
                          key={idx}
                          className="rounded-2xl border border-blue-900/70 bg-[#101a43] p-4"
                        >
                          <div className="flex items-start gap-3">
                            <div className="h-8 w-8 shrink-0 rounded-full bg-blue-600 flex items-center justify-center font-semibold">
                              {idx + 1}
                            </div>
                            <p className="text-slate-100 leading-7">{tip}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-slate-300">No recommendations available.</p>
                  )}
                </div>

                <div className="rounded-3xl border border-blue-900/60 bg-[#08133b] p-6 shadow-xl">
                  <h2 className="text-2xl font-semibold mb-4">
                    Rule-Based Analysis
                  </h2>
                  {renderObjectGrid(result.rule_based)}
                </div>

                <div className="rounded-3xl border border-blue-900/60 bg-[#08133b] p-6 shadow-xl">
                  <h2 className="text-2xl font-semibold mb-4">ML Analysis</h2>
                  {renderObjectGrid(result.ml_based)}
                </div>
              </>
            )}
          </div>

          <div className="space-y-8">
            <div className="rounded-3xl border border-blue-900/60 bg-[#08133b] p-6 shadow-xl">
              <h2 className="text-2xl font-semibold mb-4">How This Works</h2>
              <div className="space-y-4 text-slate-300 leading-7">
                <div className="rounded-2xl bg-[#101a43] border border-blue-900/70 p-4">
                  <p className="text-sky-300 font-medium mb-1">Step 1</p>
                  <p>Portfolio and user activity are analyzed using rule-based logic.</p>
                </div>
                <div className="rounded-2xl bg-[#101a43] border border-blue-900/70 p-4">
                  <p className="text-sky-300 font-medium mb-1">Step 2</p>
                  <p>Behavioral ML models infer trader type and detect anomalies.</p>
                </div>
                <div className="rounded-2xl bg-[#101a43] border border-blue-900/70 p-4">
                  <p className="text-sky-300 font-medium mb-1">Step 3</p>
                  <p>Signals are combined into a saved insight record and recommendation list.</p>
                </div>
              </div>
            </div>

            <div className="rounded-3xl border border-blue-900/60 bg-[#08133b] p-6 shadow-xl">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-semibold">Recent Insight History</h2>
                <button
                  onClick={fetchHistory}
                  className="text-sm px-3 py-2 rounded-xl bg-white/5 hover:bg-white/10 transition"
                >
                  Refresh
                </button>
              </div>

              {historyLoading ? (
                <p className="text-slate-300">Loading history...</p>
              ) : history.length ? (
                <div className="space-y-4 max-h-[650px] overflow-y-auto pr-1">
                  {history.slice(0, 8).map((item) => (
                    <div
                      key={item.id}
                      className="rounded-2xl border border-blue-900/70 bg-[#101a43] p-4"
                    >
                      <div className="flex items-center justify-between gap-3 mb-3">
                        <p className="text-sky-300 font-medium">
                          Insight #{item.id}
                        </p>
                        <p className="text-xs text-slate-400">
                          {item.created_at
                            ? new Date(item.created_at).toLocaleString()
                            : "Timestamp unavailable"}
                        </p>
                      </div>

                      <div className="space-y-2 text-sm">
                        <p>
                          <span className="text-slate-400">Risk:</span>{" "}
                          <span className="text-white">{item.risk_profile || "—"}</span>
                        </p>
                        <p>
                          <span className="text-slate-400">Trader Type:</span>{" "}
                          <span className="text-white">{item.trader_type || "—"}</span>
                        </p>
                        <p>
                          <span className="text-slate-400">Anomaly:</span>{" "}
                          <span className="text-white">
                            {item.anomaly_detected ? "Yes" : "No"}
                          </span>
                        </p>
                      </div>

                      <div className="mt-3 rounded-xl bg-white/5 p-3 text-sm text-slate-300 leading-6">
                        {item.summary || "No summary available."}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-slate-300">
                  No insight history found yet. Generate feedback to create the first record.
                </p>
              )}
            </div>
          </div>
        </div>

        <div className="mt-8 rounded-3xl border border-blue-900/60 bg-[#08133b] p-6 shadow-xl">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3 mb-6">
            <div>
              <h2 className="text-2xl font-semibold">AI Chatbot Assistant</h2>
              <p className="text-slate-300 mt-1">
                Ask for explanation of your current risk profile, trader behavior, anomaly detection, or suggestions.
              </p>
            </div>
          </div>

          <div className="rounded-2xl border border-blue-900/70 bg-[#101a43] p-4 h-[420px] overflow-y-auto space-y-4 mb-4">
            {chatMessages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-3 leading-7 ${
                    msg.role === "user"
                      ? "bg-blue-600 text-white"
                      : "bg-white/5 border border-blue-900/70 text-slate-100"
                  }`}
                >
                  {msg.text}
                </div>
              </div>
            ))}

            {chatLoading && (
              <div className="flex justify-start">
                <div className="max-w-[80%] rounded-2xl px-4 py-3 bg-white/5 border border-blue-900/70 text-slate-100">
                  Thinking...
                </div>
              </div>
            )}
          </div>

          <div className="flex flex-col md:flex-row gap-3">
            <textarea
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={handleChatKeyDown}
              placeholder="Ask something like: Why is my risk profile high?"
              className="flex-1 min-h-[70px] rounded-2xl bg-[#101a43] border border-blue-900/70 p-4 text-white outline-none resize-none"
            />
            <button
              onClick={handleSendChat}
              disabled={chatLoading}
              className="px-6 py-3 rounded-2xl bg-blue-600 hover:bg-blue-700 transition disabled:opacity-60"
            >
              {chatLoading ? "Sending..." : "Send"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AIPage;