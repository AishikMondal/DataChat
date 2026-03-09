"use client";

import { useStore } from "@/lib/store";
import { PlotlyChart } from "./PlotlyChart";
import { KpiCards } from "./KpiCards";
import { SqlBlock } from "./SqlBlock";
import { BadgeRow } from "./BadgeRow";
import { DataTable } from "./DataTable";
import {
  BarChart3,
  BarChart2,
  BarChartHorizontal,
  PieChart,
  TrendingUp,
  ScatterChart,
  Lightbulb,
  Table2,
  AlertTriangle,
  Info,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";
import type { QueryResponse, PlotlyFigure } from "@/lib/types";

export function DashboardPanel() {
  const { lastResult, activeTable } = useStore();

  return (
    <div className="flex flex-col h-full overflow-hidden bg-[#0c1020]">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-white/[0.05] shrink-0">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-violet-400" />
          <h2 className="text-sm font-semibold text-white/80">Analysis</h2>
          {activeTable && (
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/[0.04] border border-white/[0.08] text-white/30 font-mono">
              {activeTable.table}
            </span>
          )}
        </div>
        {lastResult && (
          <span className="text-[10px] text-white/25 font-mono">
            {lastResult.type}
          </span>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
        {!lastResult ? (
          <EmptyState />
        ) : (
          <ResultView result={lastResult} />
        )}
      </div>
    </div>
  );
}

// ── Empty state ─────────────────────────────────────────────────────────────
function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center gap-6 py-16">
      <div className="relative">
        <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-indigo-600/10 to-violet-600/10 border border-indigo-500/15 flex items-center justify-center">
          <BarChart3 className="w-9 h-9 text-indigo-400/60" />
        </div>
        <div className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-violet-500/20 border border-violet-500/30 flex items-center justify-center">
          <span className="text-[8px] text-violet-300">AI</span>
        </div>
      </div>
      <div className="max-w-xs">
        <p className="text-white/50 font-medium text-sm mb-2">
          Ask a question to see analysis
        </p>
        <p className="text-white/20 text-xs leading-relaxed">
          Charts, KPI metrics, data tables, and AI-generated insights will appear here after you chat.
        </p>
      </div>
    </div>
  );
}

// ── Result view ─────────────────────────────────────────────────────────────
function ResultView({ result }: { result: QueryResponse }) {
  const [tableExpanded, setTableExpanded] = useState(false);

  const type = result.type;

  return (
    <div className="space-y-4 pb-2">
      {/* Title */}
      {result.title && (
        <h3 className="text-base font-semibold text-white/80">{result.title}</h3>
      )}

      {/* Badges */}
      {result.badges && result.badges.length > 0 && (
        <BadgeRow badges={result.badges} />
      )}

      {/* KPI Cards */}
      {result.kpi_cards && result.kpi_cards.length > 0 && (
        <KpiCards cards={result.kpi_cards} />
      )}

      {/* Warning: empty result */}
      {result.empty && (
        <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-yellow-500/5 border border-yellow-500/15 text-yellow-300/80 text-sm">
          <AlertTriangle className="w-4 h-4 shrink-0 text-yellow-400" />
          Query ran successfully but returned no rows. Check filter values.
        </div>
      )}

      {/* Summary insight */}
      {result.summary && (
        <InsightBox text={result.summary} />
      )}

      {/* Highlights */}
      {result.highlights && result.highlights.length > 0 && (
        <div className="space-y-1">
          {result.highlights.map((h, i) => (
            <p key={i} className="text-xs text-white/45 leading-relaxed">
              {h.replace(/\*\*/g, "")}
            </p>
          ))}
        </div>
      )}

      {/* Schema view */}
      {type === "schema" && result.schema && (
        <SchemaView schema={result.schema} rowCount={result.row_count} />
      )}

      {/* Column metadata */}
      {(type === "column_type" || type === "unique_count" || type === "null_count") && (
        <MetaCard result={result} />
      )}

      {/* Chart — multi-viz tabs or single */}
      {result.charts && result.charts.length > 1 ? (
        <ChartTabs charts={result.charts} />
      ) : result.chart ? (
        <div className="rounded-xl border border-white/[0.06] overflow-hidden bg-white/[0.015] p-2">
          <PlotlyChart figure={result.chart} className="h-72" />
        </div>
      ) : null}

      {/* SQL */}
      {result.sql && <SqlBlock sql={result.sql} />}

      {/* Data table (collapsible) */}
      {result.table && (
        <div>
          <button
            onClick={() => setTableExpanded((e) => !e)}
            className="flex items-center gap-2 text-xs text-white/40 hover:text-white/60 transition-colors mb-2"
          >
            <Table2 className="w-3.5 h-3.5" />
            {tableExpanded ? "Hide" : "Show"} Data Table ({result.table.rows.length} rows)
            {tableExpanded ? (
              <ChevronUp className="w-3.5 h-3.5" />
            ) : (
              <ChevronDown className="w-3.5 h-3.5" />
            )}
          </button>
          {tableExpanded && <DataTable data={result.table} />}
        </div>
      )}

      {/* For top_values, schema, sample_values — always show table inline */}
      {(type === "top_values" || type === "sample_values" || type === "schema") &&
        result.table &&
        !tableExpanded && (
          <DataTable data={result.table} />
        )}
    </div>
  );
}

// ── Insight box ──────────────────────────────────────────────────────────────
function InsightBox({ text }: { text: string }) {
  return (
    <div className="flex gap-3 items-start px-4 py-3 rounded-xl bg-emerald-500/5 border-l-2 border-emerald-500/40 border border-emerald-500/10">
      <Lightbulb className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" />
      <p className="text-sm text-emerald-200/80 leading-relaxed">{text}</p>
    </div>
  );
}

// ── Schema view ──────────────────────────────────────────────────────────────
function SchemaView({ schema, rowCount }: { schema: { name: string; type: string }[]; rowCount?: number }) {
  return (
    <div className="rounded-xl border border-white/[0.06] overflow-hidden">
      <div className="flex items-center gap-3 px-4 py-2.5 bg-white/[0.02] border-b border-white/[0.05]">
        <Info className="w-3.5 h-3.5 text-blue-400" />
        <span className="text-xs font-semibold text-white/50">
          Schema — {rowCount?.toLocaleString()} rows · {schema.length} columns
        </span>
      </div>
      <div className="divide-y divide-white/[0.03]">
        {schema.map((col) => (
          <div
            key={col.name}
            className="flex items-center justify-between px-4 py-2 hover:bg-white/[0.02] transition-colors"
          >
            <span className="text-xs font-mono text-white/70">{col.name}</span>
            <span className="text-[10px] font-semibold uppercase tracking-widest text-white/30 bg-white/[0.04] px-2 py-0.5 rounded">
              {col.type}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Meta card ────────────────────────────────────────────────────────────────
function MetaCard({ result }: { result: QueryResponse }) {
  const entries: { label: string; value: string | number }[] = [];
  if (result.column_name) entries.push({ label: "Column", value: result.column_name });
  if (result.dtype) entries.push({ label: "Datatype", value: result.dtype });
  if (result.unique_count !== undefined) entries.push({ label: "Unique values", value: result.unique_count.toLocaleString() });
  if (result.null_count !== undefined) entries.push({ label: "Null values", value: result.null_count.toLocaleString() });

  return (
    <div className="grid grid-cols-2 gap-3">
      {entries.map((e) => (
        <div
          key={e.label}
          className="rounded-xl bg-white/[0.03] border border-white/[0.06] px-4 py-3"
        >
          <p className="text-[10px] font-semibold uppercase tracking-widest text-white/30 mb-1">
            {e.label}
          </p>
          <p className="text-sm font-semibold text-white/80 font-mono">{e.value}</p>
        </div>
      ))}
    </div>
  );
}

// ── Chart type icons & labels ─────────────────────────────────────────────────
const CHART_META: Record<string, { label: string; Icon: React.FC<{ className?: string }> }> = {
  bar: { label: "Bar", Icon: BarChart3 },
  horizontal_bar: { label: "H-Bar", Icon: BarChartHorizontal },
  pie: { label: "Pie", Icon: PieChart },
  line: { label: "Line", Icon: TrendingUp },
  grouped_bar: { label: "Grouped", Icon: BarChart2 },
  scatter: { label: "Scatter", Icon: ScatterChart },
  histogram: { label: "Histogram", Icon: BarChart3 },
};

// ── Multi-viz tabbed chart panel ──────────────────────────────────────────────
function ChartTabs({ charts }: { charts: Array<{ type: string; figure: PlotlyFigure }> }) {
  const [active, setActive] = useState(0);
  const current = charts[active];

  return (
    <div className="rounded-xl border border-white/[0.06] overflow-hidden bg-white/[0.015]">
      {/* Tab bar */}
      <div className="flex items-center gap-1 px-3 pt-2.5 pb-0 border-b border-white/[0.05]">
        {charts.map((c, i) => {
          const meta = CHART_META[c.type] ?? { label: c.type, Icon: BarChart3 };
          const Icon = meta.Icon;
          const isActive = i === active;
          return (
            <button
              key={c.type}
              onClick={() => setActive(i)}
              className={cn(
                "flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-medium rounded-t-md transition-all",
                "border border-transparent border-b-0",
                isActive
                  ? "bg-[#0c1020] text-indigo-300 border-white/[0.08] border-b-[#0c1020]"
                  : "text-white/35 hover:text-white/60 hover:bg-white/[0.04]"
              )}
            >
              <Icon className="w-3.5 h-3.5" />
              {meta.label}
            </button>
          );
        })}
        <div className="ml-auto pr-2 text-[10px] text-white/20 font-mono">
          {active + 1} / {charts.length}
        </div>
      </div>

      {/* Chart content */}
      <div className="p-2">
        <PlotlyChart figure={current.figure} className="h-72" />
      </div>
    </div>
  );
}
