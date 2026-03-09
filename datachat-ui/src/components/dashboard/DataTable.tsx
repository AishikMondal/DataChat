"use client";

import { useState } from "react";
import type { TableData } from "@/lib/types";
import { ChevronDown, ChevronUp, ChevronsUpDown, Table2 } from "lucide-react";

interface Props {
  data: TableData;
  title?: string;
}

export function DataTable({ data, title }: Props) {
  const [sortCol, setSortCol] = useState<number | null>(null);
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");
  const [page, setPage] = useState(0);
  const PAGE_SIZE = 25;

  const toggleSort = (colIdx: number) => {
    if (sortCol === colIdx) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortCol(colIdx);
      setSortDir("asc");
    }
    setPage(0);
  };

  const sortedRows = [...data.rows].sort((a, b) => {
    if (sortCol === null) return 0;
    const av = a[sortCol];
    const bv = b[sortCol];
    if (av === null) return 1;
    if (bv === null) return -1;
    const cmp = av < bv ? -1 : av > bv ? 1 : 0;
    return sortDir === "asc" ? cmp : -cmp;
  });

  const totalPages = Math.ceil(sortedRows.length / PAGE_SIZE);
  const pageRows = sortedRows.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  return (
    <div className="rounded-xl border border-white/[0.06] overflow-hidden bg-white/[0.015]">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-white/[0.06] bg-white/[0.02]">
        <div className="flex items-center gap-2">
          <Table2 className="w-3.5 h-3.5 text-white/30" />
          <span className="text-xs font-semibold text-white/50">
            {title || "Data Table"}
          </span>
          <span className="text-[10px] text-white/25 font-mono">
            ({data.rows.length} rows × {data.columns.length} cols)
          </span>
        </div>
        {totalPages > 1 && (
          <div className="flex items-center gap-2 text-[10px] text-white/30">
            <button
              disabled={page === 0}
              onClick={() => setPage((p) => p - 1)}
              className="px-2 py-0.5 rounded hover:bg-white/[0.06] disabled:opacity-30 transition-colors"
            >
              ← Prev
            </button>
            <span>
              {page + 1} / {totalPages}
            </span>
            <button
              disabled={page >= totalPages - 1}
              onClick={() => setPage((p) => p + 1)}
              className="px-2 py-0.5 rounded hover:bg-white/[0.06] disabled:opacity-30 transition-colors"
            >
              Next →
            </button>
          </div>
        )}
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-xs border-collapse">
          <thead>
            <tr className="border-b border-white/[0.05]">
              {data.columns.map((col, i) => (
                <th
                  key={col}
                  onClick={() => toggleSort(i)}
                  className="text-left px-4 py-2.5 text-[10px] font-semibold uppercase tracking-widest text-white/35 cursor-pointer hover:text-white/60 hover:bg-white/[0.03] transition-colors select-none whitespace-nowrap"
                >
                  <span className="flex items-center gap-1">
                    {col}
                    {sortCol === i ? (
                      sortDir === "asc" ? (
                        <ChevronUp className="w-3 h-3 text-indigo-400" />
                      ) : (
                        <ChevronDown className="w-3 h-3 text-indigo-400" />
                      )
                    ) : (
                      <ChevronsUpDown className="w-3 h-3 opacity-20" />
                    )}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pageRows.map((row, ri) => (
              <tr
                key={ri}
                className="border-b border-white/[0.03] hover:bg-white/[0.025] transition-colors"
              >
                {row.map((cell, ci) => (
                  <td
                    key={ci}
                    className="px-4 py-2 text-white/60 font-mono whitespace-nowrap max-w-[200px] overflow-hidden text-ellipsis"
                  >
                    {cell === null ? (
                      <span className="text-white/20 italic">null</span>
                    ) : (
                      String(cell)
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
