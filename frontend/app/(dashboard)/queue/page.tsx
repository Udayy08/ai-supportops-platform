"use client";

import React from "react";
import useSWR from "swr";
import Link from "next/link";
import { CheckCircle, AlertTriangle, ArrowRight } from "lucide-react";
import { Header } from "@/components/layout/header";
import { PriorityBadge } from "@/components/shared/status-badges";
import { TableSkeleton } from "@/components/shared/skeleton-loaders";
import { EmptyState } from "@/components/shared/empty-state";
import { Button } from "@/components/ui/button";
import { listTickets } from "@/lib/api/endpoints";
import { formatDateTime } from "@/lib/utils";

export default function QueuePage() {
  const { data, isLoading } = useSWR("queue/escalated", () =>
    listTickets({ status: "escalated", page: 1, page_size: 50 })
  );

  return (
    <>
      <Header
        title="Review Queue"
        description="Escalated tickets awaiting human approval"
      />
      <main className="flex-1 p-6 space-y-4">
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-orange-500" />
          <p className="text-sm text-muted-foreground">
            {isLoading ? "Loading..." : `${data?.total ?? 0} ticket${data?.total !== 1 ? "s" : ""} awaiting review`}
          </p>
        </div>

        {isLoading ? (
          <div className="rounded-lg border bg-card p-6">
            <TableSkeleton rows={6} />
          </div>
        ) : !data?.items.length ? (
          <div className="rounded-lg border bg-card">
            <EmptyState
              title="No tickets in queue"
              description="All escalated tickets have been reviewed. Check back later."
              icon={<CheckCircle className="h-8 w-8 text-emerald-500" />}
            />
          </div>
        ) : (
          <div className="space-y-2">
            {data.items.map((ticket) => (
              <div
                key={ticket.id}
                className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-lg border bg-card px-5 py-4 shadow-sm hover:border-blue-500/50 transition-colors"
              >
                <div className="min-w-0 flex-1">
                  <Link
                    href={`/queue/${ticket.id}`}
                    className="text-sm font-semibold hover:underline flex items-center gap-2"
                  >
                    {ticket.subject}
                  </Link>
                  <div className="flex items-center gap-3 mt-1.5">
                    <PriorityBadge priority={ticket.priority} />
                    <span className="text-xs text-muted-foreground">
                      Escalated {formatDateTime(ticket.updated_at)}
                    </span>
                  </div>
                </div>
                <div className="flex gap-2 shrink-0">
                  <Button
                    size="sm"
                    asChild
                  >
                    <Link href={`/queue/${ticket.id}`}>
                      Review
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </Link>
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </>
  );
}
