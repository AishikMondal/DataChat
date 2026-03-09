import type { QueryResponse, TableInfo } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {}
    throw new Error(detail);
  }
  return res.json();
}

export const api = {
  health: () => request<{ status: string; model: string; api_key_configured: boolean }>("/api/health"),

  getTables: () => request<{ tables: string[] }>("/api/tables"),

  getActiveTable: () => request<TableInfo>("/api/tables/active"),

  setActiveTable: (table: string) =>
    request<TableInfo>("/api/tables/active", {
      method: "POST",
      body: JSON.stringify({ table }),
    }),

  getTableMetadata: (name: string) =>
    request<TableInfo>(`/api/tables/${name}/metadata`),

  uploadCSV: async (file: File): Promise<TableInfo> => {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${BASE}/api/upload`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `Upload failed: HTTP ${res.status}`);
    }
    return res.json();
  },

  query: (question: string) =>
    request<QueryResponse>("/api/query", {
      method: "POST",
      body: JSON.stringify({ question }),
    }),
};
