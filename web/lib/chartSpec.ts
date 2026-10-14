import type { EChartsOption } from "echarts";
import { formatValue, timeLabel } from "./format";
import type { Column, Row } from "./types";

export type Viz = "kpi" | "line" | "bar" | "table";

const PALETTE = ["#2147d6", "#b8243f", "#d49a1c", "#168a73", "#7a4fc4", "#4b5a6b"];

/** Dynamic visualization rule: time series -> line, categories -> bar, single value -> KPI, otherwise table. */
export function pickViz(columns: Column[], rows: Row[]): Viz {
  const measures = columns.filter((c) => c.kind === "measure");
  const time = columns.find((c) => c.kind === "time");
  const dims = columns.filter((c) => c.kind === "dimension");
  if (!rows.length || !measures.length) return "table";
  if (time) {
    const buckets = new Set(rows.map((r) => r[time.key])).size;
    if (buckets > 1) return dims.length <= 1 ? "line" : "table";
    if (dims.length === 0) return "kpi";
    return dims.length <= 2 ? "bar" : "table";
  }
  if (dims.length === 0) return rows.length === 1 ? "kpi" : "table";
  if (dims.length <= 2 && rows.length <= 40) return "bar";
  return "table";
}

function axisFormatter(format?: string | null) {
  return (v: number) => formatValue(v, { key: "", label: "", kind: "measure", format }, true);
}

export function buildOption(columns: Column[], rows: Row[], viz: "line" | "bar", css: { ink: string; mute: string; line: string }): EChartsOption {
  const measures = columns.filter((c) => c.kind === "measure");
  const time = columns.find((c) => c.kind === "time");
  const dims = columns.filter((c) => c.kind === "dimension");

  const xCol = viz === "line" && time ? time : dims[0];
  const seriesCol = viz === "line" ? dims[0] : time && dims.length === 1 ? undefined : dims[1];
  const xRaw: string[] = [];
  rows.forEach((r) => { const x = String(r[xCol.key]); if (!xRaw.includes(x)) xRaw.push(x); });
  if (xCol.kind === "time") xRaw.sort();
  else if (!seriesCol) {
    const m0 = measures[0].key;
    xRaw.sort((a, b) => Number(rows.find((r) => String(r[xCol.key]) === b)?.[m0] ?? 0) - Number(rows.find((r) => String(r[xCol.key]) === a)?.[m0] ?? 0));
  }
  const seriesValues = seriesCol ? Array.from(new Set(rows.map((r) => String(r[seriesCol.key])))) : [null];

  const hasPercent = measures.some((m) => m.format === "percent");
  const hasOther = measures.some((m) => m.format !== "percent");
  const dual = hasPercent && hasOther;

  const series: NonNullable<EChartsOption["series"]> = [];
  measures.forEach((m) => {
    seriesValues.forEach((sv) => {
      const data = xRaw.map((x) => {
        const row = rows.find((r) => String(r[xCol.key]) === x && (sv === null || String(r[seriesCol!.key]) === sv));
        return (row?.[m.key] as number | null | undefined) ?? null;
      });
      const name = sv === null ? m.label : measures.length > 1 ? `${sv} - ${m.label}` : sv;
      (series as unknown[]).push({
        name, type: viz, data, smooth: false, symbolSize: 7, barMaxWidth: 44,
        yAxisIndex: dual && m.format === "percent" ? 1 : 0,
        lineStyle: { width: 2.5 },
        tooltip: { valueFormatter: (v: unknown) => formatValue(v as number, m) },
      });
    });
  });

  const fmtLeft = axisFormatter(dual ? measures.find((m) => m.format !== "percent")?.format : measures[0].format);
  const axisText = { color: css.mute, fontSize: 12 };
  return {
    color: PALETTE,
    textStyle: { fontFamily: "inherit" },
    grid: { left: 8, right: dual ? 8 : 16, top: series.length > 1 ? 40 : 16, bottom: 4, containLabel: true },
    legend: series.length > 1 ? { top: 0, left: 0, textStyle: { color: css.ink } } : undefined,
    tooltip: { trigger: "axis", backgroundColor: "#fbfcf9", borderColor: css.line, textStyle: { color: css.ink } },
    xAxis: {
      type: "category",
      data: xRaw.map((x) => (xCol.kind === "time" ? timeLabel(x, xCol.granularity) : x)),
      axisLine: { lineStyle: { color: css.line } }, axisTick: { show: false }, axisLabel: { ...axisText, hideOverlap: true },
    },
    yAxis: [
      { type: "value", axisLabel: { ...axisText, formatter: fmtLeft }, splitLine: { lineStyle: { color: css.line } } },
      ...(dual ? [{ type: "value" as const, axisLabel: { ...axisText, formatter: axisFormatter("percent") }, splitLine: { show: false } }] : []),
    ],
    series,
  };
}
