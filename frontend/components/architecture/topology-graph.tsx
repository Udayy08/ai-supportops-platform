"use client";

import React, { useMemo, useCallback } from "react";
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  MarkerType,
  Handle,
  Position,
  NodeProps
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import type { NodeMetrics } from "@/lib/types";

// Custom node component matching enterprise UI
const CustomNode = ({ data, selected }: NodeProps) => {
  const { label, sublabel, type, metrics } = data as {
    label: string;
    sublabel?: string;
    type: "agent" | "decision" | "infra";
    metrics?: NodeMetrics;
  };

  const getBorderColor = () => {
    if (selected) return "border-blue-500 ring-2 ring-blue-500/20";
    if (metrics?.status === "warning") return "border-amber-500";
    if (type === "infra") return "border-purple-500/50";
    if (type === "decision") return "border-orange-500/50";
    return "border-emerald-500/50";
  };

  const getBgColor = () => {
    if (type === "infra") return "bg-purple-950/20";
    if (type === "decision") return "bg-orange-950/20";
    return "bg-card";
  };

  return (
    <div className={`px-4 py-3 shadow-lg rounded-xl border ${getBorderColor()} ${getBgColor()} min-w-[180px]`}>
      <Handle type="target" position={Position.Top} className="w-2 h-2 !bg-muted-foreground" />
      <Handle type="target" position={Position.Left} id="left" className="w-2 h-2 !bg-muted-foreground" />
      
      <div className="flex flex-col">
        <div className="text-sm font-bold">{label}</div>
        {sublabel && <div className="text-xs text-muted-foreground mt-0.5">{sublabel}</div>}
      </div>
      
      {metrics && metrics.status !== "inactive" && (
        <div className="mt-3 pt-2 border-t border-border flex items-center justify-between text-[10px]">
          <span className="text-muted-foreground">Vol: <span className="font-mono text-foreground">{metrics.volume_processed}</span></span>
          <span className="text-muted-foreground">Lat: <span className="font-mono text-foreground">{Math.round(metrics.avg_latency_ms)}ms</span></span>
        </div>
      )}

      <Handle type="source" position={Position.Bottom} className="w-2 h-2 !bg-muted-foreground" />
      <Handle type="source" position={Position.Right} id="right" className="w-2 h-2 !bg-muted-foreground" />
    </div>
  );
};

const nodeTypes = { custom: CustomNode };

interface TopologyGraphProps {
  metrics: Record<string, NodeMetrics> | undefined;
  onNodeClick: (nodeId: string, nodeData: any) => void;
}

