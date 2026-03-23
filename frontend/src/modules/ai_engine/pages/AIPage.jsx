import { useEffect, useMemo, useRef, useState } from "react";

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
  const defaultMessages = [
    {
      role: "assistant",
      text: "Hi! 👋 I’m your trading assistant. Ask me about your trading pattern, peer comparison, anomaly status, or how to improve.",
    },
  ];

  const [user, setUser] = useState(null);
  const [showHistory, setShowHistory] = useState(false);
  const [chatLoading, setChatLoading] = useState(false);
  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState(defaultMessages);

  const chatBoxRef = useRef(null);

  const storageKey = user?.username
    ? `ai_chat_history_${user.username}`
    : "ai_chat_history_guest";

  useEffect(() => {
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

        if (res.ok) {
          setUser(data);
        }
      } catch (err) {
        console.log("Fetch user failed:", err);
      }
    };

    fetchCSRF();
    fetchMe();
  }, []);

  useEffect(() => {
    try {
      const saved = localStorage.getItem(storageKey);
      if (saved) {
        setChatMessages(JSON.parse(saved));
      } else {
        setChatMessages(defaultMessages);
      }
    } catch {
      setChatMessages(defaultMessages);
    }
  }, [storageKey]);

  useEffect(() => {
    try {
      localStorage.setItem(storageKey, JSON.stringify(chatMessages));
    } catch (err) {
      console.log("Saving chat history failed:", err);
    }
  }, [chatMessages, storageKey]);

  useEffect(() => {
    if (chatBoxRef.current) {
      chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight;
    }
  }, [chatMessages, chatLoading]);

  const latestAssistantReply = useMemo(() => {
    for (let i = chatMessages.length - 1; i >= 0; i--) {
      if (chatMessages[i].role === "assistant") {
        return chatMessages[i].text;
      }
    }
    return "";
  }, [chatMessages]);

  const quickSuggestions = useMemo(() => {
    if (!latestAssistantReply) {
      return [
        "Ask how your trading compares with peers.",
        "Ask how to improve your trade sizing.",
        "Ask whether any anomaly is detected.",
      ];
    }

    const lines = latestAssistantReply
      .split(/\n|\./)
      .map((x) => x.trim())
      .filter(Boolean);

    const out = [];

    for (const line of lines) {
      const l = line.toLowerCase();

      if (
        l.includes("improve") ||
        l.includes("consider") ||
        l.includes("reduce") ||
        l.includes("avoid") ||
        l.includes("maintain") ||
        l.includes("keep") ||
        l.includes("monitor") ||
        l.includes("diversif") ||
        l.includes("smaller") ||
        l.includes("balance") ||
        l.includes("stability")
      ) {
        out.push(line);
      }

      if (out.length === 3) break;
    }

    if (!out.length) {
      return [
        "Ask for a short improvement plan.",
        "Ask for peer comparison in simple words.",
        "Ask what your current trading style means.",
      ];
    }

    return out;
  }, [latestAssistantReply]);

  const clearChatHistory = () => {
    setChatMessages(defaultMessages);
    localStorage.setItem(storageKey, JSON.stringify(defaultMessages));
  };

  const handleSendChat = async () => {
    if (!chatInput.trim()) return;

    const currentMessage = chatInput.trim();
    const msg = currentMessage.toLowerCase();

    const greetings = ["hi", "hello", "hey", "hii", "heyy"];
    if (greetings.includes(msg)) {
      setChatMessages((prev) => [
        ...prev,
        { role: "user", text: currentMessage },
        {
          role: "assistant",
          text: "Hi! 😊 Ask me about your trading style, peer comparison, anomaly status, or suggestions to improve.",
        },
      ]);
      setChatInput("");
      return;
    }

    const userMsg = { role: "user", text: currentMessage };
    setChatMessages((prev) => [...prev, userMsg]);
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
            text: data.error || "Sorry, something went wrong while generating the reply.",
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-indigo-950 to-blue-950 text-white px-4 py-6 md:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-white">
            Trading Assistant ✨
          </h1>
          <p className="text-slate-300 mt-2 max-w-3xl">
            Ask about your trading behavior, peer comparison, anomaly detection, or suggestions to improve.
          </p>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
          <div className="xl:col-span-2">
            <div className="rounded-3xl border border-blue-900/60 bg-[#08133b] p-6 shadow-xl shadow-blue-900/20 h-full">
              <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3 mb-6">
                <div>
                  <h2 className="text-2xl font-semibold">Chatbot 💬</h2>
                  <p className="text-slate-300 mt-1">
                    Talk naturally with your assistant.
                  </p>
                </div>

                <div className="flex items-center gap-3 flex-wrap">
                  <div className="rounded-2xl border border-cyan-700/50 bg-gradient-to-r from-cyan-900/30 to-blue-900/30 px-4 py-2 text-sm text-cyan-200 shadow-md shadow-cyan-900/20">
                    Smart • Personal • Conversational
                  </div>

                  <button
                    onClick={() => setShowHistory(true)}
                    className="px-4 py-2 rounded-2xl bg-gradient-to-r from-purple-900/40 to-blue-900/40 border border-indigo-700/50 hover:from-purple-800/50 hover:to-blue-800/50 transition text-sm text-indigo-100 shadow-md shadow-indigo-900/20"
                  >
                    History 📜
                  </button>
                </div>
              </div>

              <div
                ref={chatBoxRef}
                className="rounded-2xl border border-blue-800/60 bg-gradient-to-br from-[#0f1b4c] via-[#111f5a] to-[#0b1640] p-4 h-[520px] overflow-y-auto space-y-4 mb-4 scroll-smooth shadow-inner shadow-blue-900/40"
              >
                {chatMessages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`max-w-[85%] rounded-3xl px-4 py-3 leading-8 whitespace-pre-wrap break-words transition-transform hover:scale-[1.01] ${
                        msg.role === "user"
                          ? "bg-gradient-to-r from-blue-500 to-indigo-500 text-white shadow-lg shadow-blue-500/30"
                          : "bg-gradient-to-br from-indigo-900/40 to-blue-900/30 backdrop-blur-md border border-blue-800/60 text-slate-100 shadow-md shadow-indigo-950/20"
                      }`}
                    >
                      <div className="text-xs mb-1 opacity-80">
                        {msg.role === "user" ? "You" : "Assistant 🤖"}
                      </div>
                      <div>{msg.text}</div>
                    </div>
                  </div>
                ))}

                {chatLoading && (
                  <div className="flex justify-start">
                    <div className="max-w-[85%] rounded-3xl px-4 py-3 bg-gradient-to-br from-indigo-900/40 to-blue-900/30 backdrop-blur-md border border-blue-800/60 text-slate-100 shadow-md shadow-indigo-950/20">
                      <div className="text-xs mb-1 opacity-80">Assistant 🤖</div>
                      <div className="flex items-center gap-2">
                        <span className="h-2 w-2 rounded-full bg-cyan-300 animate-bounce" />
                        <span className="h-2 w-2 rounded-full bg-blue-300 animate-bounce [animation-delay:120ms]" />
                        <span className="h-2 w-2 rounded-full bg-violet-300 animate-bounce [animation-delay:240ms]" />
                        <span className="ml-2 text-cyan-100">Thinking...</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              <div className="flex flex-col md:flex-row gap-3">
                <textarea
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={handleChatKeyDown}
                  placeholder="Ask something like: How can I improve my trading style?"
                  className="flex-1 min-h-[72px] rounded-2xl bg-gradient-to-r from-[#0f1b4c] to-[#0b1640] border border-blue-800/60 p-4 text-white outline-none resize-none placeholder:text-slate-400 focus:ring-2 focus:ring-blue-500/40"
                />
                <button
                  onClick={handleSendChat}
                  disabled={chatLoading}
                  className="px-6 py-3 rounded-2xl bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-600 hover:to-indigo-600 transition disabled:opacity-60 shadow-lg shadow-blue-500/30"
                >
                  {chatLoading ? "Sending..." : "Send 🚀"}
                </button>
              </div>
            </div>
          </div>

          <div className="space-y-8">
            <div className="rounded-3xl border border-cyan-900/40 bg-gradient-to-br from-[#08133b] to-[#0b1748] p-6 shadow-xl shadow-cyan-950/10">
              <h2 className="text-2xl font-semibold mb-4">How This Works 🧠</h2>

              <div className="space-y-4 text-slate-300 leading-7">
                <div className="rounded-2xl bg-gradient-to-r from-cyan-900/20 to-blue-900/20 border border-cyan-800/30 p-4">
                  <p className="text-cyan-300 font-medium mb-1">Step 1 • Behavior Analysis</p>
                  <p>
                    Your trading activity and portfolio behavior are studied using rule-based logic and machine learning signals.
                  </p>
                </div>

                <div className="rounded-2xl bg-gradient-to-r from-blue-900/20 to-indigo-900/20 border border-blue-800/30 p-4">
                  <p className="text-sky-300 font-medium mb-1">Step 2 • Peer Comparison</p>
                  <p>
                    Your patterns are compared with aggregated peer trends to understand how your activity differs from typical users.
                  </p>
                </div>

                <div className="rounded-2xl bg-gradient-to-r from-violet-900/20 to-indigo-900/20 border border-violet-800/30 p-4">
                  <p className="text-violet-300 font-medium mb-1">Step 3 • Explanation</p>
                  <p>
                    The chatbot turns these signals into a clear explanation with short, useful suggestions.
                  </p>
                </div>
              </div>
            </div>

            <div className="rounded-3xl border border-pink-900/30 bg-gradient-to-br from-[#08133b] to-[#15123f] p-6 shadow-xl shadow-pink-950/10">
              <h2 className="text-2xl font-semibold mb-1">Quick Suggestions 🌟</h2>
              <p className="text-slate-400 text-sm mb-4">
                Based on your latest response
              </p>

              <div className="space-y-3">
                {quickSuggestions.map((item, idx) => (
                  <div
                    key={idx}
                    className="rounded-2xl bg-gradient-to-r from-indigo-900/25 to-pink-900/20 border border-indigo-800/30 p-4 text-slate-300 leading-6 shadow-sm"
                  >
                    <span className="text-pink-300 mr-2">•</span>
                    {item}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {showHistory && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-4">
            <div className="w-full max-w-3xl rounded-3xl border border-blue-800/50 bg-gradient-to-br from-[#08133b] to-[#101a43] shadow-2xl shadow-blue-950/40 max-h-[80vh] overflow-hidden">
              <div className="flex items-center justify-between px-6 py-4 border-b border-blue-900/60">
                <h2 className="text-2xl font-semibold text-white">Chat History 📜</h2>

                <div className="flex items-center gap-3">
                  <button
                    onClick={clearChatHistory}
                    className="px-3 py-2 rounded-xl bg-gradient-to-r from-red-500/20 to-pink-500/20 hover:from-red-500/30 hover:to-pink-500/30 transition text-red-200 border border-red-800/30"
                  >
                    Clear
                  </button>

                  <button
                    onClick={() => setShowHistory(false)}
                    className="px-3 py-2 rounded-xl bg-white/5 hover:bg-white/10 transition text-slate-200 border border-blue-900/40"
                  >
                    Close ✖
                  </button>
                </div>
              </div>

              <div className="p-6 overflow-y-auto max-h-[65vh] space-y-4 bg-gradient-to-br from-[#0f1b4c] via-[#111f5a] to-[#0b1640]">
                {chatMessages.length ? (
                  chatMessages.map((msg, idx) => (
                    <div
                      key={idx}
                      className={`rounded-2xl p-4 border ${
                        msg.role === "user"
                          ? "bg-gradient-to-r from-blue-500 to-indigo-500 text-white border-blue-400 shadow-lg shadow-blue-500/20"
                          : "bg-gradient-to-br from-indigo-900/40 to-blue-900/30 text-slate-200 border-blue-800/50"
                      }`}
                    >
                      <div className="text-xs mb-2 opacity-80">
                        {msg.role === "user" ? "You" : "Assistant 🤖"}
                      </div>
                      <div className="whitespace-pre-wrap break-words leading-7">
                        {msg.text}
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-slate-300">No previous conversation found.</p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default AIPage;