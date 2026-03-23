import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { csrfFetch, readJsonSafe } from "../auth/http";
import { useAuth } from "../auth/AuthContext";

function LoginPage() {
  const navigate = useNavigate();
  const { user, refresh } = useAuth();

  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
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

  const googleHref = useMemo(
    () => "http://localhost:8000/accounts/google/login/?process=login",
    []
  );

  useEffect(() => {
    if (user) navigate("/");
    fetch("/api/users/csrf/", { credentials: "include" }).catch(() => { });
  }, [navigate, user]);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch("/api/users/oauth/status/", {
          credentials: "include",
        });
        const data = await readJsonSafe(res);
        setGoogleReady(Boolean(data?.google_configured));
      } catch {
        setGoogleReady(false);
      }
    })();
  }, []);

  const clearAlerts = () => {
    setError("");
    setMessage("");
  };

  const go = (m) => {
    clearAlerts();
    setMode(m);
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
      if (!res.ok) throw new Error(data?.error || "Login failed");

      setMessage("Logged in!");
      await refresh();
      setTimeout(() => navigate("/"), 300);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const onSignup = async (e) => {
    e.preventDefault();
    clearAlerts();
    setBusy(true);
    try {
      await fetch("/api/users/csrf/", { credentials: "include" });

      const res = await csrfFetch("/api/users/signup/", {
        method: "POST",
        body: JSON.stringify({ email, username, password }),
      });

      const data = await readJsonSafe(res);
      if (!res.ok)
        throw new Error(
          Array.isArray(data?.error)
            ? data.error.join(" ")
            : data?.error || "Signup failed"
        );

      setMessage("Account created!");
      await refresh();
      setTimeout(() => navigate("/"), 500);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const onForgot = async (e) => {
    e.preventDefault();
    clearAlerts();
    setBusy(true);
    try {
      await csrfFetch("/api/users/password/forgot/", {
        method: "POST",
        body: JSON.stringify({ email }),
      });

      setMessage("OTP sent");
      setMode("otp");
    } catch (err) {
      setError("Failed to send OTP");
    } finally {
      setBusy(false);
    }
  };

  const onVerifyOtp = async (e) => {
    e.preventDefault();
    clearAlerts();
    setBusy(true);
    try {
      const res = await csrfFetch("/api/users/password/verify-otp/", {
        method: "POST",
        body: JSON.stringify({ email, otp }),
      });

      const data = await readJsonSafe(res);
      if (!res.ok) throw new Error("OTP failed");

      setResetUid(data.uid);
      setResetToken(data.token);
      setMode("reset");
    } catch {
      setError("Invalid OTP");
    } finally {
      setBusy(false);
    }
  };

  const onReset = async (e) => {
    e.preventDefault();
    clearAlerts();

    if (newPassword !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    setBusy(true);
    try {
      const res = await csrfFetch("/api/users/password/reset/", {
        method: "POST",
        body: JSON.stringify({
          uid: resetUid,
          token: resetToken,
          new_password: newPassword,
        }),
      });

      const data = await readJsonSafe(res);
      if (!res.ok) throw new Error("Reset failed");

      setMessage("Password updated!");
      setMode("login");
    } catch {
      setError("Reset failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0a0f1c] text-white relative overflow-hidden">
      {/* Background decorations */}
      <div className="absolute top-[-10%] left-[-10%] w-96 h-96 bg-blue-600/20 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-96 h-96 bg-purple-600/20 rounded-full blur-[120px] pointer-events-none" />

      <div className="relative z-10 w-full max-w-md p-8 bg-white/[0.03] backdrop-blur-2xl border border-white/10 shadow-2xl rounded-3xl transition-all duration-500 hover:border-white/20">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-extrabold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent capitalize tracking-tight">
            {mode === "login" ? "Welcome Back" : mode === "signup" ? "Create Account" : mode === "forgot" ? "Reset Password" : mode}
          </h2>
          <p className="text-slate-400 mt-2 text-sm font-medium">
            {mode === "login" ? "Sign in to your account to continue" : "Fill in your details below"}
          </p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm font-medium animate-pulse">
            {error}
          </div>
        )}
        {message && (
          <div className="mb-6 p-4 bg-green-500/10 border border-green-500/20 rounded-xl text-green-400 text-sm font-medium">
            {message}
          </div>
        )}

        <div className="space-y-5">
          {mode === "login" && googleReady && (
            <a
              href={googleHref}
              onClick={(e) => { if (!googleReady) e.preventDefault(); }}
              className="group relative flex w-full items-center justify-center gap-3 rounded-xl bg-white/5 px-4 py-3.5 text-sm font-semibold text-white transition-all duration-300 hover:bg-white/10 hover:shadow-[0_0_20px_rgba(255,255,255,0.1)] border border-white/10 hover:border-white/20"
            >
              <svg className="w-5 h-5 transition-transform group-hover:scale-110" viewBox="0 0 24 24">
                <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
              </svg>
              Continue with Google
            </a>
          )}

          {mode === "login" && googleReady && (
            <div className="relative flex items-center py-2">
              <div className="flex-grow border-t border-white/10"></div>
              <span className="flex-shrink-0 px-4 text-xs font-medium text-slate-500 uppercase tracking-wider">Or</span>
              <div className="flex-grow border-t border-white/10"></div>
            </div>
          )}

          {mode === "login" && (
            <form onSubmit={onLogin} className="space-y-4">
              <div>
                <input
                  type="email"
                  placeholder="Email address"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-slate-900/50 border border-white/10 rounded-xl px-4 py-3.5 text-sm outline-none transition-all placeholder:text-slate-500 focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20"
                  required
                />
              </div>
              <div>
                <input
                  type="password"
                  placeholder="Password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-slate-900/50 border border-white/10 rounded-xl px-4 py-3.5 text-sm outline-none transition-all placeholder:text-slate-500 focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20"
                  required
                />
              </div>
              <button disabled={busy} className="relative w-full overflow-hidden rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 px-4 py-3.5 text-sm font-semibold text-white transition-all hover:scale-[1.02] hover:shadow-[0_0_20px_rgba(79,70,229,0.4)] active:scale-[0.98] disabled:opacity-70 disabled:hover:scale-100">
                <span className="relative z-10">{busy ? "Authenticating..." : "Sign In"}</span>
              </button>
            </form>
          )}

          {mode === "signup" && (
            <form onSubmit={onSignup} className="space-y-4">
              <input
                placeholder="Choose a Username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full bg-slate-900/50 border border-white/10 rounded-xl px-4 py-3.5 text-sm outline-none transition-all placeholder:text-slate-500 focus:border-purple-500/50 focus:ring-2 focus:ring-purple-500/20"
                required
              />
              <input
                type="email"
                placeholder="Email address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-slate-900/50 border border-white/10 rounded-xl px-4 py-3.5 text-sm outline-none transition-all placeholder:text-slate-500 focus:border-purple-500/50 focus:ring-2 focus:ring-purple-500/20"
                required
              />
              <input
                type="password"
                placeholder="Create Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-slate-900/50 border border-white/10 rounded-xl px-4 py-3.5 text-sm outline-none transition-all placeholder:text-slate-500 focus:border-purple-500/50 focus:ring-2 focus:ring-purple-500/20"
                required
              />
              <button disabled={busy} className="relative w-full overflow-hidden rounded-xl bg-gradient-to-r from-teal-500 to-emerald-600 px-4 py-3.5 text-sm font-semibold text-white transition-all hover:scale-[1.02] hover:shadow-[0_0_20px_rgba(16,185,129,0.4)] active:scale-[0.98] disabled:opacity-70 disabled:hover:scale-100">
                <span className="relative z-10">{busy ? "Creating account..." : "Sign Up"}</span>
              </button>
            </form>
          )}

          {mode === "forgot" && (
            <form onSubmit={onForgot} className="space-y-4">
              <p className="text-sm text-slate-400 pb-2">Enter your email to receive a password reset code.</p>
              <input
                type="email"
                placeholder="Email address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-slate-900/50 border border-white/10 rounded-xl px-4 py-3.5 text-sm outline-none transition-all placeholder:text-slate-500 focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20"
                required
              />
              <button disabled={busy} className="relative w-full overflow-hidden rounded-xl bg-gradient-to-r from-slate-700 to-slate-600 px-4 py-3.5 text-sm font-semibold text-white transition-all hover:scale-[1.02] hover:border-slate-500 active:scale-[0.98] disabled:opacity-70 disabled:hover:scale-100">
                <span className="relative z-10">{busy ? "Sending Code..." : "Send Reset Code"}</span>
              </button>
            </form>
          )}

          {mode === "otp" && (
            <form onSubmit={onVerifyOtp} className="space-y-4">
              <p className="text-sm text-slate-400 pb-2">Enter the verification code sent to your email.</p>
              <input
                placeholder="6-digit code"
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                className="w-full bg-slate-900/50 border border-white/10 rounded-xl px-4 py-3.5 text-sm outline-none tracking-widest text-center transition-all placeholder:text-slate-500 focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20"
                required
              />
              <button disabled={busy} className="relative w-full overflow-hidden rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 px-4 py-3.5 text-sm font-semibold text-white transition-all hover:scale-[1.02] hover:shadow-[0_0_20px_rgba(79,70,229,0.4)] active:scale-[0.98] disabled:opacity-70 disabled:hover:scale-100">
                <span className="relative z-10">{busy ? "Verifying..." : "Verify Code"}</span>
              </button>
            </form>
          )}

          {mode === "reset" && (
            <form onSubmit={onReset} className="space-y-4">
              <input
                type="password"
                placeholder="New Password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full bg-slate-900/50 border border-white/10 rounded-xl px-4 py-3.5 text-sm outline-none transition-all placeholder:text-slate-500 focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20"
                required
              />
              <input
                type="password"
                placeholder="Confirm Password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full bg-slate-900/50 border border-white/10 rounded-xl px-4 py-3.5 text-sm outline-none transition-all placeholder:text-slate-500 focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20"
                required
              />
              <button disabled={busy} className="relative w-full overflow-hidden rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 px-4 py-3.5 text-sm font-semibold text-white transition-all hover:scale-[1.02] hover:shadow-[0_0_20px_rgba(79,70,229,0.4)] active:scale-[0.98] disabled:opacity-70 disabled:hover:scale-100">
                <span className="relative z-10">{busy ? "Resetting..." : "Save New Password"}</span>
              </button>
            </form>
          )}
        </div>

        <div className="mt-8 flex items-center justify-center gap-4 text-sm font-medium text-slate-400">
          {mode !== "login" && (
            <button onClick={() => go("login")} className="hover:text-white transition-colors duration-200">
              Sign In
            </button>
          )}
          {mode !== "signup" && (
            <button onClick={() => go("signup")} className="hover:text-white transition-colors duration-200">
              Create Account
            </button>
          )}
          {mode === "login" && (
            <>
              <span className="w-1 h-1 rounded-full bg-slate-700"></span>
              <button onClick={() => go("forgot")} className="hover:text-white transition-colors duration-200">
                Forgot password?
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default LoginPage;