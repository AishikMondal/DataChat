// ── API Response Types ─────────────────────────────────────────────────────

export interface TableInfo {
  table: string;
  row_count: number;
  columns: string[];
  schema: SchemaColumn[];
}

export interface SchemaColumn {
  name: string;
  type: string;
}

export interface Badge {
  label: string;
  color: "green" | "blue" | "purple" | "gray";
}

export interface KpiCard {
  label: string;
  value: string;
  raw: number | null;
}

export interface TableData {
  columns: string[];
  rows: (string | number | null)[][];
}

export interface PlotlyFigure {
  data: object[];
  layout: object;
  [key: string]: unknown;
}

export interface QueryResponse {
  type:
    | "dashboard"
    | "schema"
    | "sample_values"
    | "column_type"
    | "unique_count"
    | "null_count"
    | "top_values";
  reply: string;
  // dashboard
  sql?: string;
  badges?: Badge[];
  kpi_cards?: KpiCard[];
  chart?: PlotlyFigure | null;
  chart_type?: string;
  charts?: Array<{ type: string; figure: PlotlyFigure }> | null;
  summary?: string | null;
  highlights?: string[];
  table?: TableData | null;
  empty?: boolean;
  title?: string;
  // schema
  row_count?: number;
  schema?: SchemaColumn[];
  // metadata
  column_name?: string;
  dtype?: string;
  unique_count?: number;
  null_count?: number;
}

// ── Chat Types ─────────────────────────────────────────────────────────────

export type MessageRole = "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  text: string;
  time: string;
  result?: QueryResponse;
}

// ── App State ──────────────────────────────────────────────────────────────

export interface AppState {
  // Data
  tables: string[];
  activeTable: TableInfo | null;
  // Chat
  messages: ChatMessage[];
  isLoading: boolean;
  // Dashboard
  lastResult: QueryResponse | null;
  // UI
  sidebarOpen: boolean;
  schemaOpen: boolean;
  uploadOpen: boolean;
}
