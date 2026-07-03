"use client";

import { client } from "@light-event/shared-types/client";

const ACCESS_KEY = "le_access_token";
const REFRESH_KEY = "le_refresh_token";

export function getTokens() {
  if (typeof window === "undefined") return null;
  const access = localStorage.getItem(ACCESS_KEY);
  const refresh = localStorage.getItem(REFRESH_KEY);
  return access && refresh ? { access, refresh } : null;
}

export function saveTokens(access: string, refresh: string) {
  localStorage.setItem(ACCESS_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

client.setConfig({
  baseUrl: "", // same-origin: dev — rewrites на uvicorn, prod — nginx
  auth: () => getTokens()?.access,
});

let refreshing: Promise<boolean> | null = null;

async function tryRefresh(): Promise<boolean> {
  refreshing ??= (async () => {
    const tokens = getTokens();
    if (!tokens) return false;
    const resp = await fetch("/api/v1/auth/refresh", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: tokens.refresh }),
    });
    if (!resp.ok) {
      clearTokens();
      return false;
    }
    const data = await resp.json();
    saveTokens(data.access_token, data.refresh_token);
    return true;
  })().finally(() => {
    refreshing = null;
  });
  return refreshing;
}

// 401 → одна попытка refresh и повтор запроса; иначе отдаём ответ как есть
client.interceptors.response.use(async (response, request) => {
  if (response.status !== 401 || !getTokens()) return response;
  if (request.url.includes("/auth/")) return response;
  if (!(await tryRefresh())) return response;
  const retried = new Request(request, {
    headers: new Headers(request.headers),
  });
  retried.headers.set("Authorization", `Bearer ${getTokens()?.access}`);
  return fetch(retried);
});

export { client };
