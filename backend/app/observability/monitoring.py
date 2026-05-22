"""Workflow monitoring integration."""

def log_workflow_completion(tenant_id: str, ticket_id: str, disposition: str, latency: int):
    """Log the completion of a workflow to monitoring systems (e.g., Datadog)."""
    import structlog
    logger = structlog.get_logger()
    
    logger.info(
        "workflow.completed",
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        disposition=disposition,
        latency_ms=latency
    )
