"""
End-to-end test script for the Phase 5 LangGraph multi-agent workflow.

Usage:
    cd backend
    source .venv/bin/activate
    python scripts/test_workflow.py
"""

import json
import os
import sys

# Add the backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.workflow_service import WorkflowService


def run_test():
    # Read tenant_id from seed_kb.py output
    tenant_id = os.environ.get("TENANT_ID")
    if not tenant_id:
        try:
            with open("demo_tenant_id.txt", "r") as f:
                tenant_id = f.read().strip()
        except FileNotFoundError:
            print("Please run seed_kb.py first or set TENANT_ID env var.")
            sys.exit(1)

    print(f"Tenant ID: {tenant_id}")
    print("=" * 70)

    test_cases = [
        {
            "name": "Refund Request",
            "message": "I received a damaged product and I want a full refund. I ordered it 2 weeks ago.",
            "customer_name": "Alice",
        },
        {
            "name": "Subscription Question",
            "message": "My payment failed and I'm worried I'll lose access to my premium features. What happens next?",
            "customer_name": "Bob",
        },
        {
            "name": "Shipping Inquiry",
            "message": "I placed an order 3 days ago and haven't received a tracking number yet. When will my package arrive?",
            "customer_name": "Carol",
        },
    ]

    service = WorkflowService()

    for tc in test_cases:
        print(f"\n{'=' * 70}")
        print(f"TEST: {tc['name']}")
        print(f"MESSAGE: {tc['message']}")
        print(f"{'=' * 70}")

        result = service.run_sync(
            tenant_id=tenant_id,
            customer_message=tc["message"],
            customer_name=tc["customer_name"],
        )

        # Print structured results
        print(f"\n[Classification]")
        print(f"  Category: {result.get('category')}")
        print(f"  Subcategory: {result.get('subcategory')}")
        print(f"  Priority: {result.get('priority')}")
        print(f"  Classification Confidence: {result.get('classification_confidence')}")

        print(f"\n[RAG Retrieval]")
        print(f"  Sources Found: {result.get('num_sources_found')}")
        print(f"  Retrieval Confidence: {result.get('retrieval_confidence')}")
        citations = result.get("citations", [])
        for c in citations:
            print(f"    - {c.get('title')} ({c.get('category')}) | Score: {c.get('confidence_score')}")

        print(f"\n[Sentiment & Risk]")
        print(f"  Sentiment: {result.get('sentiment')}")
        print(f"  Risk Level: {result.get('risk_level')}")
        print(f"  Urgency Modifier: {result.get('urgency_modifier')}")

        print(f"\n[Resolution Plan]")
        print(f"  Plan: {result.get('resolution_plan')}")
        steps = result.get("resolution_steps", [])
        for i, s in enumerate(steps, 1):
            print(f"    {i}. {s}")
        print(f"  Requires Action: {result.get('requires_action')}")

        print(f"\n[Proposed Response]")
        print(f"  Tone: {result.get('response_tone')}")
        print(f"  Response:\n    {result.get('proposed_response', '')[:500]}")

        print(f"\n[Quality Check]")
        print(f"  Hallucination Score: {result.get('hallucination_score')}")
        print(f"  Overall Confidence: {result.get('overall_confidence')}")
        print(f"  Below Threshold: {result.get('is_below_threshold')}")
        issues = result.get("grounding_issues", [])
        if issues:
            print(f"  Grounding Issues:")
            for issue in issues:
                print(f"    - {issue}")

        print(f"\n[Final Disposition]")
        print(f"  Disposition: {result.get('final_disposition')}")
        if result.get("final_disposition") == "escalated":
            print(f"  Escalation Reason: {result.get('escalation_reason')}")
            print(f"  Approval Request ID: {result.get('approval_request_id')}")

        print(f"\n[Workflow Metadata]")
        print(f"  Nodes Visited: {' → '.join(result.get('nodes_visited', []))}")
        print(f"  Total Latency: {result.get('total_latency_ms')}ms")
        print(f"  Queued for Offline Eval: {result.get('queued_for_evaluation', False)}")
        
        if result.get("langsmith_run_id"):
            print(f"  LangSmith Run ID: {result.get('langsmith_run_id')}")
            print(f"  LangSmith Run URL: {result.get('langsmith_run_url') or 'Not available (check credentials)'}")
            
        metrics = result.get("metrics")
        if metrics:
            print(f"  Token Usage: {metrics.get('total_tokens')} (Prompt: {metrics.get('prompt_tokens')}, Completion: {metrics.get('completion_tokens')})")

        if result.get("error"):
            print(f"\n  ⚠️  ERROR: {result['error']}")


if __name__ == "__main__":
    run_test()
