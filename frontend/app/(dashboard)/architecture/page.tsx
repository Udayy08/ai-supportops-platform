"use client";

import React, { useState } from "react";
import useSWR from "swr";
import { Header } from "@/components/layout/header";
import { TopologyGraph } from "@/components/architecture/topology-graph";
import { NodeDetailsPanel } from "@/components/architecture/node-details-panel";
import { getArchitectureMetrics } from "@/lib/api/endpoints";
import type { ArchitectureAnalyticsResponse, NodeMetrics } from "@/lib/types";

export default function ArchitecturePage() {
  const [selectedNode, setSelectedNode] = useState<{ id: string; name: string; desc: string } | null>(null);

  // Fetch metrics every 5 seconds for "live" feel
  const { data: metricsData, isLoading } = useSWR<ArchitectureAnalyticsResponse>(
    "analytics/architecture",
    getArchitectureMetrics,
    { refreshInterval: 5000 }
  );

  const handleNodeClick = (id: string, data: any) => {
    setSelectedNode({
      id,
      name: data.label,
      desc: data.desc
    });
  };

  const handleClosePanel = () => {
    setSelectedNode(null);
  };

  const metricsForSelectedNode = selectedNode && metricsData?.nodes 
    ? metricsData.nodes[selectedNode.id] 
    : null;

  return (
    <>
      <Header
        title="Agent Network Architecture"
        description="Live topology view of the AI SupportOps LangGraph execution pipeline."
      />
      <main className="flex-1 flex flex-col p-6 min-h-[calc(100vh-4rem)]">
        {/* We use a relative container for the React Flow graph so the side panel can overlay it nicely */}
        <div className="relative flex-1 rounded-xl border bg-card shadow-sm overflow-hidden flex">
          {isLoading && !metricsData ? (
            <div className="absolute inset-0 z-10 flex items-center justify-center bg-background/50 backdrop-blur-sm">
              <div className="animate-pulse flex flex-col items-center">
                <div className="h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-4" />
                <p className="text-sm font-medium text-muted-foreground">Loading Architecture Topology...</p>
              </div>
            </div>
          ) : null}

          <div className="flex-1 relative">
            <TopologyGraph 
              metrics={metricsData?.nodes} 
              onNodeClick={handleNodeClick} 
            />
            
            {selectedNode && (
              <NodeDetailsPanel
                nodeId={selectedNode.id}
                nodeName={selectedNode.name}
                nodeDesc={selectedNode.desc}
                metrics={metricsForSelectedNode || null}
                onClose={handleClosePanel}
              />
            )}
          </div>
        </div>
      </main>
    </>
  );
}
