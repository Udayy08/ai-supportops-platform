"use client";

import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from "recharts";
import type { TrendPoint } from "@/lib/types";

interface TrendChartProps {
  data: TrendPoint[];
  dataKey: keyof TrendPoint;
  title: string;
  color?: string;
  isPercentage?: boolean;
}

export function TrendChart({ data, dataKey, title, color = "#3b82f6", isPercentage = false }: TrendChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="h-[250px] w-full flex items-center justify-center text-sm text-muted-foreground border rounded-lg bg-card/50">
        No trend data available
      </div>
    );
  }

  const formatYAxis = (value: number) => {
    if (isPercentage) return `${Math.round(value)}%`;
    if (dataKey === "avg_latency_ms") return `${Math.round(value)}ms`;
    if (dataKey === "avg_similarity") return value.toFixed(2);
    if (dataKey === "hallucination_score") return value.toFixed(2);
    return value.toString();
  };

  const formatXAxis = (dateStr: string) => {
    try {
      return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric' }).format(new Date(dateStr));
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="space-y-3">
      <h4 className="text-sm font-medium">{title}</h4>
      <div className="h-[250px] w-full border rounded-lg bg-card p-4">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
            <XAxis 
              dataKey="date" 
              tickFormatter={formatXAxis} 
              tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
              axisLine={false}
              tickLine={false}
              dy={10}
            />
            <YAxis 
              tickFormatter={formatYAxis}
              tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: "hsl(var(--popover))", 
                borderColor: "hsl(var(--border))",
                borderRadius: "var(--radius)",
                fontSize: "12px"
              }}
              labelFormatter={(label) => formatXAxis(label as string)}
              formatter={(value: any) => [formatYAxis(Number(value) || 0), title]}
            />
            <Line 
              type="monotone" 
              dataKey={dataKey as string} 
              stroke={color} 
              strokeWidth={2}
              dot={{ r: 3, fill: color, strokeWidth: 0 }}
              activeDot={{ r: 5 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
