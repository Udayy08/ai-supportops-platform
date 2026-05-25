import { cn, getMetricColor } from "@/lib/utils";
import { LineChart, Line, ResponsiveContainer, YAxis } from "recharts";

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: "up" | "down" | "neutral";
  trendValue?: string;
  className?: string;
  isPercent?: boolean;
  chartData?: { value: number }[];
  chartColor?: string;
}

export function MetricCard({
  title,
  value,
  subtitle,
  trend,
  trendValue,
  className,
  isPercent,
  chartData,
  chartColor = "#3b82f6",
}: MetricCardProps) {
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-xl border bg-card p-5 shadow-sm transition-all hover:shadow-md",
        className
      )}
    >
      <div className="relative z-10">
        <p className="text-sm font-medium text-muted-foreground">{title}</p>
        <p className="mt-1 text-3xl font-bold tracking-tight">
          {isPercent
            ? `${(Number(value) * 100).toFixed(1)}%`
            : value}
        </p>
        {(subtitle || trendValue) && (
          <div className="mt-2 flex items-center gap-1.5 text-xs">
            {trendValue && (
              <span
                className={cn(
                  "font-medium px-1.5 py-0.5 rounded-md",
                  trend === "up" && "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400",
                  trend === "down" && "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
                  trend === "neutral" && "bg-muted text-muted-foreground"
                )}
              >
                {trend === "up" ? "↑" : trend === "down" ? "↓" : ""} {trendValue}
              </span>
            )}
            {subtitle && (
              <span className="text-muted-foreground">{subtitle}</span>
            )}
          </div>
        )}
      </div>

      {chartData && chartData.length > 0 && (
        <div className="absolute bottom-0 right-0 left-0 h-16 opacity-30 pointer-events-none">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <YAxis domain={['auto', 'auto']} hide />
              <Line 
                type="monotone" 
                dataKey="value" 
                stroke={chartColor} 
                strokeWidth={2} 
                dot={false}
                isAnimationActive={true}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

interface RAGASMetricCardProps {
  label: string;
  value: number;
}

export function RAGASMetricCard({ label, value }: RAGASMetricCardProps) {
  const pct = (value * 100).toFixed(1);
  const color = getMetricColor(value);
  const barWidth = Math.max(0, Math.min(100, value * 100));

  return (
    <div className="rounded-lg border bg-card p-5 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <p className="text-sm font-medium text-muted-foreground">{label}</p>
        <span className={cn("text-sm font-semibold", color)}>{pct}%</span>
      </div>
      <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
        <div
          className={cn(
            "h-full rounded-full transition-all",
            value >= 0.8
              ? "bg-emerald-500"
              : value >= 0.6
              ? "bg-amber-500"
              : "bg-red-500"
          )}
          style={{ width: `${barWidth}%` }}
        />
      </div>
    </div>
  );
}
