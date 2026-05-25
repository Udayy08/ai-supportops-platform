"""
ORM model registry — import ALL models here so that:
  1. Alembic autogenerate can detect all table schemas
  2. SQLAlchemy can resolve cross-model relationships (string forward refs)
  3. A single import of this module brings the full schema into scope

Model dependency order (topological):
  Base → Tenant → User → Ticket
       → Conversation → Message
       → WorkflowRun → WorkflowNodeExecution
       → HallucinationFlag / ConfidenceScore
       → ApprovalRequest
       → Evaluation
       → KnowledgeArticle / AgentConfig
       → AuditLog / TicketAnalyticsSnapshot
"""

# ── Foundation ────────────────────────────────────────────────────────────────
from app.models.base import Base, SoftDeleteMixin, TenantMixin, TimestampMixin, UUIDPrimaryKeyMixin  # noqa: F401

# ── Core domain ───────────────────────────────────────────────────────────────
from app.models.tenant import Tenant  # noqa: F401
from app.models.user import User, UserRole  # noqa: F401
from app.models.ticket import Ticket, TicketPriority, TicketSource, TicketStatus  # noqa: F401
from app.models.conversation import Conversation, ConversationStatus  # noqa: F401
from app.models.message import Message, MessageRole  # noqa: F401

# ── AI workflow ───────────────────────────────────────────────────────────────
from app.models.workflow import (  # noqa: F401
    NodeStatus,
    WorkflowNodeExecution,
    WorkflowRun,
    WorkflowRunStatus,
)

# ── AI quality ────────────────────────────────────────────────────────────────
from app.models.quality import (  # noqa: F401
    ConfidenceScore,
    HallucinationFlag,
    HallucinationSeverity,
)

# ── Human-in-the-loop ─────────────────────────────────────────────────────────
from app.models.approval import ApprovalPriority, ApprovalRequest, ApprovalStatus  # noqa: F401

# ── Evaluation ────────────────────────────────────────────────────────────────
from app.models.evaluation import Evaluation, EvalType  # noqa: F401
from app.models.retrieval_snapshot import RetrievalEvaluationSnapshot  # noqa: F401

# ── Knowledge base ────────────────────────────────────────────────────────────
from app.models.knowledge_article import KnowledgeArticle  # noqa: F401

# ── Agent configuration ───────────────────────────────────────────────────────
from app.models.agent_config import AgentConfig  # noqa: F401

# ── Observability ─────────────────────────────────────────────────────────────
from app.models.audit_log import AuditAction, AuditLog  # noqa: F401
from app.models.analytics import TicketAnalyticsSnapshot  # noqa: F401

__all__ = [
    # Base
    "Base", "UUIDPrimaryKeyMixin", "TimestampMixin", "TenantMixin", "SoftDeleteMixin",
    # Core
    "Tenant",
    "User", "UserRole",
    "Ticket", "TicketStatus", "TicketPriority", "TicketSource",
    "Conversation", "ConversationStatus",
    "Message", "MessageRole",
    # Workflow
    "WorkflowRun", "WorkflowRunStatus",
    "WorkflowNodeExecution", "NodeStatus",
    # Quality
    "HallucinationFlag", "HallucinationSeverity",
    "ConfidenceScore",
    # Approvals
    "ApprovalRequest", "ApprovalStatus", "ApprovalPriority",
    # Evaluation
    "Evaluation", "EvalType", "RetrievalEvaluationSnapshot",
    # Knowledge
    "KnowledgeArticle",
    # Agent config
    "AgentConfig",
    # Observability
    "AuditLog", "AuditAction",
    "TicketAnalyticsSnapshot",
]
