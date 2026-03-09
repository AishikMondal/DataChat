"use client";

import { useState } from "react";
import { Copy, Check } from "lucide-react";
import { cn } from "@/lib/utils";

interface Props {
  sql: string;
}

export function SqlBlock({ sql }: Props) {
  const [copied, setCopied] = useState(false);

  const copy = () => {
    navigator.clipboard.writeText(sql).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  };

  return (
    <div className="relative group rounded-xl bg-black/25 border border-white/[0.06] overflow-hidden">
      <div className="flex items-center justify-between px-3 py-1.5 border-b border-white/[0.05] bg-white/[0.02]">
        <span className="text-[10px] font-semibold uppercase tracking-widest text-white/30">
          SQL
        </span>
        <button
          onClick={copy}
          className="flex items-center gap-1 text-[10px] text-white/30 hover:text-white/60 transition-colors"
        >
          {copied ? (
            <>
              <Check className="w-3 h-3 text-emerald-400" />
              <span className="text-emerald-400">Copied</span>
            </>
          ) : (
            <>
              <Copy className="w-3 h-3" />
              Copy
            </>
          )}
        </button>
      </div>
      <pre className="px-4 py-3 text-xs font-mono text-indigo-300/90 overflow-x-auto leading-relaxed whitespace-pre-wrap break-all">
        {sql}
      </pre>
    </div>
  );
}
