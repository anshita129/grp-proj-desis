import { useState } from "react";
import { useNavigate } from "react-router-dom";

function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMsg("");

    try {
      const res = await fetch("http://localhost:8000/api/users/login/", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password }),
      });

      const data = await res.json();

      if (res.ok) {
        setMsg(`Logged in as ${data.username}`);
        setTimeout(() => {
          navigate("/ai");
        }, 800);
      } else {
        setMsg(data.error || `Login failed (${res.status})`);
      }
    } catch (err) {
      setMsg(`Request failed: ${err.message}`);
    }

    setLoading(false);
  };

  return (
    <div className="p-8 min-h-screen bg-[#020b2d] text-white">
      <h1 className="text-3xl font-semibold mb-6">Login</h1>

      <form
        onSubmit={handleLogin}
        className="max-w-md bg-[#0b1437] p-6 rounded-2xl border border-blue-900 shadow-lg"
      >
        <label className="block mb-2">Username</label>
        <input
          className="w-full mb-4 p-3 rounded-xl bg-[#111c44] border border-blue-800 outline-none"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="Enter username"
        />

        <label className="block mb-2">Password</label>
        <input
          type="password"
          className="w-full mb-4 p-3 rounded-xl bg-[#111c44] border border-blue-800 outline-none"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Enter password"
        />

        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 rounded-xl bg-blue-600 hover:bg-blue-700 transition disabled:opacity-60"
        >
          {loading ? "Signing in..." : "Sign in"}
        </button>

        {msg && <p className="mt-4 text-sm">{msg}</p>}
      </form>
    </div>
  );
}

export default LoginPage;