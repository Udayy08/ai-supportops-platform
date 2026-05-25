"use client";

import React from "react";
import useSWR from "swr";
import Link from "next/link";
import { useParams } from "next/navigation";
import { 
  GitBranch,
  Search,
  MessageSquare,
  AlertTriangle,
  User,
  Clock,
  CheckCircle2,
  BrainCircuit,
  Database,
  ShieldCheck,
  Bot
} from "lucide-react";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getWorkflowTrace } from "@/lib/api/endpoints";
import { formatDuration } from "@/lib/utils";
import type { WorkflowTraceResponse } from "@/lib/types";
import { cn } from "@/lib/utils";
import { SourceAttribution } from "@/components/shared/source-attribution";

export default function TraceDetailsPage() {
  const params = useParams();
  const id = params?.id as string;

  const { data: trace, isLoading } = useSWR<WorkflowTraceResponse>(
    id ? `traces/${id}` : null,
    () => getWorkflowTrace(id)
  );

  if (isLoading) {
    return (
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center">
        <div className="flex flex-col items-center gap-4 text-muted-foreground">
          <GitBranch className="h-8 w-8 animate-pulse" />
          <p>Loading trace details...</p>
        </div>
      </div>
    );
  }

  if (!trace) {
    return (
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center">
        <div className="flex flex-col items-center gap-4 text-muted-foreground">
          <AlertTriangle className="h-8 w-8 text-amber-500" />
          <p>Trace not found.</p>
          <Button variant="outline" asChild>
            <Link href="/traces">Back to Traces</Link>
          </Button>
        </div>
      </div>
    );
  }

  const { input_state, output_state } = trace;
  const retrieval = output_state?.retrieval_debug;

  return (
    <>
      <Header
        title="Trace Details"
        description={`Execution details for trace ${trace.id}`}
        backLink="/traces"
      />
      <main className="flex-1 p-6 space-y-6 max-w-7xl mx-auto w-full">
        
        {/* Overview Cards */}
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Status</CardTitle>
              <GitBranch className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold uppercase">{trace.status}</div>
              <p className="text-xs text-muted-foreground">
                Final disposition
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Latency</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatDuration(trace.total_latency_ms || 0)}</div>
              <p className="text-xs text-muted-foreground">
                Total workflow execution time
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Hallucination</CardTitle>
              <AlertTriangle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className={cn(
                "text-2xl font-bold font-mono",
                (Number(output_state?.hallucination_score) ?? 0) > 0.5 ? "text-red-500" : "text-emerald-500"
              )}>
                {output_state?.hallucination_score !== undefined ? Number(output_state.hallucination_score).toFixed(2) : "N/A"}
              </div>
              <p className="text-xs text-muted-foreground">
                Quality score (lower is better)
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Ticket</CardTitle>
              <MessageSquare className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <Link href={`/tickets/${trace.ticket_id}`} className="text-xl font-bold text-primary hover:underline truncate block">
                {trace.ticket_id.slice(0, 8)}…
              </Link>
              <p className="text-xs text-muted-foreground">
                View related ticket
              </p>
            </CardContent>
          </Card>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          {/* Left Column: Workflow Timeline & Generation */}
          <div className="space-y-6 md:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <GitBranch className="h-4 w-4" />
                  Workflow Path
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="relative border-l border-muted-foreground/20 ml-3 space-y-6 pb-2">
                  {trace.nodes_visited.map((node, i) => {
                    const isLast = i === trace.nodes_visited.length - 1;
                    const isError = trace.status === "failed" && isLast;
                    const isEscalated = (trace.status === "escalated" || node === "human_approval") && isLast;
                    
                    let Icon = Bot;
                    let iconColor = "text-blue-500 bg-blue-100 dark:bg-blue-900/30";
                    
                    if (node === "intake") { Icon = User; iconColor = "text-indigo-500 bg-indigo-100 dark:bg-indigo-900/30"; }
                    if (node === "classifier") { Icon = BrainCircuit; }
                    if (node === "retriever") { Icon = Database; iconColor = "text-emerald-500 bg-emerald-100 dark:bg-emerald-900/30"; }
                    if (node === "hallucination_checker") { Icon = ShieldCheck; }
                    if (node === "auto_resolve") { Icon = CheckCircle2; iconColor = "text-emerald-500 bg-emerald-100 dark:bg-emerald-900/30"; }
                    
                    if (isError) { Icon = AlertTriangle; iconColor = "text-red-500 bg-red-100 dark:bg-red-900/30"; }
                    if (isEscalated) { Icon = User; iconColor = "text-orange-500 bg-orange-100 dark:bg-orange-900/30"; }

                    return (
                      <div key={i} className="relative flex items-start pl-6 group">
                        <div className={cn(
                          "absolute -left-[13px] top-0.5 flex h-6 w-6 items-center justify-center rounded-full border bg-background shadow-sm transition-transform group-hover:scale-110",
                          iconColor
                        )}>
                          <Icon className="h-3 w-3" />
                        </div>
                        <div className="flex flex-col">
                          <span className={cn(
                            "text-sm font-semibold capitalize",
                            isError ? "text-red-500" : isEscalated ? "text-orange-500" : "text-foreground"
                          )}>
                            {node.replace(/_/g, " ")}
                          </span>
                          <span className="text-xs text-muted-foreground mt-0.5">
                            {isLast ? (isError ? "Failed execution" : isEscalated ? "Escalated to human" : "Completed successfully") : "Processed"}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <User className="h-4 w-4" />
                  User Query
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="bg-muted/50 p-4 rounded-md text-sm whitespace-pre-wrap font-medium">
                  {input_state?.customer_message || "—"}
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <MessageSquare className="h-4 w-4" />
                  Final Response
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="bg-blue-500/10 border border-blue-200 text-blue-900 dark:text-blue-200 p-4 rounded-md text-sm whitespace-pre-wrap">
                  {trace.final_response || "No response generated."}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right Column: Retrieval Diagnostics */}
          <div className="space-y-6 md:col-span-2">
            <Card className="border-emerald-200 dark:border-emerald-900 shadow-sm">
              <CardHeader className="bg-emerald-50 dark:bg-emerald-900/10 border-b border-emerald-100 dark:border-emerald-900">
                <CardTitle className="text-base flex items-center gap-2 text-emerald-800 dark:text-emerald-400">
                  <Search className="h-4 w-4" />
                  Retrieval Diagnostics
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                {!retrieval ? (
                  <div className="p-6 text-center text-muted-foreground text-sm">
                    No retrieval data available for this trace.
                  </div>
                ) : (
                  <div className="divide-y">
                    <div className="p-4 grid grid-cols-2 gap-4 bg-muted/20 text-sm">
                      <div>
                        <span className="text-muted-foreground block text-xs uppercase mb-1">Search Query</span>
                        <span className="font-medium">{retrieval.query || "—"}</span>
                      </div>
                      <div className="flex gap-6">
                        <div>
                          <span className="text-muted-foreground block text-xs uppercase mb-1">Top K</span>
                          <span className="font-mono">{retrieval.top_k}</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground block text-xs uppercase mb-1">Latency</span>
                          <span className="font-mono">{formatDuration(retrieval.retrieval_latency_ms)}</span>
                        </div>
                      </div>
                    </div>

                    <div className="p-4">
                      <SourceAttribution sources={retrieval.documents || []} />
                      {(!retrieval.documents || retrieval.documents.length === 0) && (
                        <div className="text-center p-4 text-muted-foreground border rounded-md border-dashed">
                          No documents were retrieved for this query.
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Hallucination / Escalation Details */}
            {output_state?.hallucination_decision && (
              <Card className="border-red-200 dark:border-red-900 shadow-sm">
                <CardHeader className="bg-red-50 dark:bg-red-900/10 border-b border-red-100 dark:border-red-900">
                  <CardTitle className="text-base flex items-center gap-2 text-red-800 dark:text-red-400">
                    <AlertTriangle className="h-4 w-4" />
                    Hallucination & Risk Analysis
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-4 space-y-4 text-sm">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <span className="text-muted-foreground block text-xs uppercase mb-1">Decision</span>
                      <Badge variant={output_state.hallucination_decision === "escalate" ? "destructive" : "secondary"}>
                        {output_state.hallucination_decision}
                      </Badge>
                    </div>
                  </div>
                  {output_state.escalation_reason && (
                    <div>
                      <span className="text-muted-foreground block text-xs uppercase mb-1">Escalation Reason</span>
                      <div className="bg-red-500/10 text-red-700 dark:text-red-400 p-3 rounded-md">
                        {output_state.escalation_reason}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </main>
    </>
  );
}
