<<<<<<< HEAD
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { csrfFetch, readJsonSafe } from "../auth/http";
import { useAuth } from "../auth/AuthContext";

function LoginPage() {
  const navigate = useNavigate();
  const { user, refresh } = useAuth();

  const [mode, setMode] = useState("login"); // login | forgot | otp | reset
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [otp, setOtp] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [resetUid, setResetUid] = useState("");
  const [resetToken, setResetToken] = useState("");

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [googleReady, setGoogleReady] = useState(false);

  const googleHref = useMemo(() => "/accounts/google/login/?process=login&next=/", []);

  useEffect(() => {
    if (user) navigate("/");
    const t = setTimeout(() => {
      fetch("/api/users/csrf/", { credentials: "include" }).catch(() => { });
    }, 0);
    return () => clearTimeout(t);
  }, [navigate, user]);

  useEffect(() => {
    const t = setTimeout(async () => {
      try {
        const res = await fetch("/api/users/oauth/status/", { credentials: "include" });
        const data = await readJsonSafe(res);
        setGoogleReady(Boolean(data?.google_configured));
      } catch {
        setGoogleReady(false);
      }
    }, 0);
    return () => clearTimeout(t);
  }, []);

  const clearAlerts = () => {
    setError("");
    setMessage("");
  };

  const go = (nextMode) => {
    clearAlerts();
    setMode(nextMode);
  };

  const onLogin = async (e) => {
    e.preventDefault();
    clearAlerts();
    setBusy(true);
    try {
      await fetch("/api/users/csrf/", { credentials: "include" });
      const res = await csrfFetch("/api/users/login/", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      const data = await readJsonSafe(res);
      if (!res.ok) throw new Error(data?.error || "Login failed.");
      setMessage("Logged in! Redirecting...");
      await refresh();
      setTimeout(() => navigate("/"), 300);
    } catch (err) {
      setError(err?.message || "Login failed.");
    } finally {
      setBusy(false);
    }
  };

  const onForgot = async (e) => {
    e.preventDefault();
    clearAlerts();
    setBusy(true);
    try {
      await fetch("/api/users/csrf/", { credentials: "include" });
      const res = await csrfFetch("/api/users/password/forgot/", {
        method: "POST",
        body: JSON.stringify({ email }),
      });
      const data = await readJsonSafe(res);
      if (!res.ok) throw new Error(data?.error || "Could not send OTP.");
      setMessage("If that email exists, an OTP was sent. Enter it below.");
      setOtp("");
      setResetUid("");
      setResetToken("");
      setMode("otp");
    } catch (err) {
      setError(err?.message || "Could not send OTP.");
    } finally {
      setBusy(false);
    }
  };

  const onVerifyOtp = async (e) => {
    e.preventDefault();
    clearAlerts();
    setBusy(true);
    try {
      await fetch("/api/users/csrf/", { credentials: "include" });
      const res = await csrfFetch("/api/users/password/verify-otp/", {
        method: "POST",
        body: JSON.stringify({ email, otp }),
      });
      const data = await readJsonSafe(res);
      if (!res.ok) throw new Error(data?.error || "OTP verification failed.");
      setResetUid(data.uid);
      setResetToken(data.token);
      setMessage("OTP verified. Now set a new password.");
      setMode("reset");
    } catch (err) {
      setError(err?.message || "OTP verification failed.");
    } finally {
      setBusy(false);
    }
  };

  const onReset = async (e) => {
    e.preventDefault();
    clearAlerts();
    if (newPassword !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    setBusy(true);
    try {
      await fetch("/api/users/csrf/", { credentials: "include" });
      const res = await csrfFetch("/api/users/password/reset/", {
        method: "POST",
        body: JSON.stringify({ uid: resetUid, token: resetToken, new_password: newPassword }),
      });
      const data = await readJsonSafe(res);
      if (!res.ok) throw new Error((Array.isArray(data?.error) ? data.error.join(" ") : data?.error) || "Reset failed.");
      setMessage("Password updated! You can log in now.");
      setPassword("");
      setOtp("");
      setNewPassword("");
      setConfirmPassword("");
      setMode("login");
    } catch (err) {
      setError(err?.message || "Reset failed.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-6">
      <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden">
        <div className="p-6 border-b border-slate-800">
          <div className="text-sm text-slate-400">GRP DESIS</div>
          <h1 className="text-2xl font-extrabold tracking-tight mt-1">Sign in</h1>
          <p className="text-slate-400 text-sm mt-2">
            Use your email + password, or continue with Google.
          </p>
        </div>

        <div className="p-6 space-y-4">
          {message && (
            <div className="rounded-xl border border-emerald-500/40 bg-emerald-500/10 text-emerald-200 px-4 py-3 text-sm">
              {message}
            </div>
          )}
          {error && (
            <div className="rounded-xl border border-red-500/40 bg-red-500/10 text-red-200 px-4 py-3 text-sm">
              {error}
            </div>
          )}

          <a
            href={googleHref}
            onClick={(e) => {
              if (!googleReady) e.preventDefault();
            }}
            className={`w-full inline-flex items-center justify-center gap-3 rounded-xl border px-4 py-3 font-semibold transition-colors ${
              googleReady
                ? "border-slate-700 bg-slate-950 hover:bg-slate-900"
                : "border-slate-900 bg-slate-950 text-slate-500 cursor-not-allowed"
            }`}
            aria-disabled={!googleReady}
          >
            <span className="w-5 h-5 rounded-full bg-white text-black flex items-center justify-center text-xs font-black">G</span>
            Continue with Google
          </a>
          {!googleReady && (
            <div className="text-xs text-slate-500">
              Google login isn’t set up yet (needs a Google OAuth Client ID/Secret in Django Admin → Social applications).
            </div>
          )}

          <div className="flex items-center gap-3">
            <div className="h-px bg-slate-800 flex-1" />
            <div className="text-xs text-slate-500">or</div>
            <div className="h-px bg-slate-800 flex-1" />
          </div>

          {(mode === "login") && (
            <form onSubmit={onLogin} className="space-y-3">
              <div>
                <label className="text-xs text-slate-400">Email</label>
                <input
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  type="email"
                  required
                  placeholder="you@example.com"
                  className="mt-1 w-full rounded-xl bg-slate-950 border border-slate-800 px-4 py-3 outline-none focus:ring-2 focus:ring-blue-500/60"
                />
              </div>
              <div>
                <label className="text-xs text-slate-400">Password</label>
                <input
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  type="password"
                  required
                  placeholder="••••••••"
                  className="mt-1 w-full rounded-xl bg-slate-950 border border-slate-800 px-4 py-3 outline-none focus:ring-2 focus:ring-blue-500/60"
                />
              </div>
              <button
                disabled={busy}
                className="w-full rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-50 px-4 py-3 font-bold transition-colors"
                type="submit"
              >
                {busy ? "Signing in..." : "Sign in"}
              </button>
              <button
                type="button"
                onClick={() => go("forgot")}
                className="w-full text-sm text-slate-400 hover:text-slate-200"
              >
                Forgot password?
              </button>
            </form>
          )}

          {(mode === "forgot") && (
            <form onSubmit={onForgot} className="space-y-3">
              <div>
                <label className="text-xs text-slate-400">Email</label>
                <input
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  type="email"
                  required
                  placeholder="you@example.com"
                  className="mt-1 w-full rounded-xl bg-slate-950 border border-slate-800 px-4 py-3 outline-none focus:ring-2 focus:ring-blue-500/60"
                />
              </div>
              <button
                disabled={busy}
                className="w-full rounded-xl bg-amber-500 hover:bg-amber-400 disabled:opacity-50 px-4 py-3 font-bold text-black transition-colors"
                type="submit"
              >
                {busy ? "Sending OTP..." : "Send OTP"}
              </button>
              <button
                type="button"
                onClick={() => go("login")}
                className="w-full text-sm text-slate-400 hover:text-slate-200"
              >
                Back to sign in
              </button>
            </form>
          )}

          {(mode === "otp") && (
            <form onSubmit={onVerifyOtp} className="space-y-3">
              <div>
                <label className="text-xs text-slate-400">Email</label>
                <input
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  type="email"
                  required
                  className="mt-1 w-full rounded-xl bg-slate-950 border border-slate-800 px-4 py-3 outline-none focus:ring-2 focus:ring-blue-500/60"
                />
              </div>
              <div>
                <label className="text-xs text-slate-400">OTP (6 digits)</label>
                <input
                  value={otp}
                  onChange={(e) => setOtp(e.target.value)}
                  inputMode="numeric"
                  pattern="[0-9]{6}"
                  required
                  placeholder="123456"
                  className="mt-1 w-full rounded-xl bg-slate-950 border border-slate-800 px-4 py-3 outline-none focus:ring-2 focus:ring-blue-500/60 tracking-widest"
                />
                <div className="text-xs text-slate-500 mt-2">
                  Dev note: if email is using the console backend, the OTP prints in the Django server logs.
                </div>
              </div>
              <button
                disabled={busy}
                className="w-full rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 px-4 py-3 font-bold transition-colors"
                type="submit"
              >
                {busy ? "Verifying..." : "Verify OTP"}
              </button>
              <div className="flex justify-between text-sm">
                <button type="button" onClick={() => go("forgot")} className="text-slate-400 hover:text-slate-200">
                  Resend OTP
                </button>
                <button type="button" onClick={() => go("login")} className="text-slate-400 hover:text-slate-200">
                  Back to sign in
                </button>
              </div>
            </form>
          )}

          {(mode === "reset") && (
            <form onSubmit={onReset} className="space-y-3">
              <div>
                <label className="text-xs text-slate-400">New password</label>
                <input
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  type="password"
                  required
                  className="mt-1 w-full rounded-xl bg-slate-950 border border-slate-800 px-4 py-3 outline-none focus:ring-2 focus:ring-blue-500/60"
                />
              </div>
              <div>
                <label className="text-xs text-slate-400">Confirm new password</label>
                <input
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  type="password"
                  required
                  className="mt-1 w-full rounded-xl bg-slate-950 border border-slate-800 px-4 py-3 outline-none focus:ring-2 focus:ring-blue-500/60"
                />
              </div>
              <button
                disabled={busy}
                className="w-full rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-50 px-4 py-3 font-bold transition-colors"
                type="submit"
              >
                {busy ? "Updating..." : "Update password"}
              </button>
              <button
                type="button"
                onClick={() => go("login")}
                className="w-full text-sm text-slate-400 hover:text-slate-200"
              >
                Back to sign in
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
=======
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

export default function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleLogin = async () => {
    setLoading(true)
    setError('')

    // Step 1 — get CSRF token
    await fetch('/api-auth/login/', { credentials: 'include' })
    const csrfToken = document.cookie
      .split('; ')
      .find(row => row.startsWith('csrftoken='))
      ?.split('=')[1]

    // Step 2 — submit login
    const response = await fetch('/api-auth/login/', {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': csrfToken || ''
      },
      body: new URLSearchParams({
        username,
        password,
        next: '/portfolio'
      }),
      redirect: 'manual'
    })

    if (response.status === 200 || response.status === 0 || response.type === 'opaqueredirect') {
      navigate('/portfolio')
    } else {
      setError('Invalid username or password')
    }
    setLoading(false)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900 flex items-center justify-center">
      <div className="w-full max-w-md">

        {/* LOGO */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center font-bold text-2xl mx-auto mb-4">D</div>
          <h1 className="text-3xl font-black text-white">Desis Portfolio</h1>
          <p className="text-gray-400 mt-2">Sign in to your account</p>
        </div>

        {/* FORM CARD */}
        <div className="bg-gray-900/50 backdrop-blur-xl rounded-2xl p-8 border border-gray-800">

          {/* Error */}
          {error && (
            <div className="mb-6 p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm">
              🚨 {error}
            </div>
          )}

          {/* Username */}
          <div className="mb-4">
            <label className="text-sm text-gray-400 mb-2 block">Username</label>
            <input
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              placeholder="Enter your username"
              className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
            />
          </div>

          {/* Password */}
          <div className="mb-6">
            <label className="text-sm text-gray-400 mb-2 block">Password</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="Enter your password"
              onKeyDown={e => e.key === 'Enter' && handleLogin()}
              className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
            />
          </div>

          {/* Button */}
          <button
            onClick={handleLogin}
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-bold py-3 rounded-xl transition-colors"
          >
            {loading ? 'Signing in...' : 'Sign In →'}
          </button>

        </div>

        <p className="text-center text-gray-500 text-sm mt-6">
          Desis Portfolio Intelligence Platform
        </p>
      </div>
    </div>
  )
}
>>>>>>> origin/main
