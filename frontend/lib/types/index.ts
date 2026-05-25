// Types mirroring the backend Pydantic schemas exactly

export type TicketStatus = "open" | "in_progress" | "escalated" | "closed";
export type TicketPriority = "low" | "medium" | "high" | "critical";
export type TicketSource = "api" | "email" | "chat" | "phone" | "web";
export type ApprovalDecision = "APPROVED" | "REJECTED";

export interface SourceAttribution {
  document_id: string;
  filename: string;
  chunk_index: number;
  similarity_score: number;
  retrieval_rank: number;
  semantic_score?: number;
  lexical_score?: number;
  rrf_score?: number;
  cross_encoder_score?: number;
  pre_rerank_rank?: number;
  post_rerank_rank?: number;
  used_for_generation: boolean;
  chunk_preview: string;
}

export interface TicketMetadata extends Record<string, unknown> {
  sources_used?: SourceAttribution[];
}

export interface Ticket {
  id: string;
  tenant_id: string;
  external_id: string | null;
  subject: string;
  description: string;
  status: TicketStatus;
  priority: TicketPriority;
  category: string | null;
  source: TicketSource;
  assigned_to: string | null;
  created_by: string | null;
  metadata: TicketMetadata;
  resolved_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface TicketListResponse {
  items: Ticket[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

export interface TicketCreateRequest {
  subject: string;
  description: string;
  priority?: TicketPriority;
  source?: TicketSource;
  category?: string;
  external_id?: string;
  metadata?: Record<string, unknown>;
}

export interface TicketProcessRequest {
  ticket_id: string;
  additional_context?: string;
}

export interface HumanReviewRequest {
  ticket_id: string;
  approval_decision: ApprovalDecision;
  agent_override_notes?: string;
  edited_response?: string;
}

// Analytics
export interface ResolutionAnalytics {
  auto_resolved: number;
  escalated: number;
  open: number;
  closed: number;
  human_approved: number;
  human_rejected: number;
}

export interface HallucinationDistribution {
  range_0_0_2: number;
  range_0_2_0_4: number;
  range_0_4_0_6: number;
  range_0_6_0_8: number;
  range_0_8_1_0: number;
}

export interface HighLowTicket {
  id: string;
  subject: string;
  score: number;
}

export interface AIQualityAnalytics {
  distribution: HallucinationDistribution;
  avg_score: number;
  highest_tickets: HighLowTicket[];
  lowest_tickets: HighLowTicket[];
}

export interface WorkflowPath {
  path: string;
  frequency: number;
}

export interface WorkflowAnalytics {
  most_common_path: string;
  paths: WorkflowPath[];
  avg_nodes: number;
}

export interface HumanReviewAnalytics {
  approved: number;
  rejected: number;
  intervention_rate: number;
}

export interface TimeSeriesPoint {
  date: string;
  created: number;
  resolved: number;
  escalated: number;
}

export interface TimeBasedAnalytics {
  data: TimeSeriesPoint[];
}

export interface DashboardAnalyticsResponse {
  total_tickets: number;
  open_tickets: number;
  closed_tickets: number;
  escalated_tickets: number;
  auto_resolved_tickets: number;
  human_reviewed_tickets: number;
  resolution_rate: number;
  escalation_rate: number;
  avg_workflow_latency: number;
  avg_hallucination_score: number;

  resolution_analytics: ResolutionAnalytics;
  ai_quality_analytics: AIQualityAnalytics;
  workflow_analytics: WorkflowAnalytics;
  human_review_analytics: HumanReviewAnalytics;
  time_based_analytics: TimeBasedAnalytics;
}

// Evaluations
export interface EvaluationMetrics {
  total_evaluations: number;
  avg_faithfulness: number;
  avg_answer_relevancy: number;
  avg_context_precision: number;
  avg_context_recall: number;
  period_start: string | null;
  period_end: string | null;
}

export interface RetrievalMetrics {
  avg_latency_ms: number;
  median_latency_ms: number;
  p95_latency_ms: number;
  avg_top1_similarity: number;
  avg_top3_similarity: number;
  avg_retrieved_chunks: number;
  avg_confidence_score: number;
}

export interface ResolutionMetrics {
  auto_resolution_rate: number;
  escalation_rate: number;
  avg_hallucination_score: number;
  avg_processing_time_ms: number;
}

export interface DocumentAnalytics {
  document_id: string | null;
  filename: string;
  retrieval_count: number;
  avg_similarity: number;
  avg_rank: number;
  auto_resolution_contribution: number;
  escalation_contribution: number;
  last_retrieved_at: string | null;
  days_since_last_retrieval: number | null;
}

export interface FailureAnalytics {
  no_source_count: number;
  no_source_percent: number;
  low_similarity_count: number;
  low_similarity_percent: number;
  hallucination_escalation_count: number;
  hallucination_escalation_percent: number;
  human_review_escalation_count: number;
  human_review_escalation_percent: number;
  confidence_escalation_count: number;
  confidence_escalation_percent: number;
}

export interface RetrievalEvaluationResponse {
  retrieval_health_score: number;
  retrieval_metrics: RetrievalMetrics;
  resolution_metrics: ResolutionMetrics;
  most_retrieved_documents: DocumentAnalytics[];
  least_retrieved_documents: DocumentAnalytics[];
  never_retrieved_documents: DocumentAnalytics[];
  failure_analytics: FailureAnalytics;
}

export interface TrendPoint {
  date: string;
  retrieval_health_score: number;
  avg_latency_ms: number;
  avg_similarity: number;
  hallucination_score: number;
  auto_resolution_rate: number;
  escalation_rate: number;
}

export interface RetrievalTrendsResponse {
  trends: TrendPoint[];
}

// Architecture
export interface NodeMetrics {
  id: string;
  status: "healthy" | "warning" | "inactive";
  avg_latency_ms: number;
  success_rate: number;
  volume_processed: number;
  custom_metrics: Record<string, any>;
}

export interface ArchitectureAnalyticsResponse {
  nodes: Record<string, NodeMetrics>;
}

// Workflow Traces
export interface WorkflowTraceResponse {
  id: string;
  ticket_id: string;
  status: string;
  nodes_visited: string[];
  total_latency_ms: number | null;
  created_at: string;
  
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  input_state: Record<string, any>;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  output_state: Record<string, any>;
  final_response: string | null;
  error_message: string | null;
}

export interface WorkflowTraceListResponse {
  items: WorkflowTraceResponse[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

// Knowledge Base
export interface KnowledgeDocumentMetadata {
  filename?: string;
  file_type?: string;
  chunk_count?: number;
  indexed_status?: "SUCCESS" | "PENDING" | "FAILED";
  processing_status?: "COMPLETED" | "PROCESSING" | "FAILED";
  last_indexed_at?: string;
  error?: string;
  [key: string]: unknown;
}

export interface KnowledgeArticle {
  id: string;
  tenant_id: string;
  title: string;
  content: string;
  category: string | null;
  metadata: KnowledgeDocumentMetadata;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeArticleListResponse {
  items: KnowledgeArticle[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}
