import { create } from "zustand";
import { api } from "./api";
import type { AppState, ChatMessage, QueryResponse, TableInfo } from "./types";

interface Actions {
  init: () => Promise<void>;
  setActiveTable: (table: string) => Promise<void>;
  sendMessage: (text: string) => Promise<void>;
  uploadFile: (file: File) => Promise<void>;
  clearChat: () => void;
  setSidebarOpen: (open: boolean) => void;
  setSchemaOpen: (open: boolean) => void;
  setUploadOpen: (open: boolean) => void;
}

function makeId() {
  return Math.random().toString(36).slice(2, 9);
}

function nowTime() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export const useStore = create<AppState & Actions>((set, get) => ({
  // ── State ────────────────────────────────────────────────────────────────
  tables: [],
  activeTable: null,
  messages: [],
  isLoading: false,
  lastResult: null,
  sidebarOpen: true,
  schemaOpen: false,
  uploadOpen: false,

  // ── Actions ──────────────────────────────────────────────────────────────
  init: async () => {
    try {
      const [tablesResp, activeResp] = await Promise.all([
        api.getTables(),
        api.getActiveTable(),
      ]);
      set({ tables: tablesResp.tables, activeTable: activeResp });
    } catch {
      // Silent fail on startup
    }
  },

  setActiveTable: async (table) => {
    try {
      const info = await api.setActiveTable(table);
      const tablesResp = await api.getTables();
      set({ activeTable: info, tables: tablesResp.tables });
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      console.error("setActiveTable failed:", msg);
    }
  },

  sendMessage: async (text) => {
    const userMsg: ChatMessage = {
      id: makeId(),
      role: "user",
      text,
      time: nowTime(),
    };
    set((s) => ({ messages: [...s.messages, userMsg], isLoading: true }));

    try {
      const result: QueryResponse = await api.query(text);
      const botMsg: ChatMessage = {
        id: makeId(),
        role: "assistant",
        text: result.reply,
        time: nowTime(),
        result,
      };
      set((s) => ({
        messages: [...s.messages, botMsg],
        isLoading: false,
        lastResult: result,
      }));
    } catch (e: unknown) {
      const errText = e instanceof Error ? e.message : "Something went wrong.";
      const errMsg: ChatMessage = {
        id: makeId(),
        role: "assistant",
        text: `⚠️ ${errText}`,
        time: nowTime(),
      };
      set((s) => ({
        messages: [...s.messages, errMsg],
        isLoading: false,
      }));
    }
  },

  uploadFile: async (file) => {
    try {
      const info: TableInfo = await api.uploadCSV(file);
      const tablesResp = await api.getTables();
      set({ activeTable: info, tables: tablesResp.tables, uploadOpen: false });
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      throw new Error(msg);
    }
  },

  clearChat: () => set({ messages: [], lastResult: null }),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  setSchemaOpen: (open) => set({ schemaOpen: open }),
  setUploadOpen: (open) => set({ uploadOpen: open }),
}));
