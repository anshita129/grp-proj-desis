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
    fetch("/api/users/csrf/", { credentials: "include" }).catch(() => {});
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
      navigate("/portfolio");
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
      navigate("/portfolio");
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
    <div className="min-h-screen flex items-center justify-center bg-slate-950 text-white">
      <div className="bg-slate-900 p-6 rounded-xl w-full max-w-md">
        <h2 className="text-xl font-bold mb-4 capitalize">{mode}</h2>

        {error && <p className="text-red-400">{error}</p>}
        {message && <p className="text-green-400">{message}</p>}

        {mode === "login" && (
          <form onSubmit={onLogin}>
            <input
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full mb-2 p-2"
            />
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full mb-2 p-2"
            />
            <button className="bg-blue-600 w-full p-2">Login</button>
          </form>
        )}

        {mode === "signup" && (
          <form onSubmit={onSignup}>
            <input
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full mb-2 p-2"
            />
            <input
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full mb-2 p-2"
            />
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full mb-2 p-2"
            />
            <button className="bg-green-600 w-full p-2">Signup</button>
          </form>
        )}

        <div className="mt-4 flex justify-between text-sm">
          <button onClick={() => go("signup")}>Signup</button>
          <button onClick={() => go("login")}>Login</button>
          <button onClick={() => go("forgot")}>Forgot</button>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;