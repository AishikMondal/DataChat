"use client";

import type { KpiCard } from "@/lib/types";
import { TrendingUp } from "lucide-react";
import { cn } from "@/lib/utils";

interface Props {
  cards: KpiCard[];
}

const GRADIENT_PAIRS = [
  ["from-indigo-600/10", "border-indigo-500/20", "text-indigo-300"],
  ["from-violet-600/10", "border-violet-500/20", "text-violet-300"],
  ["from-blue-600/10", "border-blue-500/20", "text-blue-300"],
  ["from-cyan-600/10", "border-cyan-500/20", "text-cyan-300"],
  ["from-emerald-600/10", "border-emerald-500/20", "text-emerald-300"],
];

export function KpiCards({ cards }: Props) {
  if (!cards.length) return null;
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
      {cards.map((card, i) => {
        const [bg, border, accent] = GRADIENT_PAIRS[i % GRADIENT_PAIRS.length];
        return (
          <div
            key={card.label + i}
            className={cn(
              "relative rounded-xl p-4 bg-gradient-to-br",
              bg,
              "bg-white/[0.02] border",
              border,
              "overflow-hidden group hover:scale-[1.01] transition-transform"
            )}
          >
            <div className="absolute inset-0 bg-gradient-to-br from-white/[0.01] to-transparent pointer-events-none" />
            <p className="text-[10px] font-semibold uppercase tracking-widest text-white/35 mb-2 truncate">
              {card.label}
            </p>
            <p
              className={cn(
                "text-2xl font-bold tracking-tight truncate",
                accent
              )}
            >
              {card.value}
            </p>
            {card.raw !== null && (
              <TrendingUp
                className={cn("absolute right-3 bottom-3 w-4 h-4 opacity-20 group-hover:opacity-40 transition-opacity", accent)}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
