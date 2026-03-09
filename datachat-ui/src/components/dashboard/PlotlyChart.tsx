"use client";

import dynamic from "next/dynamic";
import type { PlotlyFigure } from "@/lib/types";

// Dynamically import Plotly (client-only)
const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface Props {
  figure: PlotlyFigure;
  className?: string;
}

export function PlotlyChart({ figure, className }: Props) {
  return (
    <div className={className}>
      <Plot
        data={figure.data as Plotly.Data[]}
        layout={{
          ...(figure.layout as Partial<Plotly.Layout>),
          autosize: true,
          font: { family: "Inter, sans-serif", color: "#cbd5e1", size: 12 },
        }}
        config={{
          displaylogo: false,
          responsive: true,
          toImageButtonOptions: {
            format: "png",
            filename: "datachat_chart",
            height: 600,
            width: 1000,
            scale: 2,
          },
        }}
        style={{ width: "100%", height: "100%" }}
        useResizeHandler
      />
    </div>
  );
}
