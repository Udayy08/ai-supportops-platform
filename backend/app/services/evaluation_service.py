import uuid
from datetime import datetime, date, timezone
from collections import defaultdict

from sqlalchemy import select, func, Float, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ticket import Ticket, TicketStatus
from app.models.knowledge_article import KnowledgeArticle
from app.models.retrieval_snapshot import RetrievalEvaluationSnapshot
from app.schemas.evaluation import (
    RetrievalEvaluationResponse,
    RetrievalMetrics,
    ResolutionMetrics,
    DocumentAnalytics,
    FailureAnalytics,
    TrendPoint,
    RetrievalTrendsResponse
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class EvaluationService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_retrieval_evaluation(self, tenant_id: uuid.UUID) -> RetrievalEvaluationResponse:
        """Aggregate retrieval data from Tickets and generate dashboard payload."""
        
        # 1. Fetch tickets with workflow traces (those with metadata_)
        stmt = select(Ticket).where(
            Ticket.tenant_id == tenant_id,
            Ticket.metadata_ != {}
        )
        result = await self.session.execute(stmt)
        tickets = result.scalars().all()

        if not tickets:
            empty_resp = self._empty_response()
            
            # Fetch all knowledge articles to populate never_retrieved_documents
            kb_stmt = select(KnowledgeArticle).where(KnowledgeArticle.tenant_id == tenant_id)
            kb_result = await self.session.execute(kb_stmt)
            all_articles = kb_result.scalars().all()
            for a in all_articles:
                empty_resp.never_retrieved_documents.append(DocumentAnalytics(
                    document_id=str(a.id),
                    filename=a.title,
                    retrieval_count=0,
                    avg_similarity=0.0,
                    avg_rank=0.0,
                    auto_resolution_contribution=0,
                    escalation_contribution=0,
                    last_retrieved_at=None,
                    days_since_last_retrieval=None
                ))
            
            await self._save_snapshot(tenant_id, empty_resp)
            return empty_resp

        # Metrics accumulators
        latencies = []
        top1_similarities = []
        top3_similarities = []
        chunk_counts = []
        
        processing_times = []
        hallucination_scores = []
        
        auto_resolved_count = 0
        escalated_count = 0
        
        no_source_count = 0
        low_similarity_count = 0
        hallucination_escalation_count = 0
        human_review_escalation_count = 0
        confidence_escalation_count = 0
        
        # Document tracking
        # doc_id -> { filename, count, sim_sum, rank_sum, auto_res_count, esc_count, last_retrieved }
        doc_stats = defaultdict(lambda: {
            "filename": "",
            "count": 0,
            "sim_sum": 0.0,
            "rank_sum": 0,
            "auto_res_count": 0,
            "esc_count": 0,
            "last_retrieved": None
        })

        for t in tickets:
            meta = t.metadata_
            status = t.status
            disposition = meta.get("workflow_final_disposition")
            
            # Resolution Metrics
            if disposition == "auto_resolved" or status == TicketStatus.CLOSED:
                auto_resolved_count += 1
            elif disposition == "escalated" or status == TicketStatus.ESCALATED:
                escalated_count += 1
                
                # Check escalation reason
                h_score = meta.get("hallucination_score")
                if (h_score if h_score is not None else 0.0) > 0.5:
                    hallucination_escalation_count += 1
                else:
                    human_review_escalation_count += 1
            
            if "workflow_latency_ms" in meta and meta["workflow_latency_ms"] is not None:
                processing_times.append(meta["workflow_latency_ms"])
                
            if "hallucination_score" in meta and meta["hallucination_score"] is not None:
                hallucination_scores.append(meta["hallucination_score"])
                
            # Retrieval Metrics
            retrieval = meta.get("retrieval_debug")
            sources = meta.get("sources_used", [])
            
            if retrieval:
                if retrieval.get("retrieval_latency_ms") is not None:
                    latencies.append(retrieval["retrieval_latency_ms"])
                chunk_counts.append(len(sources))
                
                # Check confidence escalation
                if retrieval.get("confidence_decision") == "escalated":
                    confidence_escalation_count += 1
            
            if not sources:
                no_source_count += 1
            else:
                sims = [(s.get("similarity_score") if s.get("similarity_score") is not None else 0.0) for s in sources]
                if sims:
                    top1_similarities.append(sims[0])
                    top3_similarities.append(sum(sims[:3]) / min(3, len(sims)))
                    
                    if sims[0] < 0.6:  # Threshold for low similarity
                        low_similarity_count += 1
                
                # Update document stats
                for s in sources:
                    did = s.get("document_id")
                    if not did:
                        continue
                    stats = doc_stats[did]
                    stats["filename"] = s.get("filename", "Unknown")
                    stats["count"] += 1
                    sim = s.get("similarity_score")
                    stats["sim_sum"] += sim if sim is not None else 0.0
                    rank = s.get("retrieval_rank")
                    stats["rank_sum"] += rank if rank is not None else 1
                    
                    if disposition == "auto_resolved" or status == TicketStatus.CLOSED:
                        stats["auto_res_count"] += 1
                    elif disposition == "escalated" or status == TicketStatus.ESCALATED:
                        stats["esc_count"] += 1
                        
                    ticket_date = t.created_at
                    if not stats["last_retrieved"] or ticket_date > stats["last_retrieved"]:
                        stats["last_retrieved"] = ticket_date

        total_tickets = len(tickets)
        
        # Calculate aggregates
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
        latencies.sort()
        median_latency = latencies[len(latencies)//2] if latencies else 0.0
        p95_latency = latencies[int(len(latencies)*0.95)] if latencies else 0.0
        
        avg_top1 = sum(top1_similarities) / len(top1_similarities) if top1_similarities else 0.0
        avg_top3 = sum(top3_similarities) / len(top3_similarities) if top3_similarities else 0.0
        avg_chunks = sum(chunk_counts) / len(chunk_counts) if chunk_counts else 0.0
        
        # Calculate avg_confidence_score based on Top-1 CE scores
        # CE score is found in citations (sources_used) or retrieval_confidence_score
        conf_scores = []
        for t in tickets:
            dbg = t.metadata_.get("retrieval_debug")
            if dbg and dbg.get("retrieval_confidence_score") is not None:
                conf_scores.append(dbg["retrieval_confidence_score"])
        avg_conf = sum(conf_scores) / len(conf_scores) if conf_scores else 0.0
        
        auto_rate = auto_resolved_count / total_tickets if total_tickets else 0.0
        esc_rate = escalated_count / total_tickets if total_tickets else 0.0
        
        avg_hallucination = sum(hallucination_scores) / len(hallucination_scores) if hallucination_scores else 0.0
        avg_processing = sum(processing_times) / len(processing_times) if processing_times else 0.0
        
        # Health Score Formula: (Avg Sim * 0.4) + (Auto Res * 0.4) + ((1 - Hallucination) * 0.2) mapped to 0-100
        health_score = (avg_top1 * 0.4) + (auto_rate * 0.4) + ((1.0 - avg_hallucination) * 0.2)
        health_score = round(health_score * 100, 2)
        
        # Compile document analytics
        active_docs = []
        now = datetime.now(timezone.utc)
        for did, stats in doc_stats.items():
            days_since = (now - stats["last_retrieved"]).days if stats["last_retrieved"] else None
            active_docs.append(DocumentAnalytics(
                document_id=did,
                filename=stats["filename"],
                retrieval_count=stats["count"],
                avg_similarity=stats["sim_sum"] / stats["count"],
                avg_rank=stats["rank_sum"] / stats["count"],
                auto_resolution_contribution=stats["auto_res_count"],
                escalation_contribution=stats["esc_count"],
                last_retrieved_at=stats["last_retrieved"].isoformat() if stats["last_retrieved"] else None,
                days_since_last_retrieval=days_since
            ))
            
        # Fetch all knowledge articles to find "never retrieved"
        kb_stmt = select(KnowledgeArticle).where(KnowledgeArticle.tenant_id == tenant_id)
        kb_result = await self.session.execute(kb_stmt)
        all_articles = kb_result.scalars().all()
        
        retrieved_ids = set(doc_stats.keys())
        never_retrieved = []
        for a in all_articles:
            if str(a.id) not in retrieved_ids:
                never_retrieved.append(DocumentAnalytics(
                    document_id=str(a.id),
                    filename=a.title,
                    retrieval_count=0,
                    avg_similarity=0.0,
                    avg_rank=0.0,
                    auto_resolution_contribution=0,
                    escalation_contribution=0,
                    last_retrieved_at=None,
                    days_since_last_retrieval=None
                ))

        # Sort documents
        active_docs.sort(key=lambda x: x.retrieval_count, reverse=True)
        most_retrieved = active_docs[:10]
        least_retrieved = active_docs[-10:] if active_docs else []
        # Re-sort least retrieved ascending
        least_retrieved.sort(key=lambda x: x.retrieval_count)

        response = RetrievalEvaluationResponse(
            retrieval_health_score=health_score,
            retrieval_metrics=RetrievalMetrics(
                avg_latency_ms=avg_latency,
                median_latency_ms=median_latency,
                p95_latency_ms=p95_latency,
                avg_top1_similarity=avg_top1,
                avg_top3_similarity=avg_top3,
                avg_retrieved_chunks=avg_chunks,
                avg_confidence_score=avg_conf
            ),
            resolution_metrics=ResolutionMetrics(
                auto_resolution_rate=auto_rate,
                escalation_rate=esc_rate,
                avg_hallucination_score=avg_hallucination,
                avg_processing_time_ms=avg_processing
            ),
            most_retrieved_documents=most_retrieved,
            least_retrieved_documents=least_retrieved,
            never_retrieved_documents=never_retrieved,
            failure_analytics=FailureAnalytics(
                no_source_count=no_source_count,
                no_source_percent=no_source_count / total_tickets if total_tickets else 0.0,
                low_similarity_count=low_similarity_count,
                low_similarity_percent=low_similarity_count / total_tickets if total_tickets else 0.0,
                hallucination_escalation_count=hallucination_escalation_count,
                hallucination_escalation_percent=hallucination_escalation_count / total_tickets if total_tickets else 0.0,
                human_review_escalation_count=human_review_escalation_count,
                human_review_escalation_percent=human_review_escalation_count / total_tickets if total_tickets else 0.0,
                confidence_escalation_count=confidence_escalation_count,
                confidence_escalation_percent=confidence_escalation_count / total_tickets if total_tickets else 0.0
            )
        )
        
        # Save snapshot
        await self._save_snapshot(tenant_id, response)
        
        return response

    async def _save_snapshot(self, tenant_id: uuid.UUID, data: RetrievalEvaluationResponse) -> None:
        """Persist or update the snapshot for today."""
        today = date.today()
        
        stmt = select(RetrievalEvaluationSnapshot).where(
            RetrievalEvaluationSnapshot.tenant_id == tenant_id,
            RetrievalEvaluationSnapshot.snapshot_date == today
        )
        result = await self.session.execute(stmt)
        snapshot = result.scalars().first()
        
        if not snapshot:
            snapshot = RetrievalEvaluationSnapshot(
                tenant_id=tenant_id,
                snapshot_date=today
            )
            self.session.add(snapshot)
            
        snapshot.avg_similarity = data.retrieval_metrics.avg_top1_similarity
        snapshot.avg_top1_similarity = data.retrieval_metrics.avg_top1_similarity
        snapshot.avg_top3_similarity = data.retrieval_metrics.avg_top3_similarity
        snapshot.avg_latency = data.retrieval_metrics.avg_latency_ms
        snapshot.auto_resolution_rate = data.resolution_metrics.auto_resolution_rate
        snapshot.escalation_rate = data.resolution_metrics.escalation_rate
        snapshot.hallucination_score = data.resolution_metrics.avg_hallucination_score
        snapshot.retrieval_health_score = data.retrieval_health_score
        
        await self.session.commit()

    async def get_trends(self, tenant_id: uuid.UUID) -> RetrievalTrendsResponse:
        """Fetch historical snapshots and return time-series data."""
        stmt = select(RetrievalEvaluationSnapshot).where(
            RetrievalEvaluationSnapshot.tenant_id == tenant_id
        ).order_by(RetrievalEvaluationSnapshot.snapshot_date.asc())
        
        result = await self.session.execute(stmt)
        snapshots = result.scalars().all()
        
        trends = []
        for s in snapshots:
            trends.append(TrendPoint(
                date=s.snapshot_date.isoformat(),
                retrieval_health_score=s.retrieval_health_score,
                avg_latency_ms=s.avg_latency,
                avg_similarity=s.avg_top1_similarity,
                hallucination_score=s.hallucination_score,
                auto_resolution_rate=s.auto_resolution_rate,
                escalation_rate=s.escalation_rate
            ))
            
        return RetrievalTrendsResponse(trends=trends)

    def _empty_response(self) -> RetrievalEvaluationResponse:
        return RetrievalEvaluationResponse(
            retrieval_health_score=0.0,
            retrieval_metrics=RetrievalMetrics(
                avg_latency_ms=0, median_latency_ms=0, p95_latency_ms=0,
                avg_top1_similarity=0, avg_top3_similarity=0, avg_retrieved_chunks=0,
                avg_confidence_score=0
            ),
            resolution_metrics=ResolutionMetrics(
                auto_resolution_rate=0, escalation_rate=0,
                avg_hallucination_score=0, avg_processing_time_ms=0
            ),
            most_retrieved_documents=[],
            least_retrieved_documents=[],
            never_retrieved_documents=[],
            failure_analytics=FailureAnalytics(
                no_source_count=0, no_source_percent=0,
                low_similarity_count=0, low_similarity_percent=0,
                hallucination_escalation_count=0, hallucination_escalation_percent=0,
                human_review_escalation_count=0, human_review_escalation_percent=0,
                confidence_escalation_count=0, confidence_escalation_percent=0
            )
        )
