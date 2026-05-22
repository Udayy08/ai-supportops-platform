"""LangSmith tracer utilities."""

import contextlib
from typing import Generator

from langchain_core.tracers.context import tracing_v2_enabled
from langsmith import Client

from app.config import settings

client = Client()

@contextlib.contextmanager
def get_tracer_context(project_name: str | None = None) -> Generator:
    """Context manager to enable LangSmith tracing and extract run details."""
    if not settings.langchain_tracing_v2:
        yield None
        return

    with tracing_v2_enabled(project_name=project_name or settings.langchain_project) as cb:
        yield cb

def get_run_url(run_id: str) -> str | None:
    """Fetch the LangSmith URL for a given run ID."""
    if not settings.langchain_tracing_v2:
        return None
    try:
        return client.get_run_url(run_id=run_id)
    except Exception:
        return None
