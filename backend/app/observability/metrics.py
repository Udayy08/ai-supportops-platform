"""Workflow metrics tracking."""

from langsmith import Client

client = Client()

def get_run_metrics(run_id: str) -> dict:
    """Extract token usage and latency from a LangSmith run."""
    try:
        run = client.read_run(run_id)
        tokens = run.prompt_tokens + run.completion_tokens if run.prompt_tokens else 0
        latency = (run.end_time - run.start_time).total_seconds() * 1000 if run.end_time and run.start_time else 0
        
        return {
            "total_tokens": tokens,
            "prompt_tokens": run.prompt_tokens or 0,
            "completion_tokens": run.completion_tokens or 0,
            "total_latency_ms": int(latency)
        }
    except Exception:
        return {
            "total_tokens": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_latency_ms": 0
        }
