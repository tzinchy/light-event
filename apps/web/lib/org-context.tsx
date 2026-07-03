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
import {
  myCompaniesApiV1CompaniesMyGet,
  type MyCompanyOut,
} from "@light-event/shared-types";
import { useAuth } from "@/lib/auth-context";

type OrgState = {
  loading: boolean;
  memberships: MyCompanyOut[];
  /** Активная компания (MVP: первая; переключатель появится с мультикомпаниями). */
  current: MyCompanyOut | null;
  reload: () => Promise<void>;
};

const OrgContext = createContext<OrgState | null>(null);

export function OrgProvider({ children }: { children: ReactNode }) {
  const { me } = useAuth();
  const [memberships, setMemberships] = useState<MyCompanyOut[]>([]);
  const [loading, setLoading] = useState(true);

  const reload = useCallback(async () => {
    if (!me) {
      setMemberships([]);
      setLoading(false);
      return;
    }
    const { data } = await myCompaniesApiV1CompaniesMyGet();
    setMemberships(data ?? []);
    setLoading(false);
  }, [me]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const value = useMemo(
    () => ({ loading, memberships, current: memberships[0] ?? null, reload }),
    [loading, memberships, reload],
  );

  return <OrgContext.Provider value={value}>{children}</OrgContext.Provider>;
}

export function useOrg(): OrgState {
  const ctx = useContext(OrgContext);
  if (!ctx) throw new Error("useOrg вызывается только внутри OrgProvider");
  return ctx;
}
