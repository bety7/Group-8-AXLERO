export type Row = Record<string, string | number | null>;

export type Column = {
  key: string;
  label: string;
  kind: "measure" | "dimension" | "time";
  format?: string | null;
  granularity?: string;
};

export type ToolResult = {
  ok: boolean;
  query?: Record<string, unknown>;
  sql?: string | null;
  params?: unknown[];
  columns?: Column[];
  rows?: Row[];
  notes?: string[];
  row_count?: number;
  elapsed_ms?: number;
  error?: string;
};

export type ToolArgs = {
  measures?: string[];
  dimensions?: string[];
  granularity?: string;
  date_range?: string | string[];
};

export type Part =
  | { type: "text"; text: string }
  | { type: "tool"; id: string; status: "running" | "done" | "error"; args?: ToolArgs; result?: ToolResult };

export type Message = { id: string; role: "user" | "assistant"; parts: Part[]; error?: string };

export type StreamEvent =
  | { type: "token"; text: string }
  | { type: "tool_start"; id: string; args: ToolArgs }
  | ({ type: "tool_result"; id: string } & ToolResult)
  | { type: "error"; message: string }
  | { type: "done" };

export type MetricInfo = { name: string; title: string; kind: "measure" | "dimension"; type: string; description: string };

export type Status = { online: boolean; semantic_layer?: string; llm_provider?: string; metrics: MetricInfo[] };
