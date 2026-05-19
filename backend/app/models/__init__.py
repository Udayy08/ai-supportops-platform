"""
ORM model registry — import all models here so Alembic can detect them
and SQLAlchemy can resolve relationships across modules.
"""

from app.models.base import Base  # noqa: F401
from app.models.tenant import Tenant  # noqa: F401
from app.models.user import User, UserRole  # noqa: F401
from app.models.ticket import Ticket, TicketStatus, TicketPriority, TicketSource  # noqa: F401
from app.models.conversation import Conversation, ConversationStatus  # noqa: F401
from app.models.message import Message, MessageRole  # noqa: F401
from app.models.knowledge_article import KnowledgeArticle  # noqa: F401
from app.models.agent_config import AgentConfig  # noqa: F401
from app.models.evaluation import Evaluation, EvalType  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401

__all__ = [
    "Base",
    "Tenant",
    "User", "UserRole",
    "Ticket", "TicketStatus", "TicketPriority", "TicketSource",
    "Conversation", "ConversationStatus",
    "Message", "MessageRole",
    "KnowledgeArticle",
    "AgentConfig",
    "Evaluation", "EvalType",
    "AuditLog",
]
