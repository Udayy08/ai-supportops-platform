import api from "./client";
import type {
  ArchitectureAnalyticsResponse,
  DashboardAnalyticsResponse,
  EvaluationMetrics,
  HumanReviewRequest,
  KnowledgeArticle,
  KnowledgeArticleListResponse,
  Ticket,
  TicketCreateRequest,
  TicketListResponse,
  TicketProcessRequest,
  WorkflowTraceListResponse,
  WorkflowTraceResponse,
} from "@/lib/types";

// ── Tickets ───────────────────────────────────────────────────────────────────

export async function listTickets(params?: {
  page?: number;
  page_size?: number;
  status?: string;
  priority?: string;
  search?: string;
}): Promise<TicketListResponse> {
  const { data } = await api.get("/tickets", { params });
  return data;
}

export async function getTicket(id: string): Promise<Ticket> {
  const { data } = await api.get(`/tickets/${id}`);
  return data;
}

export async function createTicket(body: TicketCreateRequest): Promise<Ticket> {
  const { data } = await api.post("/tickets", body);
  return data;
}

export async function processTicket(
  body: TicketProcessRequest
): Promise<{ status: string; ticket_id: string; message: string }> {
  const { data } = await api.post("/tickets/process", body);
  return data;
}

export async function humanReviewTicket(
  ticketId: string,
  body: HumanReviewRequest
): Promise<Ticket> {
  const { data } = await api.post(`/tickets/${ticketId}/human-review`, body);
  return data;
}

// ── Analytics ─────────────────────────────────────────────────────────────────

export async function getAnalyticsSummary(): Promise<DashboardAnalyticsResponse> {
  const { data } = await api.get("/analytics/summary");
  return data;
}

export async function getArchitectureMetrics(): Promise<ArchitectureAnalyticsResponse> {
  const { data } = await api.get("/analytics/architecture");
  return data;
}

// ── Evaluations ───────────────────────────────────────────────────────────────

export async function getEvaluationMetrics(): Promise<EvaluationMetrics> {
  const { data } = await api.get("/evaluations/metrics");
  return data;
}

import type { RetrievalEvaluationResponse, RetrievalTrendsResponse } from "@/lib/types";

export async function getRetrievalEvaluationMetrics(): Promise<RetrievalEvaluationResponse> {
  const { data } = await api.get("/evaluations/retrieval");
  return data;
}

export async function getRetrievalTrends(): Promise<RetrievalTrendsResponse> {
  const { data } = await api.get("/evaluations/retrieval/trends");
  return data;
}

// ── Workflow Traces ───────────────────────────────────────────────────────────

export async function listWorkflowTraces(params?: {
  page?: number;
  page_size?: number;
}): Promise<WorkflowTraceListResponse> {
  const { data } = await api.get("/workflow/traces", { params });
  return data;
}

export async function getWorkflowTrace(id: string): Promise<WorkflowTraceResponse> {
  const { data } = await api.get(`/workflow/traces/${id}`);
  return data;
}

// ── Knowledge Base ────────────────────────────────────────────────────────────

export async function listKnowledgeArticles(params?: {
  page?: number;
  page_size?: number;
  category?: string;
  search?: string;
}): Promise<KnowledgeArticleListResponse> {
  const { data } = await api.get("/knowledge", { params });
  return data;
}

export async function getKnowledgeDocument(id: string): Promise<KnowledgeArticle> {
  const { data } = await api.get(`/knowledge/${id}`);
  return data;
}

export async function uploadKnowledgeDocument(
  file: File,
  category?: string
): Promise<KnowledgeArticle> {
  const formData = new FormData();
  formData.append("file", file);
  if (category) {
    formData.append("category", category);
  }

  const { data } = await api.post("/knowledge/upload", formData, {
    transformRequest: [(data, headers) => {
      delete headers["Content-Type"];
      return data;
    }],
  });
  return data;
}

export async function deleteKnowledgeDocument(id: string): Promise<void> {
  await api.delete(`/knowledge/${id}`);
}

export async function reindexKnowledgeDocument(id: string): Promise<KnowledgeArticle> {
  const { data } = await api.post(`/knowledge/${id}/reindex`);
  return data;
}

export async function refreshKnowledgeDocument(id: string): Promise<KnowledgeArticle> {
  const { data } = await api.post(`/knowledge/${id}/refresh`);
  return data;
}
