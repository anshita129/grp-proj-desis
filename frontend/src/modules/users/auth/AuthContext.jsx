import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { csrfFetch, readJsonSafe } from "./http";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/users/me/", { credentials: "include" });
      if (!res.ok) {
        setUser(null);
        return null;
      }
      const data = await readJsonSafe(res);
      setUser(data || null);
      return data || null;
    } catch {
      setUser(null);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await fetch("/api/users/csrf/", { credentials: "include" });
      await csrfFetch("/api/users/logout/", { method: "POST" });
    } finally {
      setUser(null);
    }
  }, []);

  useEffect(() => {
    const t = setTimeout(() => {
      refresh();
    }, 0);
    return () => clearTimeout(t);
  }, [refresh]);

  const value = useMemo(() => ({ user, loading, refresh, logout, setUser }), [user, loading, refresh, logout]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

