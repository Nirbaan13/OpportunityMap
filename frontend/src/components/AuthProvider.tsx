"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { api } from "@/lib/api";
import {
  clearStoredToken,
  getStoredToken,
  setStoredToken,
} from "@/lib/auth-storage";
import { ApiError, type User } from "@/types/api";

type AuthContextValue = {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<User>;
  register: (email: string, password: string) => Promise<User>;
  logout: () => void;
  refreshUser: () => Promise<User | null>;
  updateUser: (user: User) => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    const stored = getStoredToken();
    if (!stored) {
      setUser(null);
      setToken(null);
      return null;
    }

    try {
      const me = await api.me(stored);
      setToken(stored);
      setUser(me);
      return me;
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        clearStoredToken();
        setToken(null);
        setUser(null);
        return null;
      }
      throw error;
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    const stored = getStoredToken();
    if (!stored) {
      setUser(null);
      setToken(null);
      setLoading(false);
      return;
    }

    (async () => {
      try {
        const me = await api.me(stored);
        if (cancelled) return;
        setToken(stored);
        setUser(me);
      } catch (error) {
        if (cancelled) return;
        if (error instanceof ApiError && error.status === 401) {
          clearStoredToken();
          setToken(null);
          setUser(null);
        } else {
          setToken(stored);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const { access_token } = await api.login(email, password);
    setStoredToken(access_token);
    setToken(access_token);
    const me = await api.me(access_token);
    setUser(me);
    return me;
  }, []);

  const register = useCallback(async (email: string, password: string) => {
    await api.register(email, password);
    return login(email, password);
  }, [login]);

  const logout = useCallback(() => {
    clearStoredToken();
    setToken(null);
    setUser(null);
  }, []);

  const updateUser = useCallback((nextUser: User) => {
    setUser(nextUser);
  }, []);

  const value = useMemo(
    () => ({ user, token, loading, login, register, logout, refreshUser, updateUser }),
    [user, token, loading, login, register, logout, refreshUser, updateUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}
