"use client";

import React, { useState } from "react";
import useSWR from "swr";
import Link from "next/link";
import { ExternalLink, GitBranch } from "lucide-react";
import { Header } from "@/components/layout/header";
import { TableSkeleton } from "@/components/shared/skeleton-loaders";
import { EmptyState } from "@/components/shared/empty-state";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { listWorkflowTraces } from "@/lib/api/endpoints";
import { formatDateTime, formatDuration } from "@/lib/utils";
import type { WorkflowTraceResponse } from "@/lib/types";
import { cn } from "@/lib/utils";

function DispositionBadge({ disposition }: { disposition: string | null }) {
  if (!disposition) return <span className="text-xs text-muted-foreground">—</span>;
  const color =
    disposition === "resolved"
      ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400"
      : disposition === "escalated"
      ? "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400"
      : "bg-muted text-muted-foreground";
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize",
        color
      )}
    >
      {disposition}
    </span>
  );
}

export default function TracesPage() {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useSWR(`traces?page=${page}`, () =>
    listWorkflowTraces({ page, page_size: 20 })
  );

  return (
    <>
      <Header
        title="Workflow Traces"
        description="LangGraph agent execution history and observability"
      />
      <main className="flex-1 p-6 space-y-4">
        <div className="rounded-lg border bg-card shadow-sm overflow-hidden">
          {isLoading ? (
            <div className="p-6">
              <TableSkeleton rows={8} />
            </div>
          ) : !data?.items.length ? (
            <EmptyState
              title="No workflow traces yet"
              description="Trigger the AI workflow on a ticket to see traces appear here."
              icon={<GitBranch className="h-8 w-8 text-muted-foreground" />}
              action={
                <Button size="sm" asChild variant="outline">
                  <Link href="/tickets">Go to Tickets</Link>
                </Button>
              }
            />
          ) : (
              <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Trace ID</TableHead>
                  <TableHead>Ticket ID</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Disposition</TableHead>
                  <TableHead>Workflow Path</TableHead>
                  <TableHead>Hallucination Score</TableHead>
                  <TableHead>Latency</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.items.map((trace: WorkflowTraceResponse) => (
                  <TableRow key={trace.id} className="cursor-pointer hover:bg-muted/50 transition-colors">
                    <TableCell>
                      <Link href={`/traces/${trace.id}`} className="text-xs font-mono text-primary hover:underline">
                        {trace.id.slice(0, 8)}…
                      </Link>
                    </TableCell>
                    <TableCell>
                      <Link
                        href={`/tickets/${trace.ticket_id}`}
                        className="text-xs font-mono text-muted-foreground hover:underline"
                      >
                        {trace.ticket_id.slice(0, 8)}…
                      </Link>
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground whitespace-nowrap">
                      {formatDateTime(trace.created_at)}
                    </TableCell>
                    <TableCell>
                      <DispositionBadge disposition={trace.status} />
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {trace.nodes_visited?.map((node, i) => (
                          <span key={i} className="text-[10px] px-1.5 py-0.5 bg-muted rounded">
                            {node}
                          </span>
                        ))}
                      </div>
                    </TableCell>
                    <TableCell className="text-xs">
                      {trace.output_state?.hallucination_score !== undefined ? (
                        <span className={cn(
                          "font-mono",
                          trace.output_state.hallucination_score > 0.5 ? "text-red-500" : "text-emerald-500"
                        )}>
                          {trace.output_state.hallucination_score.toFixed(2)}
                        </span>
                      ) : "—"}
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {formatDuration(trace.total_latency_ms || 0)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </div>

        {data && data.total > 20 && (
          <div className="flex items-center justify-between text-sm">
            <p className="text-xs text-muted-foreground">
              {data.total} total traces
            </p>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="h-8 text-xs"
              >
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => p + 1)}
                disabled={!data.has_next}
                className="h-8 text-xs"
              >
                Next
              </Button>
            </div>
          </div>
        )}
      </main>
    </>
  );
}
