"use client";

import dynamic from "next/dynamic";
import { useMemo } from "react";
import { buildOption } from "@/lib/chartSpec";
import type { Column, Row } from "@/lib/types";

const ReactECharts = dynamic(() => import("echarts-for-react"), {
  ssr: false,
  loading: () => <div className="h-[280px]" />,
});

export default function Chart({ columns, rows, viz }: { columns: Column[]; rows: Row[]; viz: "line" | "bar" }) {
  const option = useMemo(() => {
    const css = typeof window === "undefined"
      ? { ink: "#101a2c", mute: "#5b6776", line: "#cdd5cb" }
      : (() => {
          const s = getComputedStyle(document.documentElement);
          return { ink: s.getPropertyValue("--ink").trim(), mute: s.getPropertyValue("--mute").trim(), line: s.getPropertyValue("--line").trim() };
        })();
    return buildOption(columns, rows, viz, css);
  }, [columns, rows, viz]);

  return <ReactECharts option={option} style={{ height: 280, width: "100%" }} notMerge />;
}
