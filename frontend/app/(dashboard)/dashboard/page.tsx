"use client";

import React from "react";
import useSWR from "swr";
import Link from "next/link";
import { ArrowRight, Ticket as TicketIcon, CheckCircle, AlertTriangle } from "lucide-react";
import { Header } from "@/components/layout/header";
import { MetricCard } from "@/components/shared/metric-card";
import { CardSkeleton, TableSkeleton } from "@/components/shared/skeleton-loaders";
import { StatusBadge } from "@/components/shared/status-badges";
import { EmptyState } from "@/components/shared/empty-state";
import { Button } from "@/components/ui/button";
import { getAnalyticsSummary, listTickets } from "@/lib/api/endpoints";
import { formatDateTime } from "@/lib/utils";
import type { DashboardAnalyticsResponse, Ticket } from "@/lib/types";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

export default function DashboardPage() {
  const { data: summary, isLoading: summaryLoading } =
    useSWR<DashboardAnalyticsResponse>("analytics/summary", getAnalyticsSummary);

  const { data: ticketsData, isLoading: ticketsLoading } = useSWR(
    "tickets/recent",
    () => listTickets({ page: 1, page_size: 6 })
  );

  const chartData = summary
    ? [
        { name: "Open", value: summary.open_tickets, color: "#3b82f6" },
        { name: "Resolved", value: summary.closed_tickets, color: "#10b981" },
        { name: "Escalated", value: summary.escalated_tickets, color: "#f97316" },
      ]
    : [];

  // Sparkline data
  const tsData = summary?.time_based_analytics?.data || [];
  const totalTrend = tsData.map((d) => ({ value: d.created }));
  const resolvedTrend = tsData.map((d) => ({ value: d.resolved }));
  const escalatedTrend = tsData.map((d) => ({ value: d.escalated }));

  return (
    <>
      <Header
        title="Dashboard"
        description="Overview of your AI support operations"
      />
      <main className="flex-1 p-6 space-y-6">
        {/* KPI Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {summaryLoading ? (
            Array.from({ length: 4 }).map((_, i) => <CardSkeleton key={i} />)
          ) : (
            <>
              <MetricCard
                title="Total Tickets"
                value={summary?.total_tickets ?? 0}
                subtitle="all time"
                chartData={totalTrend}
                chartColor="#8b5cf6"
              />
              <MetricCard
                title="Open Tickets"
                value={summary?.open_tickets ?? 0}
                subtitle="active"
              />
              <MetricCard
                title="Resolution Rate"
                value={summary?.resolution_rate ?? 0}
                isPercent
                trend="up"
                trendValue="+5.2%"
                chartData={resolvedTrend}
                chartColor="#10b981"
              />
              <MetricCard
                title="Escalation Rate"
                value={summary?.escalation_rate ?? 0}
                isPercent
                trend="down"
                trendValue="-1.1%"
                chartData={escalatedTrend}
                chartColor="#f97316"
              />
            </>
          )}
        </div>

        {/* Chart + Recent Tickets */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Chart */}
          <div className="lg:col-span-1 rounded-xl border bg-card p-5 shadow-sm">
            <p className="text-sm font-semibold mb-4">Ticket Distribution</p>
            {summaryLoading ? (
              <div className="h-40 flex items-center justify-center">
                <div className="h-32 w-full animate-pulse bg-muted rounded" />
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={160}>
                <BarChart data={chartData} barSize={28}>
                  <XAxis
                    dataKey="name"
                    tick={{ fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis hide />
                  <Tooltip
                    contentStyle={{
                      fontSize: 12,
                      border: "1px solid hsl(var(--border))",
                      borderRadius: 6,
                    }}
                  />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                    {chartData.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Recent Tickets */}
          <div className="lg:col-span-2 rounded-xl border bg-card shadow-sm overflow-hidden flex flex-col">
            <div className="flex items-center justify-between px-5 py-4 border-b bg-muted/20">
              <p className="text-sm font-semibold">Recent Tickets</p>
              <Button variant="ghost" size="sm" asChild className="text-xs h-7">
                <Link href="/tickets">
                  View all <ArrowRight className="h-3 w-3 ml-1" />
                </Link>
              </Button>
            </div>
            {ticketsLoading ? (
              <div className="p-5">
                <TableSkeleton rows={5} />
              </div>
            ) : !ticketsData?.items.length ? (
              <EmptyState
                title="No tickets yet"
                description="Create your first ticket to get started."
                action={
                  <Button size="sm" asChild>
                    <Link href="/tickets/new">Create Ticket</Link>
                  </Button>
                }
              />
            ) : (
              <div className="divide-y">
                {ticketsData.items.map((ticket: Ticket) => (
                  <Link
                    key={ticket.id}
                    href={`/tickets/${ticket.id}`}
                    className="flex items-center justify-between px-5 py-3 hover:bg-muted/50 transition-colors group"
                  >
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium truncate group-hover:text-primary transition-colors">
                        {ticket.subject}
                      </p>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {formatDateTime(ticket.created_at)}
                      </p>
                    </div>
                    <div className="ml-4 shrink-0">
                      <StatusBadge status={ticket.status} />
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Quick stats row */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="rounded-xl border bg-card p-5 flex items-center gap-4 shadow-sm hover:shadow-md transition-shadow">
            <div className="h-10 w-10 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center shrink-0">
              <TicketIcon className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Avg Latency</p>
              <p className="text-lg font-semibold">
                {summary ? `${Math.round(summary.avg_workflow_latency)}ms` : "—"}
              </p>
            </div>
          </div>
          <div className="rounded-xl border bg-card p-5 flex items-center gap-4 shadow-sm hover:shadow-md transition-shadow">
            <div className="h-10 w-10 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center shrink-0">
              <CheckCircle className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Closed Total</p>
              <p className="text-lg font-semibold">{summary?.closed_tickets ?? 0}</p>
            </div>
          </div>
          <div className="rounded-xl border bg-card p-5 flex items-center gap-4 shadow-sm hover:shadow-md transition-shadow">
            <div className="h-10 w-10 rounded-full bg-orange-100 dark:bg-orange-900/30 flex items-center justify-center shrink-0">
              <AlertTriangle className="h-5 w-5 text-orange-600 dark:text-orange-400" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Escalated</p>
              <p className="text-lg font-semibold">{summary?.escalated_tickets ?? 0}</p>
            </div>
          </div>
        </div>
      </main>
    </>
  );
}
