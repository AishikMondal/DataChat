"use client";

import { useStore } from "@/lib/store";
import { BarChart3, Wifi, WifiOff, Table2 } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export function Topbar() {
  const { activeTable } = useStore();
  const [connected, setConnected] = useState<boolean | null>(null);

  useEffect(() => {
    api
      .health()
      .then(() => setConnected(true))
      .catch(() => setConnected(false));
  }, []);

  return (
    <header className="flex items-center justify-between px-4 py-2.5 bg-[#080c18] border-b border-white/[0.05] shrink-0">
      {/* Logo */}
      <div className="flex items-center gap-2.5">
        <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-900/30">
          <BarChart3 className="w-3.5 h-3.5 text-white" />
        </div>
        <span className="text-sm font-bold tracking-tight bg-gradient-to-r from-indigo-300 to-blue-300 bg-clip-text text-transparent">
          DataChat
        </span>
        <span className="text-[10px] font-medium text-white/20 border border-white/[0.07] rounded px-1.5 py-0.5">
          v2.0
        </span>
      </div>

      {/* Center: active table */}
      {activeTable && (
        <div className="hidden md:flex items-center gap-2 text-xs text-white/40">
          <Table2 className="w-3.5 h-3.5 text-indigo-400/60" />
          <span className="font-mono">{activeTable.table}</span>
          <span className="text-white/20">·</span>
          <span>{activeTable.row_count?.toLocaleString()} rows</span>
          <span className="text-white/20">·</span>
          <span>{activeTable.columns?.length} cols</span>
        </div>
      )}

      {/* Right: status */}
      <div className="flex items-center gap-2 text-[10px] text-white/30 font-medium">
        {connected === null ? (
          <span className="animate-pulse">Connecting…</span>
        ) : connected ? (
          <>
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.6)]" />
            <span className="text-white/40">gemini-2.5-flash</span>
            <Wifi className="w-3 h-3 text-emerald-400/60" />
          </>
        ) : (
          <>
            <WifiOff className="w-3 h-3 text-red-400" />
            <span className="text-red-400/70">Backend offline</span>
          </>
        )}
      </div>
    </header>
  );
}
