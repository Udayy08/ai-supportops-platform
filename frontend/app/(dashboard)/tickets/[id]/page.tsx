"use client";

import React, { useState } from "react";
import { use } from "react";
import useSWR from "swr";
import Link from "next/link";
import { toast } from "sonner";
import {
  ArrowLeft,
  Bot,
  RefreshCw,
  CheckCircle,
  XCircle,
  Loader2,
  Tag,
} from "lucide-react";
import { Header } from "@/components/layout/header";
import { StatusBadge, PriorityBadge } from "@/components/shared/status-badges";
import { SourceAttribution } from "@/components/shared/source-attribution";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { Progress, ProgressTrack, ProgressIndicator } from "@/components/ui/progress";
import { Label } from "@/components/ui/label";
import { getTicket, processTicket, humanReviewTicket } from "@/lib/api/endpoints";
import { formatDateTime } from "@/lib/utils";
import type { Ticket } from "@/lib/types";
import { cn } from "@/lib/utils";

export default function TicketDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [processing, setProcessing] = useState(false);
  const [reviewOpen, setReviewOpen] = useState(false);
  const [reviewNotes, setReviewNotes] = useState("");
  const [reviewing, setReviewing] = useState(false);

  const [refreshInterval, setRefreshInterval] = React.useState(4000);

  const { data: ticket, isLoading, mutate } = useSWR<Ticket>(
    `tickets/${id}`,
    () => getTicket(id),
    {
      refreshInterval,
      onSuccess: (data) => {
        if (data.status !== "open" && data.status !== "in_progress") {
          setRefreshInterval(0);
        }
      },
    }
  );

  const handleProcess = async () => {
    if (!ticket) return;
    setProcessing(true);
    try {
      await processTicket({ ticket_id: id, additional_context: ticket.description });
      toast.success("Workflow triggered", { description: "AI agent is processing this ticket." });
      setTimeout(() => mutate(), 3000);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to trigger workflow";
      toast.error("Error", { description: message });
    } finally {
      setProcessing(false);
    }
  };

  const handleReview = async (decision: "APPROVED" | "REJECTED") => {
    if (!ticket) return;
    setReviewing(true);
    try {
      await humanReviewTicket(id, {
        ticket_id: id,
        approval_decision: decision,
        agent_override_notes: reviewNotes,
      });
      toast.success(decision === "APPROVED" ? "Ticket Approved" : "Ticket Rejected");
      setReviewOpen(false);
      mutate();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Review failed";
      toast.error("Review failed", { description: message });
    } finally {
      setReviewing(false);
    }
  };

  if (isLoading) {
    return (
      <>
        <Header title="Ticket Detail" />
        <main className="flex-1 p-6">
          <div className="max-w-2xl mx-auto space-y-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-16 rounded-lg bg-muted animate-pulse" />
            ))}
          </div>
        </main>
      </>
    );
  }

  if (!ticket) {
    return (
      <>
        <Header title="Ticket Not Found" />
        <main className="flex-1 p-6 flex items-center justify-center">
          <p className="text-muted-foreground">This ticket does not exist.</p>
        </main>
      </>
    );
  }

  const isResolvedOrEscalated = ticket.status === "closed" || ticket.status === "escalated";
  const hasMetadata = ticket.metadata && Object.keys(ticket.metadata).length > 0;
  const aiResponse = typeof ticket.metadata?.ai_proposed_response === "string" ? ticket.metadata.ai_proposed_response : "No response generated.";
  const disposition = typeof ticket.metadata?.workflow_final_disposition === "string" ? ticket.metadata.workflow_final_disposition.replace("_", " ") : "N/A";
  const hallucinationScore = typeof ticket.metadata?.hallucination_score === "number" ? ticket.metadata.hallucination_score.toFixed(2) : "N/A";
  const latency = typeof ticket.metadata?.workflow_latency_ms === "number" ? `${ticket.metadata.workflow_latency_ms} ms` : "N/A";
  const nodesVisited = Array.isArray(ticket.metadata?.workflow_nodes_visited) ? ticket.metadata.workflow_nodes_visited.join(" → ") : "N/A";
  
  const retrievalDebug = (ticket.metadata?.retrieval_debug as any) || {};
  const confidenceScore = typeof retrievalDebug.retrieval_confidence_score === "number" ? retrievalDebug.retrieval_confidence_score : null;
  const confidenceDecision = retrievalDebug.confidence_decision || "N/A";
  const confidenceThreshold = typeof retrievalDebug.retrieval_confidence_threshold === "number" ? retrievalDebug.retrieval_confidence_threshold : -6.0;

  // Calculate a visual percentage for the confidence gauge (-10 to 0)
  const confidencePct = confidenceScore !== null 
    ? Math.max(0, Math.min(100, ((confidenceScore + 10) / 10) * 100))
    : 0;

  return (
    <>
      <Header
        title={ticket.subject}
        description={`Created ${formatDateTime(ticket.created_at)}`}
      />
      <main className="flex-1 p-6">
        <div className="max-w-2xl mx-auto space-y-5">
          <Button variant="ghost" size="sm" asChild className="-ml-1 text-xs">
            <Link href="/tickets">
              <ArrowLeft className="h-3.5 w-3.5 mr-1.5" />
              Back to Tickets
            </Link>
          </Button>

          {/* Status row */}
          <div className="flex flex-wrap items-center gap-3">
            <StatusBadge status={ticket.status} />
            <PriorityBadge priority={ticket.priority} />
            {ticket.category && (
              <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
                <Tag className="h-3 w-3" />
                {ticket.category}
              </span>
            )}
            {(ticket.status === "open" || ticket.status === "in_progress") && (
              <span className="ml-auto flex items-center gap-1 text-xs text-muted-foreground">
                <RefreshCw className="h-3 w-3 animate-spin" />
                Auto-refreshing
              </span>
            )}
          </div>

          {/* Description */}
          <div className="rounded-lg border bg-card p-5 shadow-sm">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-3">
              Description
            </p>
            <p className="text-sm leading-relaxed whitespace-pre-wrap">{ticket.description}</p>
          </div>

          {/* AI Resolution */}
          {isResolvedOrEscalated && hasMetadata && (
            <div className="rounded-lg border bg-card p-5 shadow-sm space-y-4 border-blue-100 dark:border-blue-900/50">
              <div className="flex items-center justify-between">
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide flex items-center gap-1.5">
                  <Bot className="h-4 w-4" />
                  AI Resolution
                </p>
                {ticket.status === "escalated" && (
                  <span className="inline-flex items-center rounded-full bg-orange-100 px-2.5 py-0.5 text-xs font-medium text-orange-800 dark:bg-orange-900/40 dark:text-orange-400">
                    Awaiting Human Review
                  </span>
                )}
              </div>
              
              <div className="space-y-1.5">
                <p className="text-sm font-medium">Response</p>
                <div className="rounded-md bg-muted/50 p-3.5 text-sm whitespace-pre-wrap border">
                  {aiResponse}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 border-t pt-4">
                <div className="bg-muted/30 p-3 rounded-md border">
                  <p className="text-xs text-muted-foreground uppercase mb-1">Disposition</p>
                  <p className="font-semibold capitalize">{disposition}</p>
                </div>
                
                <div className="bg-muted/30 p-3 rounded-md border">
                  <div className="flex justify-between items-center mb-1">
                    <p className="text-xs text-muted-foreground uppercase">Confidence</p>
                    <span className={cn(
                      "text-xs font-bold",
                      confidenceDecision === "proceed" ? "text-emerald-500" : "text-amber-500"
                    )}>
                      {confidenceScore !== null ? confidenceScore.toFixed(2) : "N/A"}
                    </span>
                  </div>
                  <Progress value={confidencePct} className="h-1.5 mt-2">
                    <ProgressTrack>
                      <ProgressIndicator className={cn(
                        confidenceDecision === "proceed" ? "bg-emerald-500" : "bg-amber-500"
                      )} />
                    </ProgressTrack>
                  </Progress>
                  <p className="text-[10px] text-muted-foreground mt-1 text-right">Threshold: {confidenceThreshold}</p>
                </div>

                <div className="bg-muted/30 p-3 rounded-md border">
                  <p className="text-xs text-muted-foreground uppercase mb-1">Hallucination Risk</p>
                  <p className={cn(
                    "font-semibold",
                    Number(hallucinationScore) > 0.5 ? "text-red-500" : "text-emerald-500"
                  )}>{hallucinationScore}</p>
                </div>

                <div className="bg-muted/30 p-3 rounded-md border">
                  <p className="text-xs text-muted-foreground uppercase mb-1">Processing Time</p>
                  <p className="font-semibold">{latency}</p>
                </div>

                <div className="bg-muted/30 p-3 rounded-md border col-span-2">
                  <p className="text-xs text-muted-foreground uppercase mb-1">Workflow Path</p>
                  <p className="font-medium text-xs text-muted-foreground flex flex-wrap gap-1">
                    {nodesVisited}
                  </p>
                </div>
              </div>
              
              <SourceAttribution sources={ticket.metadata.sources_used || []} />
            </div>
          )}

          {/* Metadata */}
          <div className="rounded-lg border bg-card p-5 shadow-sm">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-3">
              Details
            </p>
            <dl className="grid grid-cols-2 gap-y-3 text-sm">
              <dt className="text-muted-foreground">Source</dt>
              <dd className="font-medium capitalize">{ticket.source}</dd>
              <dt className="text-muted-foreground">Created</dt>
              <dd className="font-medium">{formatDateTime(ticket.created_at)}</dd>
              <dt className="text-muted-foreground">Updated</dt>
              <dd className="font-medium">{formatDateTime(ticket.updated_at)}</dd>
              {ticket.resolved_at && (
                <>
                  <dt className="text-muted-foreground">Resolved</dt>
                  <dd className="font-medium">{formatDateTime(ticket.resolved_at)}</dd>
                </>
              )}
            </dl>
          </div>

          {/* Actions */}
          <div className="flex flex-wrap gap-3">
            {ticket.status === "open" && (
              <Button
                onClick={handleProcess}
                disabled={processing}
                size="sm"
                className="text-sm"
              >
                {processing ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Bot className="h-4 w-4 mr-2" />
                )}
                {processing ? "Triggering..." : "Trigger AI Workflow"}
              </Button>
            )}
            {ticket.status === "escalated" && (
              <Button
                size="sm"
                variant="outline"
                className="text-sm"
                onClick={() => setReviewOpen(true)}
              >
                <CheckCircle className="h-4 w-4 mr-2 text-emerald-500" />
                Human Review
              </Button>
            )}
          </div>
        </div>
      </main>

      {/* Human Review Dialog */}
      <Dialog open={reviewOpen} onOpenChange={setReviewOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Human Review Decision</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <p className="text-sm text-muted-foreground">
              Review the AI&apos;s proposed resolution and approve or reject.
            </p>
            <div className="space-y-1.5">
              <Label className="text-sm">Override Notes (optional)</Label>
              <Textarea
                value={reviewNotes}
                onChange={(e) => setReviewNotes(e.target.value)}
                placeholder="Add any notes for the record..."
                rows={3}
                className="text-sm resize-none"
              />
            </div>
          </div>
          <DialogFooter className="gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleReview("REJECTED")}
              disabled={reviewing}
              className="text-destructive border-destructive/30 hover:bg-destructive/10"
            >
              {reviewing ? <Loader2 className="h-4 w-4 animate-spin" /> : <XCircle className="h-4 w-4 mr-1.5" />}
              Reject
            </Button>
            <Button
              size="sm"
              onClick={() => handleReview("APPROVED")}
              disabled={reviewing}
            >
              {reviewing ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle className="h-4 w-4 mr-1.5" />}
              Approve
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
