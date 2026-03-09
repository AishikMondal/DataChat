"use client";

import type { Badge } from "@/lib/types";
import { cn } from "@/lib/utils";

interface Props {
  badges: Badge[];
}

const COLOR_MAP: Record<string, string> = {
  green: "bg-emerald-500/10 border-emerald-500/20 text-emerald-400",
  blue: "bg-blue-500/10 border-blue-500/20 text-blue-400",
  purple: "bg-violet-500/10 border-violet-500/20 text-violet-400",
  gray: "bg-white/[0.04] border-white/[0.09] text-white/40",
};

export function BadgeRow({ badges }: Props) {
  if (!badges.length) return null;
  return (
    <div className="flex flex-wrap gap-1.5">
      {badges.map((b, i) => (
        <span
          key={i}
          className={cn(
            "inline-flex items-center text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-md border",
            COLOR_MAP[b.color] || COLOR_MAP.gray
          )}
        >
          {b.label}
        </span>
      ))}
    </div>
  );
}
