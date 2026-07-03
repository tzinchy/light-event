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
import { meApiV1AuthMeGet, type MeOut } from "@light-event/shared-types";
import { clearTokens, getTokens, saveTokens } from "@/lib/api";

type AuthState = {
  me: MeOut | null;
  loading: boolean;
  login: (access: string, refresh: string) => Promise<void>;
  logout: () => void;
  refreshMe: () => Promise<void>;
};

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [me, setMe] = useState<MeOut | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshMe = useCallback(async () => {
    if (!getTokens()) {
      setMe(null);
      setLoading(false);
      return;
    }
    const { data } = await meApiV1AuthMeGet();
    setMe(data ?? null);
    setLoading(false);
  }, []);

  useEffect(() => {
    void refreshMe();
  }, [refreshMe]);

  const login = useCallback(
    async (access: string, refresh: string) => {
      saveTokens(access, refresh);
      await refreshMe();
    },
    [refreshMe],
  );

  const logout = useCallback(() => {
    clearTokens();
    setMe(null);
  }, []);

  const value = useMemo(
    () => ({ me, loading, login, logout, refreshMe }),
    [me, loading, login, logout, refreshMe],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth вызывается только внутри AuthProvider");
  return ctx;
}
