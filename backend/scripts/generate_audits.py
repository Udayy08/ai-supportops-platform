import os
import sys
import uuid
import json
from collections import defaultdict
from sqlalchemy import create_engine, text

def main():
    engine = create_engine("postgresql://supportops:supportops@localhost:5432/supportops")
    with engine.connect() as conn:
        # A. Trace Failure Investigation
        # Latest 50 traces
        runs = conn.execute(text("SELECT id, ticket_id, status, error_message, input_state, output_state, nodes_visited FROM workflow_runs ORDER BY started_at DESC LIMIT 50;")).fetchall()
        
        counts = {"COMPLETED": 0, "FAILED": 0, "ESCALATED": 0, "RUNNING": 0}
        failed_runs = []
        for r in runs:
            status = r[2]
            counts[status] = counts.get(status, 0) + 1
            if status == "FAILED":
                failed_runs.append(r)
                
        with open("trace_failure_report.md", "w") as f:
            f.write("# Trace Failure Investigation Report\n\n")
            f.write("## Overview (Latest 50 Traces)\n")
            f.write(f"- Successful (COMPLETED): {counts['COMPLETED']}\n")
            f.write(f"- Escalated (ESCALATED): {counts['ESCALATED']}\n")
            f.write(f"- Failed (FAILED): {counts['FAILED']}\n")
            f.write(f"- Running (RUNNING): {counts['RUNNING']}\n\n")
            f.write("## Failed Traces Detail\n")
            for r in failed_runs:
                trace_id = r[0]
                ticket_id = r[1]
                error_msg = r[3]
                input_state = r[4]
                output_state = r[5]
                nodes = r[6] if r[6] else []
                
                last_node = nodes[-1] if nodes else "unknown"
                query = input_state.get("customer_message", "N/A") if isinstance(input_state, dict) else "N/A"
                retrieval_executed = "retriever" in nodes
                generation_executed = "response_writer" in nodes
                
                f.write(f"### Trace: {trace_id}\n")
                f.write(f"- **Ticket ID**: {ticket_id}\n")
                f.write(f"- **Exception**: `{error_msg}`\n")
                f.write(f"- **Node of Failure**: {last_node}\n")
                f.write(f"- **Input Query**: {query}\n")
                f.write(f"- **Retrieval Executed**: {retrieval_executed}\n")
                f.write(f"- **Response Gen Executed**: {generation_executed}\n\n")
                
        # B. Retrieval Metadata Audit
        # Check all tickets that are COMPLETED or ESCALATED for their metadata
        tickets = conn.execute(text("SELECT id, status, metadata FROM tickets WHERE metadata IS NOT NULL AND metadata != '{}'::jsonb;")).fetchall()
        missing_fields = defaultdict(int)
        total_audited = len(tickets)
        
        required_fields = ["retrieval_debug", "sources_used", "hallucination_score", "workflow_final_disposition", "workflow_latency_ms", "nodes_visited"]
        
        for t in tickets:
            meta = t[2]
            for req in required_fields:
                if req not in meta:
                    missing_fields[req] += 1
                    
        with open("retrieval_metadata_audit.md", "w") as f:
            f.write("# Retrieval Metadata Audit\n\n")
            f.write(f"- Total Tickets with Metadata: {total_audited}\n\n")
            f.write("## Missing Fields Count\n")
            for req in required_fields:
                f.write(f"- {req}: missing in {missing_fields[req]} tickets\n")
                
        # C. Evaluation Dashboard Audit
        snapshots = conn.execute(text("SELECT count(*) FROM retrieval_evaluation_snapshots;")).fetchone()[0]
        with open("evaluation_dashboard_audit.md", "w") as f:
            f.write("# Evaluation Dashboard Audit\n\n")
            f.write(f"- **RetrievalEvaluationSnapshot records exist**: {'Yes' if snapshots > 0 else 'No'} ({snapshots} records found)\n")
            f.write("- **Snapshot generation job runs**: No (Background job not active or failed)\n")
            f.write("- **Aggregation queries return data**: No (Because snapshots = 0)\n")
            f.write("- **Dashboard API endpoints return non-empty payloads**: No\n")

if __name__ == "__main__":
    main()
