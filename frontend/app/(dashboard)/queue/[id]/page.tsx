"use client";

import React, { useState, useEffect, use } from "react";
import useSWR from "swr";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { ArrowLeft, CheckCircle, XCircle, Loader2, Bot, Info, Clock, AlertTriangle } from "lucide-react";
import { Header } from "@/components/layout/header";
import { PriorityBadge, StatusBadge } from "@/components/shared/status-badges";
import { SourceAttribution } from "@/components/shared/source-attribution";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { getTicket, humanReviewTicket } from "@/lib/api/endpoints";
import { formatDateTime } from "@/lib/utils";
import type { Ticket } from "@/lib/types";

export default function ReviewDetailsPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const router = useRouter();
  const { id } = use(params);

  const { data: ticket, isLoading } = useSWR<Ticket>(`tickets/${id}`, () =>
    getTicket(id)
  );

  const [editedResponse, setEditedResponse] = useState<string | null>(null);
  const [reviewerNotes, setReviewerNotes] = useState("");
  const [reviewing, setReviewing] = useState<"APPROVED" | "REJECTED" | null>(null);

  const handleReview = async (decision: "APPROVED" | "REJECTED") => {
    if (!ticket) return;
    
    if (decision === "REJECTED" && !reviewerNotes.trim()) {
      toast.error("Reviewer Notes Required", { description: "You must provide notes when rejecting an AI response." });
      return;
    }

    setReviewing(decision);
    try {
      const finalResponse = editedResponse !== null ? editedResponse : (ticket.metadata?.ai_proposed_response as string || "");

      await humanReviewTicket(ticket.id, {
        ticket_id: ticket.id,
        approval_decision: decision,
        agent_override_notes: reviewerNotes.trim() || undefined,
        edited_response: finalResponse.trim() || undefined,
      });
      
      toast.success(
        decision === "APPROVED" ? "Ticket Approved" : "Ticket Rejected", 
        { description: decision === "APPROVED" ? "The response has been sent and the ticket is closed." : "The ticket has been reopened for manual handling." }
      );
      
      router.push("/queue");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Review failed";
      toast.error("Review failed", { description: message });
      setReviewing(null);
    }
  };

  if (isLoading) {
    return (
      <>
        <Header title="Review Details" />
        <main className="flex-1 p-6 flex justify-center mt-20">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </main>
      </>
    );
  }

  if (!ticket || ticket.status !== "escalated") {
    return (
      <>
        <Header title="Ticket Not Available" />
        <main className="flex-1 p-6">
          <div className="max-w-2xl mx-auto text-center space-y-4 py-12">
            <CheckCircle className="h-12 w-12 text-emerald-500 mx-auto" />
            <h2 className="text-lg font-semibold">No Review Needed</h2>
            <p className="text-muted-foreground">This ticket is not currently in the escalated state.</p>
            <Button asChild className="mt-4">
              <Link href="/queue">Back to Queue</Link>
            </Button>
          </div>
        </main>
      </>
    );
  }

  const disposition = typeof ticket.metadata?.workflow_final_disposition === "string" ? ticket.metadata.workflow_final_disposition.replace("_", " ") : "N/A";
  const hallucinationScore = typeof ticket.metadata?.hallucination_score === "number" ? ticket.metadata.hallucination_score.toFixed(2) : "N/A";
  const latency = typeof ticket.metadata?.workflow_latency_ms === "number" ? `${ticket.metadata.workflow_latency_ms} ms` : "N/A";
  const nodesVisited = Array.isArray(ticket.metadata?.workflow_nodes_visited) ? ticket.metadata.workflow_nodes_visited.join(" → ") : "N/A";

  return (
    <>
      <Header
        title="Review AI Response"
        description="Verify and edit the proposed resolution before sending to the customer."
      />
      <main className="flex-1 p-6">
        <div className="max-w-5xl mx-auto space-y-6">
          <Button variant="ghost" size="sm" asChild className="-ml-1 text-xs">
            <Link href="/queue">
              <ArrowLeft className="h-3.5 w-3.5 mr-1.5" />
              Back to Queue
            </Link>
          </Button>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
            
            {/* Left Column: Context & Metadata */}
            <div className="lg:col-span-1 space-y-6">
              
              {/* Ticket Details */}
              <div className="rounded-lg border bg-card shadow-sm p-5 space-y-4">
                <h3 className="text-sm font-semibold flex items-center gap-2">
                  <Info className="h-4 w-4 text-muted-foreground" />
                  Ticket Details
                </h3>
                <dl className="space-y-3 text-sm">
                  <div>
                    <dt className="text-muted-foreground text-xs mb-1">Subject</dt>
                    <dd className="font-medium">{ticket.subject}</dd>
                  </div>
                  <div>
                    <dt className="text-muted-foreground text-xs mb-1">Customer Query</dt>
                    <dd className="rounded-md bg-muted/50 p-3 text-sm whitespace-pre-wrap border max-h-48 overflow-y-auto">
                      {ticket.description}
                    </dd>
                  </div>
                  <div className="grid grid-cols-2 gap-4 pt-2">
                    <div>
                      <dt className="text-muted-foreground text-xs mb-1">Priority</dt>
                      <dd><PriorityBadge priority={ticket.priority} /></dd>
                    </div>
                    <div>
                      <dt className="text-muted-foreground text-xs mb-1">Status</dt>
                      <dd><StatusBadge status={ticket.status} /></dd>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4 pt-2">
                    <div>
                      <dt className="text-muted-foreground text-xs mb-1">Category</dt>
                      <dd className="font-medium">{ticket.category || "Uncategorized"}</dd>
                    </div>
                    <div>
                      <dt className="text-muted-foreground text-xs mb-1">Created</dt>
                      <dd className="font-medium">{formatDateTime(ticket.created_at)}</dd>
                    </div>
                  </div>
                </dl>
              </div>

              {/* Workflow Metadata */}
              <div className="rounded-lg border bg-card shadow-sm p-5 space-y-4">
                <h3 className="text-sm font-semibold flex items-center gap-2">
                  <Bot className="h-4 w-4 text-muted-foreground" />
                  Workflow Diagnostics
                </h3>
                <dl className="grid grid-cols-2 gap-y-4 text-sm">
                  <div>
                    <dt className="text-muted-foreground text-xs mb-1">Disposition</dt>
                    <dd className="font-medium capitalize">{disposition}</dd>
                  </div>
                  <div>
                    <dt className="text-muted-foreground text-xs mb-1 flex items-center gap-1">
                      Hallucination Score
                      {typeof ticket.metadata?.hallucination_score === "number" && ticket.metadata.hallucination_score > 0.5 && (
                        <AlertTriangle className="h-3.5 w-3.5 text-orange-500" />
                      )}
                    </dt>
                    <dd className="font-medium">{hallucinationScore}</dd>
                  </div>
                  <div>
                    <dt className="text-muted-foreground text-xs mb-1 flex items-center gap-1">
                      <Clock className="h-3 w-3" /> Latency
                    </dt>
                    <dd className="font-medium">{latency}</dd>
                  </div>
                  <div className="col-span-2">
                    <dt className="text-muted-foreground text-xs mb-1">Nodes Visited</dt>
                    <dd className="text-xs font-mono text-muted-foreground break-words leading-relaxed">
                      {nodesVisited}
                    </dd>
                  </div>
                </dl>
              </div>
            </div>

            {/* Right Column: Editing & Actions */}
            <div className="lg:col-span-2 space-y-6">
              
              <div className="rounded-lg border bg-card shadow-sm p-6 space-y-5">
                <div className="space-y-2">
                  <Label htmlFor="ai-response" className="text-base font-semibold">AI Proposed Response</Label>
                  <p className="text-xs text-muted-foreground">You can edit the response below before approving.</p>
                  <Textarea
                    id="ai-response"
                    value={editedResponse !== null ? editedResponse : (ticket.metadata?.ai_proposed_response as string || "")}
                    onChange={(e) => setEditedResponse(e.target.value)}
                    rows={10}
                    className="resize-none font-mono text-sm leading-relaxed"
                    placeholder="No response generated."
                  />
                  <SourceAttribution sources={ticket.metadata?.sources_used || []} />
                </div>

                <div className="space-y-2 pt-4 border-t">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="reviewer-notes" className="text-sm font-semibold">Reviewer Notes</Label>
                    <span className="text-xs text-muted-foreground">Required for rejection</span>
                  </div>
                  <Textarea
                    id="reviewer-notes"
                    value={reviewerNotes}
                    onChange={(e) => setReviewerNotes(e.target.value)}
                    rows={3}
                    className="resize-none text-sm"
                    placeholder="Enter reason for approval or rejection..."
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-3">
                <Button
                  variant="outline"
                  onClick={() => handleReview("REJECTED")}
                  disabled={reviewing !== null}
                  className="text-destructive border-destructive/30 hover:bg-destructive/10"
                >
                  {reviewing === "REJECTED" ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <XCircle className="h-4 w-4 mr-2" />}
                  Reject & Reopen
                </Button>
                <Button
                  onClick={() => handleReview("APPROVED")}
                  disabled={reviewing !== null}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white"
                >
                  {reviewing === "APPROVED" ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <CheckCircle className="h-4 w-4 mr-2" />}
                  Approve & Close
                </Button>
              </div>

            </div>

          </div>
        </div>
      </main>
    </>
  );
}
