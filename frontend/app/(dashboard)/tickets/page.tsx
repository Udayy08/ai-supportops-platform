"use client";

import React, { useState } from "react";
import useSWR from "swr";
import Link from "next/link";
import { Plus, Search, X } from "lucide-react";
import { Header } from "@/components/layout/header";
import { StatusBadge, PriorityBadge } from "@/components/shared/status-badges";
import { TableSkeleton } from "@/components/shared/skeleton-loaders";
import { EmptyState } from "@/components/shared/empty-state";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { listTickets } from "@/lib/api/endpoints";
import { formatDateTime } from "@/lib/utils";
import type { TicketStatus, TicketPriority } from "@/lib/types";

export default function TicketsPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<TicketStatus | "all">("all");
  const [priority, setPriority] = useState<TicketPriority | "all">("all");

  const swrKey = `tickets?page=${page}&search=${search}&status=${status}&priority=${priority}`;

  const { data, isLoading } = useSWR(swrKey, () =>
    listTickets({
      page,
      page_size: 15,
      search: search || undefined,
      status: status !== "all" ? status : undefined,
      priority: priority !== "all" ? priority : undefined,
    })
  );

  const clearFilters = () => {
    setSearch("");
    setStatus("all");
    setPriority("all");
    setPage(1);
  };

  const hasFilters = search || status !== "all" || priority !== "all";

  return (
    <>
      <Header title="Tickets" description="Manage and track support tickets" />
      <main className="flex-1 p-6 space-y-4">
        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-48 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <Input
              placeholder="Search tickets..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              className="pl-8 h-9 text-sm"
            />
          </div>
          <Select value={status} onValueChange={(v) => { setStatus(v as TicketStatus | "all"); setPage(1); }}>
            <SelectTrigger className="w-36 h-9 text-sm">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="open">Open</SelectItem>
              <SelectItem value="in_progress">In Progress</SelectItem>
              <SelectItem value="escalated">Escalated</SelectItem>
              <SelectItem value="closed">Closed</SelectItem>
            </SelectContent>
          </Select>
          <Select value={priority} onValueChange={(v) => { setPriority(v as TicketPriority | "all"); setPage(1); }}>
            <SelectTrigger className="w-36 h-9 text-sm">
              <SelectValue placeholder="Priority" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Priority</SelectItem>
              <SelectItem value="low">Low</SelectItem>
              <SelectItem value="medium">Medium</SelectItem>
              <SelectItem value="high">High</SelectItem>
              <SelectItem value="critical">Critical</SelectItem>
            </SelectContent>
          </Select>
          {hasFilters && (
            <Button variant="ghost" size="sm" onClick={clearFilters} className="h-9 text-xs">
              <X className="h-3.5 w-3.5 mr-1" /> Clear
            </Button>
          )}
          <Button asChild size="sm" className="h-9 ml-auto text-sm">
            <Link href="/tickets/new">
              <Plus className="h-3.5 w-3.5 mr-1.5" /> New Ticket
            </Link>
          </Button>
        </div>

        {/* Table */}
        <div className="rounded-lg border bg-card shadow-sm overflow-hidden">
          {isLoading ? (
            <div className="p-6">
              <TableSkeleton rows={10} />
            </div>
          ) : !data?.items.length ? (
            <EmptyState
              title="No tickets found"
              description={hasFilters ? "Try adjusting your filters." : "Create your first ticket to get started."}
              action={
                !hasFilters && (
                  <Button size="sm" asChild>
                    <Link href="/tickets/new">Create Ticket</Link>
                  </Button>
                )
              }
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[300px]">Subject</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Priority</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Created</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.items.map((ticket) => (
                  <TableRow key={ticket.id} className="cursor-pointer hover:bg-muted/30">
                    <TableCell>
                      <Link
                        href={`/tickets/${ticket.id}`}
                        className="font-medium text-sm hover:underline"
                      >
                        {ticket.subject}
                      </Link>
                      <p className="text-xs text-muted-foreground mt-0.5 truncate max-w-xs">
                        {ticket.description}
                      </p>
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={ticket.status} />
                    </TableCell>
                    <TableCell>
                      <PriorityBadge priority={ticket.priority} />
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {ticket.category ?? "—"}
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground whitespace-nowrap">
                      {formatDateTime(ticket.created_at)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </div>

        {/* Pagination */}
        {data && data.total > 15 && (
          <div className="flex items-center justify-between text-sm">
            <p className="text-muted-foreground text-xs">
              Showing {(page - 1) * 15 + 1}–{Math.min(page * 15, data.total)} of {data.total} tickets
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
