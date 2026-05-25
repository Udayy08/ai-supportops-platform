import React from "react";
import { X, Activity, CheckCircle, Clock, BarChart } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { NodeMetrics } from "@/lib/types";

interface NodeDetailsPanelProps {
  nodeId: string | null;
  nodeName: string;
  nodeDesc: string;
  metrics: NodeMetrics | null;
  onClose: () => void;
}

export function NodeDetailsPanel({ nodeId, nodeName, nodeDesc, metrics, onClose }: NodeDetailsPanelProps) {
  if (!nodeId) return null;

  return (
    <div className="absolute top-0 right-0 h-full w-[350px] border-l bg-background/95 backdrop-blur-sm shadow-xl flex flex-col z-50 transform transition-transform animate-in slide-in-from-right-10">
      <div className="p-4 border-b flex items-start justify-between">
        <div>
          <h3 className="font-semibold text-lg">{nodeName}</h3>
          <p className="text-xs text-muted-foreground mt-1">{nodeDesc}</p>
        </div>
        <button onClick={onClose} className="p-1 hover:bg-muted rounded-md">
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* Status Badge */}
        <div>
          <p className="text-xs font-semibold uppercase text-muted-foreground mb-2">Status</p>
          <Badge 
            variant="outline" 
            className={
              metrics?.status === "healthy" ? "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950 dark:text-emerald-400" :
              metrics?.status === "warning" ? "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950 dark:text-amber-400" :
              "bg-muted text-muted-foreground"
            }
          >
            {metrics?.status || "Unknown"}
          </Badge>
        </div>

        {/* Core Metrics */}
        <div>
          <p className="text-xs font-semibold uppercase text-muted-foreground mb-3 flex items-center gap-1.5">
            <Activity className="h-4 w-4" />
            Core Metrics
          </p>
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-md border p-3 bg-muted/30">
              <p className="text-xs text-muted-foreground mb-1 flex items-center gap-1">
                <BarChart className="h-3 w-3" /> Volume
              </p>
              <p className="font-mono font-medium text-lg">{metrics?.volume_processed.toLocaleString() || 0}</p>
            </div>
            
            <div className="rounded-md border p-3 bg-muted/30">
              <p className="text-xs text-muted-foreground mb-1 flex items-center gap-1">
                <Clock className="h-3 w-3" /> Avg Latency
              </p>
              <p className="font-mono font-medium text-lg">{metrics?.avg_latency_ms.toFixed(0) || 0} ms</p>
            </div>
            
            <div className="rounded-md border p-3 bg-muted/30 col-span-2">
              <p className="text-xs text-muted-foreground mb-1 flex items-center gap-1">
                <CheckCircle className="h-3 w-3" /> Success Rate
              </p>
              <p className="font-mono font-medium text-lg">
                {((metrics?.success_rate || 0) * 100).toFixed(1)}%
              </p>
            </div>
          </div>
        </div>

        {/* Custom Metrics */}
        {metrics?.custom_metrics && Object.keys(metrics.custom_metrics).length > 0 && (
          <div>
            <p className="text-xs font-semibold uppercase text-muted-foreground mb-3">Observability Insights</p>
            <div className="space-y-2">
              {Object.entries(metrics.custom_metrics).map(([key, val]) => (
                <div key={key} className="flex items-center justify-between p-2 rounded border bg-card text-sm">
                  <span className="text-muted-foreground capitalize">{key.replace(/_/g, " ")}</span>
                  <span className="font-mono font-medium">{val}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
