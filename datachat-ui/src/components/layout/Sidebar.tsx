"use client";

import { useRef, useState } from "react";
import {
  Database,
  Upload,
  ChevronRight,
  MessageSquare,
  BarChart3,
  Sparkles,
  Table2,
  X,
  PanelLeftClose,
  PanelLeftOpen,
  Trash2,
} from "lucide-react";
import { useStore } from "@/lib/store";
import { cn } from "@/lib/utils";

const QUICK_PROMPTS = [
  "What columns are in this dataset?",
  "Show top 10 rows",
  "How many rows are there?",
  "Show null counts for all columns",
  "What are the unique values?",
];

export function Sidebar() {
  const {
    tables,
    activeTable,
    setActiveTable,
    clearChat,
    setSidebarOpen,
    sidebarOpen,
    setUploadOpen,
    sendMessage,
  } = useStore();

  return (
    <aside
      className={cn(
        "flex flex-col h-full bg-[#0a0d1a] border-r border-white/[0.05] transition-all duration-300",
        sidebarOpen ? "w-64" : "w-14"
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-4 border-b border-white/[0.05]">
        {sidebarOpen && (
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-indigo-500 to-blue-500 flex items-center justify-center">
              <BarChart3 className="w-4 h-4 text-white" />
            </div>
            <span className="text-sm font-semibold text-white/90 tracking-tight">
              DataChat
            </span>
          </div>
        )}
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-1 rounded-md text-white/40 hover:text-white/70 hover:bg-white/[0.05] transition-colors"
        >
          {sidebarOpen ? (
            <PanelLeftClose className="w-4 h-4" />
          ) : (
            <PanelLeftOpen className="w-4 h-4" />
          )}
        </button>
      </div>

      {/* Datasets */}
      <div className="flex-1 overflow-y-auto px-2 py-3 space-y-4">
        {sidebarOpen && (
          <>
            {/* Upload button */}
            <button
              onClick={() => setUploadOpen(true)}
              className="w-full flex items-center gap-2 px-3 py-2 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 border border-indigo-500/20 hover:border-indigo-500/40 text-indigo-300 text-xs font-medium transition-all group"
            >
              <Upload className="w-3.5 h-3.5" />
              Upload CSV
            </button>

            {/* Dataset list */}
            <div>
              <p className="text-[10px] font-semibold text-white/30 uppercase tracking-widest px-1 mb-2">
                Datasets
              </p>
              <div className="space-y-0.5">
                {tables.map((t) => {
                  const isActive = t === activeTable?.table;
                  return (
                    <button
                      key={t}
                      onClick={() => setActiveTable(t)}
                      className={cn(
                        "w-full flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium transition-all text-left",
                        isActive
                          ? "bg-indigo-600/20 text-indigo-300 border border-indigo-500/25"
                          : "text-white/50 hover:text-white/80 hover:bg-white/[0.04]"
                      )}
                    >
                      <Database className="w-3.5 h-3.5 shrink-0" />
                      <span className="truncate">{t}</span>
                      {isActive && (
                        <ChevronRight className="w-3 h-3 ml-auto shrink-0 text-indigo-400" />
                      )}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Active table info */}
            {activeTable && (
              <div className="rounded-lg bg-white/[0.03] border border-white/[0.05] p-3">
                <p className="text-[10px] font-semibold text-white/30 uppercase tracking-widest mb-2">
                  Active Table
                </p>
                <p className="text-xs font-semibold text-white/80 truncate mb-1">
                  {activeTable.table}
                </p>
                <div className="flex gap-3 text-[10px] text-white/40">
                  <span>{activeTable.row_count?.toLocaleString()} rows</span>
                  <span>{activeTable.columns?.length} cols</span>
                </div>
              </div>
            )}

            {/* Quick prompts */}
            <div>
              <p className="text-[10px] font-semibold text-white/30 uppercase tracking-widest px-1 mb-2">
                Quick Prompts
              </p>
              <div className="space-y-0.5">
                {QUICK_PROMPTS.map((p) => (
                  <button
                    key={p}
                    onClick={() => sendMessage(p)}
                    className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-[11px] text-white/40 hover:text-white/70 hover:bg-white/[0.04] transition-all text-left group"
                  >
                    <Sparkles className="w-3 h-3 shrink-0 text-indigo-400/50 group-hover:text-indigo-400" />
                    <span className="truncate">{p}</span>
                  </button>
                ))}
              </div>
            </div>
          </>
        )}

        {/* Collapsed state icons */}
        {!sidebarOpen && (
          <div className="flex flex-col items-center gap-3 pt-1">
            <button
              onClick={() => setUploadOpen(true)}
              className="p-2 rounded-lg text-white/30 hover:text-indigo-400 hover:bg-indigo-600/10 transition-colors"
              title="Upload CSV"
            >
              <Upload className="w-4 h-4" />
            </button>
            <button
              className="p-2 rounded-lg text-white/30 hover:text-white/60 hover:bg-white/[0.05] transition-colors"
              title="Datasets"
              onClick={() => setSidebarOpen(true)}
            >
              <Database className="w-4 h-4" />
            </button>
            <button
              className="p-2 rounded-lg text-white/30 hover:text-white/60 hover:bg-white/[0.05] transition-colors"
              title="Quick prompts"
              onClick={() => setSidebarOpen(true)}
            >
              <Sparkles className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="border-t border-white/[0.05] px-2 py-2">
        <button
          onClick={clearChat}
          className={cn(
            "flex items-center gap-2 px-3 py-2 rounded-lg text-xs text-white/30 hover:text-red-400 hover:bg-red-500/5 transition-all w-full",
            !sidebarOpen && "justify-center"
          )}
          title="Clear chat"
        >
          <Trash2 className="w-3.5 h-3.5 shrink-0" />
          {sidebarOpen && "Clear chat"}
        </button>
      </div>
    </aside>
  );
}
