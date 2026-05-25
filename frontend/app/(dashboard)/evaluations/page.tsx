"use client";

import React from "react";
import useSWR from "swr";
import { Header } from "@/components/layout/header";
import { MetricCard } from "@/components/shared/metric-card";
import { CardSkeleton } from "@/components/shared/skeleton-loaders";
import { TrendChart } from "@/components/shared/trend-chart";
import { getRetrievalEvaluationMetrics, getRetrievalTrends } from "@/lib/api/endpoints";
import type { RetrievalEvaluationResponse, RetrievalTrendsResponse } from "@/lib/types";
import { FileText, Search, Activity, AlertTriangle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export default function EvaluationsPage() {
  const { data: metrics, isLoading: loadingMetrics } =
    useSWR<RetrievalEvaluationResponse>("evaluations/retrieval", getRetrievalEvaluationMetrics);
    
  const { data: trendsData, isLoading: loadingTrends } =
    useSWR<RetrievalTrendsResponse>("evaluations/retrieval/trends", getRetrievalTrends);

  return (
    <>
      <Header
        title="Retrieval Evaluation Dashboard"
        description="Quantitative baselines and historical trends for RAG retrieval performance."
      />
      <main className="flex-1 p-6 space-y-8 max-w-[1600px] mx-auto w-full">
        
        {/* KPI Section */}
        <section className="space-y-4">
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-emerald-500" />
            <h2 className="text-lg font-semibold">Key Performance Indicators</h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {loadingMetrics || !metrics ? (
              Array.from({ length: 4 }).map((_, i) => <CardSkeleton key={i} />)
            ) : (
              <>
                <MetricCard
                  title="Retrieval Health Score"
                  value={metrics.retrieval_health_score}
                  subtitle="Overall retrieval quality (0-100)"
                  trend="up"
                  trendValue="0"
                />
                <MetricCard
                  title="Avg Top-1 Similarity"
                  value={`${(metrics.retrieval_metrics.avg_top1_similarity * 100).toFixed(1)}%`}
                  subtitle="Top chunk relevance"
                />
                <MetricCard
                  title="Auto Resolution Rate"
                  value={`${(metrics.resolution_metrics.auto_resolution_rate * 100).toFixed(1)}%`}
                  subtitle="Tickets resolved without human"
                />
                <MetricCard
                  title="Avg Hallucination Score"
                  value={metrics.resolution_metrics.avg_hallucination_score.toFixed(2)}
                  subtitle="Lower is better"
                />
                <MetricCard
                  title="Avg Confidence Score"
                  value={metrics.retrieval_metrics.avg_confidence_score.toFixed(2)}
                  subtitle="Cross-Encoder (Target > -6.0)"
                />
              </>
            )}
          </div>
        </section>

        {/* Trend Charts */}
        <section className="space-y-4">
          <div className="flex items-center gap-2">
            <Search className="h-5 w-5 text-blue-500" />
            <h2 className="text-lg font-semibold">Historical Trends</h2>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {loadingTrends || !trendsData ? (
              Array.from({ length: 3 }).map((_, i) => <div key={i} className="h-[280px] bg-muted/50 rounded-lg animate-pulse" />)
            ) : (
              <>
                <TrendChart 
                  data={trendsData.trends} 
                  dataKey="retrieval_health_score" 
                  title="Health Score" 
                  color="#10b981" 
                />
                <TrendChart 
                  data={trendsData.trends} 
                  dataKey="avg_similarity" 
                  title="Avg Similarity" 
                  color="#3b82f6" 
                  isPercentage={false}
                />
                <TrendChart 
                  data={trendsData.trends} 
                  dataKey="avg_latency_ms" 
                  title="Avg Latency (ms)" 
                  color="#f59e0b" 
                />
              </>
            )}
          </div>
        </section>

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
          
          {/* Document Analytics Table */}
          <section className="xl:col-span-2 space-y-4">
            <div className="flex items-center gap-2 mb-2">
              <FileText className="h-5 w-5 text-purple-500" />
              <h2 className="text-lg font-semibold">Top Retrieved Documents</h2>
            </div>
            
            <div className="rounded-xl border bg-card shadow-sm overflow-hidden">
              <div className="divide-y">
                {loadingMetrics ? (
                  <div className="p-8 text-center text-muted-foreground">Loading documents...</div>
                ) : metrics?.most_retrieved_documents.length === 0 ? (
                  <div className="p-8 text-center text-muted-foreground">No documents retrieved yet.</div>
                ) : (
                  metrics?.most_retrieved_documents.map((doc, i) => (
                    <div key={i} className="p-4 hover:bg-muted/30 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                      <div className="flex items-center gap-3 flex-1 min-w-0">
                        <div className="h-8 w-8 rounded-full bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center shrink-0">
                          <span className="text-sm font-bold text-purple-700 dark:text-purple-400">#{i + 1}</span>
                        </div>
                        <div className="min-w-0">
                          <p className="font-semibold text-sm truncate">{doc.filename}</p>
                          <p className="text-xs text-muted-foreground mt-0.5">{doc.retrieval_count} retrievals • Avg Rank: {doc.avg_rank.toFixed(1)}</p>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-6 shrink-0">
                        <div className="text-right">
                          <p className="text-[10px] uppercase text-muted-foreground font-semibold mb-1">Avg Sim</p>
                          <Badge variant="soft-success" className={cn(
                            "font-mono",
                            doc.avg_similarity < 0.6 && "bg-red-100 text-red-800 border-red-200 dark:bg-red-900/30 dark:text-red-400 dark:border-red-800",
                            doc.avg_similarity >= 0.6 && doc.avg_similarity < 0.8 && "bg-amber-100 text-amber-800 border-amber-200 dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-800"
                          )}>
                            {(doc.avg_similarity * 100).toFixed(1)}%
                          </Badge>
                        </div>
                        
                        <div className="text-right w-16">
                          <p className="text-[10px] uppercase text-muted-foreground font-semibold mb-1">Auto Res</p>
                          <p className="text-sm font-bold text-emerald-600 dark:text-emerald-400">{doc.auto_resolution_contribution}</p>
                        </div>
                        
                        <div className="text-right w-16">
                          <p className="text-[10px] uppercase text-muted-foreground font-semibold mb-1">Escalated</p>
                          <p className="text-sm font-bold text-red-600 dark:text-red-400">{doc.escalation_contribution}</p>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
            
            {/* Never Retrieved Section */}
            {!loadingMetrics && metrics && metrics.never_retrieved_documents.length > 0 && (
              <div className="mt-6">
                <h3 className="text-sm font-semibold mb-3 flex items-center gap-2 text-muted-foreground">
                  <AlertTriangle className="h-4 w-4 text-amber-500" />
                  Never Retrieved Documents
                </h3>
                <div className="flex flex-wrap gap-2">
                  {metrics.never_retrieved_documents.map((doc, i) => (
                    <Badge key={i} variant="secondary" className="px-3 py-1 font-normal bg-amber-50 text-amber-800 dark:bg-amber-950 dark:text-amber-300 border-amber-200">
                      {doc.filename}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </section>

          {/* Failure Analytics */}
          <section className="space-y-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-red-500" />
              <h2 className="text-lg font-semibold">Failure Analytics</h2>
            </div>
            
            {loadingMetrics || !metrics ? (
              <CardSkeleton />
            ) : (
              <div className="rounded-xl border bg-card shadow-sm overflow-hidden">
                <div className="p-5 grid grid-cols-2 gap-y-6 gap-x-4 text-sm bg-muted/10">
                  
                  <div className="space-y-1.5 bg-background p-3 rounded-lg border shadow-sm">
                    <p className="text-muted-foreground text-[10px] font-semibold uppercase tracking-wide">No Source Found</p>
                    <div className="flex items-baseline justify-between">
                      <span className="text-2xl font-bold">{metrics.failure_analytics.no_source_count}</span>
                      <span className="text-xs font-medium text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
                        {(metrics.failure_analytics.no_source_percent * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  
                  <div className="space-y-1.5 bg-background p-3 rounded-lg border shadow-sm">
                    <p className="text-muted-foreground text-[10px] font-semibold uppercase tracking-wide">Low Similarity</p>
                    <div className="flex items-baseline justify-between">
                      <span className="text-2xl font-bold">{metrics.failure_analytics.low_similarity_count}</span>
                      <span className="text-xs font-medium text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
                        {(metrics.failure_analytics.low_similarity_percent * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  
                  <div className="space-y-1.5 bg-red-50/50 dark:bg-red-950/20 p-3 rounded-lg border border-red-100 dark:border-red-900 shadow-sm">
                    <p className="text-red-600 dark:text-red-400 text-[10px] font-semibold uppercase tracking-wide">Hallucination Esc.</p>
                    <div className="flex items-baseline justify-between">
                      <span className="text-2xl font-bold text-red-600 dark:text-red-400">{metrics.failure_analytics.hallucination_escalation_count}</span>
                      <span className="text-xs font-medium text-red-700 bg-red-100 dark:bg-red-900/50 dark:text-red-300 px-1.5 py-0.5 rounded">
                        {(metrics.failure_analytics.hallucination_escalation_percent * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  
                  <div className="space-y-1.5 bg-amber-50/50 dark:bg-amber-950/20 p-3 rounded-lg border border-amber-100 dark:border-amber-900 shadow-sm">
                    <p className="text-amber-600 dark:text-amber-400 text-[10px] font-semibold uppercase tracking-wide">Human Review Esc.</p>
                    <div className="flex items-baseline justify-between">
                      <span className="text-2xl font-bold text-amber-600 dark:text-amber-400">{metrics.failure_analytics.human_review_escalation_count}</span>
                      <span className="text-xs font-medium text-amber-700 bg-amber-100 dark:bg-amber-900/50 dark:text-amber-300 px-1.5 py-0.5 rounded">
                        {(metrics.failure_analytics.human_review_escalation_percent * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  
                  <div className="space-y-1.5 col-span-2 bg-orange-50/50 dark:bg-orange-950/20 p-3 rounded-lg border border-orange-100 dark:border-orange-900 shadow-sm">
                    <p className="text-orange-600 dark:text-orange-400 text-[10px] font-semibold uppercase tracking-wide">Confidence Esc.</p>
                    <div className="flex items-baseline justify-between">
                      <span className="text-2xl font-bold text-orange-600 dark:text-orange-400">{metrics.failure_analytics.confidence_escalation_count}</span>
                      <span className="text-xs font-medium text-orange-700 bg-orange-100 dark:bg-orange-900/50 dark:text-orange-300 px-1.5 py-0.5 rounded">
                        {(metrics.failure_analytics.confidence_escalation_percent * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  
                </div>
              </div>
            )}
            
            {/* Additional Metrics Box */}
            {metrics && (
              <div className="rounded-xl border bg-card shadow-sm p-5 mt-4 space-y-4 text-sm bg-muted/5">
                <h3 className="font-semibold border-b pb-2 text-muted-foreground uppercase text-xs tracking-wider">Retrieval Averages</h3>
                <dl className="grid grid-cols-2 gap-y-4 gap-x-2">
                  <dt className="text-muted-foreground font-medium">Avg Latency</dt>
                  <dd className="font-mono font-semibold text-right">{metrics.retrieval_metrics.avg_latency_ms.toFixed(0)} ms</dd>
                  
                  <dt className="text-muted-foreground font-medium">P95 Latency</dt>
                  <dd className="font-mono font-semibold text-right">{metrics.retrieval_metrics.p95_latency_ms.toFixed(0)} ms</dd>
                  
                  <dt className="text-muted-foreground font-medium">Avg Top-3 Sim</dt>
                  <dd className="font-mono font-semibold text-right text-blue-600 dark:text-blue-400">{(metrics.retrieval_metrics.avg_top3_similarity * 100).toFixed(1)}%</dd>
                  
                  <dt className="text-muted-foreground font-medium">Avg Chunks/Query</dt>
                  <dd className="font-mono font-semibold text-right">{metrics.retrieval_metrics.avg_retrieved_chunks.toFixed(1)}</dd>
                </dl>
              </div>
            )}
          </section>

        </div>
      </main>
    </>
  );
}
