"use client";

import React from "react";
import useSWR from "swr";
import { Header } from "@/components/layout/header";
import { MetricCard } from "@/components/shared/metric-card";
import { CardSkeleton } from "@/components/shared/skeleton-loaders";
import { getAnalyticsSummary } from "@/lib/api/endpoints";
import type { DashboardAnalyticsResponse } from "@/lib/types";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
  LineChart,
  Line,
  CartesianGrid
} from "recharts";

const COLORS = ["#3b82f6", "#10b981", "#f97316", "#ef4444", "#8b5cf6", "#64748b"];

export default function AnalyticsPage() {
  const { data: summary, isLoading } =
    useSWR<DashboardAnalyticsResponse>("analytics/summary-page", getAnalyticsSummary);

  const statusDistributionData = summary
    ? [
        { name: "Open", value: summary.resolution_analytics.open, color: "#3b82f6" },
        { name: "Closed", value: summary.resolution_analytics.closed, color: "#10b981" },
        { name: "Escalated", value: summary.resolution_analytics.escalated, color: "#f97316" },
      ].filter((d) => d.value > 0)
    : [];

  const resolutionVsEscalationData = summary
    ? [
        { name: "Auto Resolved", value: summary.resolution_analytics.auto_resolved, color: "#10b981" },
        { name: "Escalated", value: summary.resolution_analytics.escalated, color: "#f97316" },
      ]
    : [];

  const humanReviewData = summary
    ? [
        { name: "Approved", value: summary.human_review_analytics.approved, color: "#10b981" },
        { name: "Rejected", value: summary.human_review_analytics.rejected, color: "#ef4444" },
      ]
    : [];

  const hallucinationDistributionData = summary
    ? [
        { name: "0 - 0.2", value: summary.ai_quality_analytics.distribution.range_0_0_2 },
        { name: "0.2 - 0.4", value: summary.ai_quality_analytics.distribution.range_0_2_0_4 },
        { name: "0.4 - 0.6", value: summary.ai_quality_analytics.distribution.range_0_4_0_6 },
        { name: "0.6 - 0.8", value: summary.ai_quality_analytics.distribution.range_0_6_0_8 },
        { name: "0.8 - 1.0", value: summary.ai_quality_analytics.distribution.range_0_8_1_0 },
      ]
    : [];

  const timeSeriesData = summary ? [...summary.time_based_analytics.data].reverse() : [];

  return (
    <>
      <Header
        title="Analytics Dashboard"
        description="Comprehensive metrics and trends for AI SupportOps"
      />
      <main className="flex-1 p-6 space-y-8 max-w-[1600px] mx-auto w-full">
        {/* Top KPIs */}
        <div>
          <h2 className="text-lg font-semibold mb-4">Key Performance Indicators</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {isLoading ? (
              Array.from({ length: 10 }).map((_, i) => <CardSkeleton key={i} />)
            ) : summary ? (
              <>
                <MetricCard title="Total Tickets" value={summary.total_tickets} />
                <MetricCard title="Open Tickets" value={summary.open_tickets} />
                <MetricCard title="Closed Tickets" value={summary.closed_tickets} />
                <MetricCard title="Escalated Tickets" value={summary.escalated_tickets} />
                <MetricCard title="Resolution Rate" value={summary.resolution_rate} isPercent />
                <MetricCard title="Auto Resolved" value={summary.auto_resolved_tickets} />
                <MetricCard title="Human Reviewed" value={summary.human_reviewed_tickets} />
                <MetricCard title="Escalation Rate" value={summary.escalation_rate} isPercent />
                <MetricCard title="Avg Latency" value={`${Math.round(summary.avg_workflow_latency)} ms`} />
                <MetricCard title="Avg Hallucination" value={summary.avg_hallucination_score.toFixed(2)} />
              </>
            ) : null}
          </div>
        </div>

        {/* Charts Row 1 */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Resolution Types */}
          <div className="rounded-lg border bg-card p-5 shadow-sm col-span-1">
            <h3 className="text-sm font-semibold mb-4">Auto vs Escalated</h3>
            {isLoading ? (
              <div className="h-64 bg-muted animate-pulse rounded" />
            ) : resolutionVsEscalationData.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-12">No data available</p>
            ) : (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={resolutionVsEscalationData}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      label={({ name, value }) => `${name}: ${value}`}
                    >
                      {resolutionVsEscalationData.map((entry, i) => (
                        <Cell key={i} fill={entry.color} />
                      ))}
                    </Pie>
                    <Legend iconType="circle" />
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          {/* Time Based Analytics */}
          <div className="rounded-lg border bg-card p-5 shadow-sm col-span-1 lg:col-span-2">
            <h3 className="text-sm font-semibold mb-4">Tickets Over Time (Last 30 Days)</h3>
            {isLoading ? (
              <div className="h-64 bg-muted animate-pulse rounded" />
            ) : (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={timeSeriesData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                    <XAxis dataKey="date" tick={{ fontSize: 11 }} tickMargin={10} minTickGap={30} />
                    <YAxis tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                    <Tooltip />
                    <Legend iconType="circle" wrapperStyle={{ fontSize: 12 }} />
                    <Line type="monotone" dataKey="created" stroke="#3b82f6" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="resolved" stroke="#10b981" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="escalated" stroke="#f97316" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        </div>

        {/* Charts Row 2 */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Status Breakdown */}
          <div className="rounded-lg border bg-card p-5 shadow-sm">
            <h3 className="text-sm font-semibold mb-4">Ticket Statuses</h3>
            {isLoading ? (
              <div className="h-64 bg-muted animate-pulse rounded" />
            ) : (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={statusDistributionData}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={5}
                    >
                      {statusDistributionData.map((entry, i) => (
                        <Cell key={i} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend iconType="circle" />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          {/* AI Quality - Hallucination */}
          <div className="rounded-lg border bg-card p-5 shadow-sm">
            <h3 className="text-sm font-semibold mb-4">Hallucination Score Distribution</h3>
            {isLoading ? (
              <div className="h-64 bg-muted animate-pulse rounded" />
            ) : (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={hallucinationDistributionData} margin={{ top: 20 }}>
                    <XAxis dataKey="name" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fontSize: 11 }} axisLine={false} tickLine={false} allowDecimals={false} />
                    <Tooltip cursor={{ fill: "transparent" }} />
                    <Bar dataKey="value" fill="#8b5cf6" radius={[4, 4, 0, 0]} barSize={40} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          {/* Human Review Outcomes */}
          <div className="rounded-lg border bg-card p-5 shadow-sm">
            <h3 className="text-sm font-semibold mb-4">Human Review Outcomes</h3>
            {isLoading ? (
              <div className="h-64 bg-muted animate-pulse rounded" />
            ) : humanReviewData.length === 0 || (summary && summary.human_reviewed_tickets === 0) ? (
              <p className="text-sm text-muted-foreground text-center py-12">No human reviews yet</p>
            ) : (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={humanReviewData} layout="vertical" margin={{ left: 20 }}>
                    <XAxis type="number" hide />
                    <YAxis dataKey="name" type="category" tick={{ fontSize: 12 }} axisLine={false} tickLine={false} />
                    <Tooltip cursor={{ fill: "transparent" }} />
                    <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={30}>
                      {humanReviewData.map((entry, i) => (
                        <Cell key={i} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        </div>

        {/* Bottom Section: Tables and Lists */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Workflow Paths */}
          <div className="rounded-lg border bg-card p-5 shadow-sm overflow-hidden flex flex-col">
            <h3 className="text-sm font-semibold mb-4">Workflow Analytics</h3>
            {isLoading ? (
              <div className="h-48 bg-muted animate-pulse rounded" />
            ) : summary ? (
              <div className="flex-1 overflow-auto">
                <div className="mb-4">
                  <p className="text-xs text-muted-foreground">Most Common Path</p>
                  <p className="text-sm font-mono mt-1 break-words bg-muted p-2 rounded">{summary.workflow_analytics.most_common_path}</p>
                </div>
                <p className="text-xs text-muted-foreground mb-2">Path Frequencies</p>
                <div className="space-y-2">
                  {summary.workflow_analytics.paths.slice(0, 5).map((path, idx) => (
                    <div key={idx} className="flex items-center justify-between text-sm p-2 hover:bg-muted/50 rounded transition-colors">
                      <span className="font-mono text-xs truncate mr-4" title={path.path}>{path.path}</span>
                      <span className="font-semibold">{path.frequency}</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </div>

          {/* High/Low Hallucination Tickets */}
          <div className="rounded-lg border bg-card p-5 shadow-sm overflow-hidden flex flex-col">
            <h3 className="text-sm font-semibold mb-4">AI Quality Extremes</h3>
            {isLoading ? (
              <div className="h-48 bg-muted animate-pulse rounded" />
            ) : summary ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 flex-1 overflow-auto">
                <div>
                  <p className="text-xs font-semibold text-red-500 mb-2">Highest Hallucination Risk</p>
                  <div className="space-y-2">
                    {summary.ai_quality_analytics.highest_tickets.map((t) => (
                      <div key={t.id} className="text-sm p-2 bg-red-500/10 rounded flex flex-col">
                        <span className="truncate font-medium">{t.subject}</span>
                        <span className="text-xs text-muted-foreground mt-1">Score: {t.score.toFixed(2)}</span>
                      </div>
                    ))}
                    {summary.ai_quality_analytics.highest_tickets.length === 0 && <p className="text-xs text-muted-foreground">No scored tickets.</p>}
                  </div>
                </div>
                <div>
                  <p className="text-xs font-semibold text-green-500 mb-2">Lowest Hallucination Risk</p>
                  <div className="space-y-2">
                    {summary.ai_quality_analytics.lowest_tickets.map((t) => (
                      <div key={t.id} className="text-sm p-2 bg-green-500/10 rounded flex flex-col">
                        <span className="truncate font-medium">{t.subject}</span>
                        <span className="text-xs text-muted-foreground mt-1">Score: {t.score.toFixed(2)}</span>
                      </div>
                    ))}
                    {summary.ai_quality_analytics.lowest_tickets.length === 0 && <p className="text-xs text-muted-foreground">No scored tickets.</p>}
                  </div>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      </main>
    </>
  );
}