export function TopologyGraph({ metrics, onNodeClick }: TopologyGraphProps) {
  
  // Base initial nodes layout matching the LangGraph topology + infra
  const initialNodes = [
    // --- MAIN AGENT PIPELINE (Center Column) ---
    { id: "intake", type: "custom", position: { x: 400, y: 50 }, data: { label: "Ticket Intake", type: "agent" } },
    { id: "classifier", type: "custom", position: { x: 400, y: 150 }, data: { label: "Classifier Agent", sublabel: "Categorizes & Routes", type: "agent" } },
    { id: "retriever", type: "custom", position: { x: 400, y: 250 }, data: { label: "Hybrid Retriever", sublabel: "Semantic + Lexical + RRF", type: "agent" } },
    { id: "confidence_gate", type: "custom", position: { x: 400, y: 350 }, data: { label: "Confidence Gate", sublabel: "Threshold: -6.0", type: "decision" } },
    { id: "sentiment", type: "custom", position: { x: 400, y: 450 }, data: { label: "Sentiment Agent", sublabel: "Tone & Urgency", type: "agent" } },
    { id: "resolution", type: "custom", position: { x: 400, y: 550 }, data: { label: "Resolution Agent", sublabel: "Assembles Answer", type: "agent" } },
    { id: "response_writer", type: "custom", position: { x: 400, y: 650 }, data: { label: "Response Writer", sublabel: "Formats Response", type: "agent" } },
    { id: "hallucination_checker", type: "custom", position: { x: 400, y: 750 }, data: { label: "Hallucination Checker", sublabel: "Final Safety Net", type: "decision" } },
    
    // --- TERMINAL NODES (Right Column) ---
    { id: "human_approval", type: "custom", position: { x: 700, y: 350 }, data: { label: "Human Review Queue", sublabel: "Escalations", type: "agent" } },
    { id: "auto_resolve", type: "custom", position: { x: 700, y: 750 }, data: { label: "Auto Resolution", sublabel: "Ticket Closed", type: "agent" } },

    // --- INFRASTRUCTURE LAYER (Left Column) ---
    { id: "knowledge_base", type: "custom", position: { x: 50, y: 150 }, data: { label: "Knowledge Base", sublabel: "Source Documents", type: "infra" } },
    { id: "chromadb", type: "custom", position: { x: 50, y: 250 }, data: { label: "ChromaDB", sublabel: "Vector Store", type: "infra" } },
    { id: "bm25", type: "custom", position: { x: 220, y: 250 }, data: { label: "BM25 Index", sublabel: "Lexical Search", type: "infra" } },
    { id: "cross_encoder", type: "custom", position: { x: 50, y: 350 }, data: { label: "Cross-Encoder", sublabel: "ms-marco-MiniLM", type: "infra" } },
  ];

  const initialEdges = [
    // Main Flow
    { id: "e-intake-class", source: "intake", target: "classifier", animated: true },
    { id: "e-class-retr", source: "classifier", target: "retriever", animated: true },
    { id: "e-retr-conf", source: "retriever", target: "confidence_gate", animated: true },
    
    // Confidence Branches
    { id: "e-conf-sent", source: "confidence_gate", target: "sentiment", animated: true, label: "Pass (Proceed)" },
    { id: "e-conf-hum", source: "confidence_gate", target: "human_approval", animated: true, label: "Fail (Escalate)" },
    
    // Remainder of Generation Flow
    { id: "e-sent-res", source: "sentiment", target: "resolution", animated: true },
    { id: "e-res-write", source: "resolution", target: "response_writer", animated: true },
    { id: "e-write-hal", source: "response_writer", target: "hallucination_checker", animated: true },

    // Hallucination Branches
    { id: "e-hal-auto", source: "hallucination_checker", target: "auto_resolve", animated: true, label: "Pass" },
    { id: "e-hal-hum", source: "hallucination_checker", target: "human_approval", sourceHandle: "right", targetHandle: "left", animated: true, label: "Fail (Risk High)", type: "smoothstep" },

    // Infra Edges
    { id: "e-kb-chroma", source: "knowledge_base", target: "chromadb" },
    { id: "e-kb-bm25", source: "knowledge_base", target: "bm25" },
    { id: "e-chroma-retr", source: "chromadb", target: "retriever", sourceHandle: "right", targetHandle: "left", animated: true },
    { id: "e-bm25-retr", source: "bm25", target: "retriever", sourceHandle: "right", targetHandle: "left", animated: true },
    { id: "e-ce-retr", source: "cross_encoder", target: "retriever", sourceHandle: "right", targetHandle: "left", animated: true },
  ].map(e => ({
    ...e,
    style: { stroke: "#64748b", strokeWidth: 1.5 },
    markerEnd: { type: MarkerType.ArrowClosed, color: "#64748b" }
  }));

  // Bind metrics to nodes
  const nodesWithMetrics = useMemo(() => {
    return initialNodes.map(node => ({
      ...node,
      data: {
        ...node.data,
        metrics: metrics?.[node.id] || null,
        desc: getNodeDescription(node.id)
      }
    }));
  }, [metrics]);

  const [nodes, setNodes, onNodesChange] = useNodesState(nodesWithMetrics);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Update nodes when metrics change
  React.useEffect(() => {
    setNodes(nodesWithMetrics);
  }, [nodesWithMetrics, setNodes]);

  const onNodeClickCallback = useCallback((_: any, node: any) => {
    onNodeClick(node.id, node.data);
  }, [onNodeClick]);

  return (
    <div className="w-full h-full rounded-xl overflow-hidden border bg-background/50 relative">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClickCallback}
        nodeTypes={nodeTypes}
        fitView
        className="bg-dot-pattern"
        minZoom={0.5}
        maxZoom={1.5}
      >
        <Background color="#334155" gap={20} size={1} />
        <Controls />
        <MiniMap 
          nodeColor={(n) => {
            if (n.data?.type === "infra") return "#6b21a8";
            if (n.data?.type === "decision") return "#c2410c";
            return "#0f172a";
          }}
          maskColor="rgba(0,0,0,0.2)"
          className="bg-background/80"
        />
      </ReactFlow>
    </div>
  );
}

function getNodeDescription(id: string): string {
  const descs: Record<string, string> = {
    intake: "Receives external customer queries via API or webhook.",
    classifier: "Analyzes the initial input to determine ticket category, routing rules, and urgency context.",
    retriever: "Orchestrates multi-modal retrieval. Uses BM25 for lexical matching and ChromaDB for semantic matching, then applies RRF.",
    confidence_gate: "Analyzes Cross-Encoder scores to gate the system. Low confidence auto-escalates to prevent LLM hallucinations.",
    sentiment: "Detects emotional tone, urgency flags, and implicit sentiment of the customer.",
    resolution: "Assembles context from retrieval and synthesizes the core logic for a support answer.",
    response_writer: "Drafts the final human-readable response applying proper tone and formatting.",
    hallucination_checker: "Performs self-reflection on the generated response against the retrieved context to verify factual accuracy.",
    human_approval: "Escalation queue where human agents review AI proposed answers or take over unresolved tickets.",
    auto_resolve: "Terminal state where the system automatically replies to the customer and closes the ticket.",
    knowledge_base: "Source of truth for all support articles, syncs chunks into vector/lexical stores.",
    chromadb: "Vector database storing dense embeddings for semantic search.",
    bm25: "Lexical search index tracking keyword frequencies (TF-IDF variant).",
    cross_encoder: "Secondary reranking model (ms-marco-MiniLM-L-6-v2) that evaluates the semantic overlap between query and retrieved chunks."
  };
  return descs[id] || "No description available.";
}
