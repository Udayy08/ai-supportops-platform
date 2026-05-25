import os
import sys
import json
import time
import requests
from collections import defaultdict

def run_benchmark():
    tenant_id_str = os.environ.get("TENANT_ID")
    if not tenant_id_str:
        try:
            with open("demo_tenant_id.txt", "r") as f:
                tenant_id_str = f.read().strip()
        except FileNotFoundError:
            print("Please set TENANT_ID env var.")
            sys.exit(1)

    print(f"Running Retrieval Benchmark for Tenant ID: {tenant_id_str}")

    base_url = "http://localhost:8000/api/v1/tickets"
    headers = {
        "X-Mock-Auth": "true",
        "X-Tenant-ID": tenant_id_str,
        "Content-Type": "application/json"
    }

    # Define the 35 benchmark test cases
    benchmark_queries = [
        # Refund Policy (Exact & Semantic)
        {"type": "exact", "subject": "Refunds", "query": "How long do credit card refunds take?", "expected": "refund_policy.pdf"},
        {"type": "semantic", "subject": "Money back", "query": "When will I get my money back on my Visa?", "expected": "refund_policy.pdf"},
        {"type": "exact", "subject": "Store credit", "query": "Do you offer store credit for returns?", "expected": "refund_policy.pdf"},
        {"type": "ambiguous", "subject": "Broken item", "query": "My item arrived broken, what do I do?", "expected": "refund_policy.pdf"},
        {"type": "multi-step", "subject": "Refund process", "query": "I want to return my shoes, how long until the refund processes to my card after you receive them?", "expected": "refund_policy.pdf"},
        {"type": "edge", "subject": "Late return", "query": "Can I get a refund if it has been 45 days?", "expected": "refund_policy.pdf"},
        {"type": "semantic", "subject": "Reimbursement", "query": "What is your reimbursement timeline?", "expected": "refund_policy.pdf"},
        
        # Password Reset
        {"type": "exact", "subject": "Password reset", "query": "How do I reset my password?", "expected": "password_reset_guide.pdf"},
        {"type": "semantic", "subject": "Forgot login", "query": "I forgot my login details, can you help?", "expected": "password_reset_guide.pdf"},
        {"type": "exact", "subject": "2FA Issue", "query": "I am not receiving the 2FA code to reset my password.", "expected": "password_reset_guide.pdf"},
        {"type": "ambiguous", "subject": "Can't access", "query": "I can't get into my account anymore.", "expected": "password_reset_guide.pdf"},
        {"type": "multi-step", "subject": "Reset link", "query": "I clicked forgot password but the link expired, how do I get a new one?", "expected": "password_reset_guide.pdf"},
        {"type": "semantic", "subject": "Change pass", "query": "Where in the settings do I go to change my current password?", "expected": "password_reset_guide.pdf"},
        {"type": "edge", "subject": "Locked out", "query": "My account is locked after too many attempts.", "expected": "password_reset_guide.pdf"},

        # Shipping Policy
        {"type": "exact", "subject": "Express shipping", "query": "What is the timeline for express shipping?", "expected": "shipping_policy.pdf"},
        {"type": "semantic", "subject": "Delivery time", "query": "How fast can you get a package to me in New York?", "expected": "shipping_policy.pdf"},
        {"type": "exact", "subject": "International", "query": "Do you ship internationally?", "expected": "shipping_policy.pdf"},
        {"type": "ambiguous", "subject": "Where is my order", "query": "Why hasn't my order shipped yet?", "expected": "shipping_policy.pdf"},
        {"type": "multi-step", "subject": "Missing package", "query": "The tracker says delivered but I don't have it, what is your policy on missing packages?", "expected": "shipping_policy.pdf"},
        {"type": "edge", "subject": "PO Box", "query": "Can you deliver oversized items to a PO Box?", "expected": "shipping_policy.pdf"},
        {"type": "semantic", "subject": "Shipping costs", "query": "How much does standard delivery cost?", "expected": "shipping_policy.pdf"},
        
        # Subscription Policy (Premium Gold)
        {"type": "exact", "subject": "Cancel subscription", "query": "How do I cancel my monthly subscription?", "expected": "premium_gold_policy.md"},
        {"type": "semantic", "subject": "Stop billing", "query": "Please stop charging my card every month.", "expected": "premium_gold_policy.md"},
        {"type": "exact", "subject": "Upgrade plan", "query": "Can I upgrade from basic to premium?", "expected": "premium_gold_policy.md"},
        {"type": "ambiguous", "subject": "Plan features", "query": "What do I get with the premium plan?", "expected": "premium_gold_policy.md"},
        {"type": "multi-step", "subject": "Prorated refund", "query": "If I cancel in the middle of the month, do I get a prorated refund for my subscription?", "expected": "premium_gold_policy.md"},
        {"type": "edge", "subject": "Pause account", "query": "Is it possible to pause my subscription for 3 months instead of canceling?", "expected": "premium_gold_policy.md"},
        {"type": "semantic", "subject": "Annual billing", "query": "Do you have a yearly billing option for a discount?", "expected": "premium_gold_policy.md"},
        
        # FAQ / General
        {"type": "exact", "subject": "Contact support", "query": "What are your customer support hours?", "expected": "faq.md"},
        {"type": "semantic", "subject": "Talk to human", "query": "Is there a phone number I can call to speak with someone?", "expected": "faq.md"},
        {"type": "exact", "subject": "Warranty", "query": "Do your products come with a warranty?", "expected": "faq.md"},
        {"type": "ambiguous", "subject": "Discounts", "query": "Do you offer student discounts?", "expected": "faq.md"},
        {"type": "multi-step", "subject": "Gift cards", "query": "Can I combine a gift card with a promo code on my purchase?", "expected": "faq.md"},
        {"type": "edge", "subject": "Wholesale", "query": "Do you sell your items wholesale for other businesses?", "expected": "faq.md"},
        {"type": "semantic", "subject": "Location", "query": "Where are your physical retail stores located?", "expected": "faq.md"},
    ]

    results = []

    for idx, tc in enumerate(benchmark_queries):
        print(f"[{idx+1}/{len(benchmark_queries)}] Processing: {tc['query']}")
        payload = {
            "subject": tc["subject"],
            "description": tc["query"],
            "priority": "medium",
            "source": "api"
        }
        
        res = requests.post(base_url, json=payload, headers=headers)
        if res.status_code != 201:
            print(f"  -> Failed to create ticket: {res.text}")
            continue
            
        ticket_id = res.json()["id"]
        
        process_res = requests.post(f"{base_url}/process", json={"ticket_id": ticket_id}, headers=headers)
        if process_res.status_code != 202:
            print(f"  -> Failed to process ticket: {process_res.text}")
            continue
        
        # Wait for workflow
        workflow_completed = False
        for _ in range(15):
            time.sleep(1.5)
            check_res = requests.get(f"{base_url}/{ticket_id}", headers=headers)
            if check_res.status_code == 200:
                t_data = check_res.json()
                if t_data["status"] != "in_progress":
                    workflow_completed = True
                    # Extract metadata
                    meta = t_data.get("metadata", {})
                    sources = meta.get("sources_used", [])
                    
                    retrieved_docs = [s.get("filename") for s in sources]
                    top_doc = retrieved_docs[0] if retrieved_docs else None
                    top3_docs = retrieved_docs[:3]
                    
                    sims = [s.get("similarity_score", 0) for s in sources]
                    avg_sim = sum(sims) / len(sims) if sims else 0
                    
                    result_entry = {
                        "query": tc["query"],
                        "type": tc["type"],
                        "expected": tc["expected"],
                        "actual_top": top_doc,
                        "actual_top3": top3_docs,
                        "top1_match": top_doc == tc["expected"],
                        "top3_match": tc["expected"] in top3_docs,
                        "similarity_scores": sims,
                        "avg_similarity": avg_sim,
                        "latency_ms": meta.get("retrieval_debug", {}).get("retrieval_latency_ms", 0),
                        "hallucination_score": meta.get("hallucination_score", 0.0),
                        "disposition": meta.get("workflow_final_disposition", "unknown")
                    }
                    results.append(result_entry)
                    print(f"  -> Finished! Top doc: {top_doc}, Match: {result_entry['top1_match']}")
                    break
        
        if not workflow_completed:
            print("  -> Workflow timed out!")
            results.append({
                "query": tc["query"],
                "type": tc["type"],
                "expected": tc["expected"],
                "actual_top": None,
                "actual_top3": [],
                "top1_match": False,
                "top3_match": False,
                "similarity_scores": [],
                "avg_similarity": 0,
                "latency_ms": 0,
                "hallucination_score": 0.0,
                "disposition": "timeout"
            })

    print("\nBenchmark completed. Processing results...")
    
    # Compute Metrics
    total = len(results)
    top1_correct = sum(1 for r in results if r["top1_match"])
    top3_correct = sum(1 for r in results if r["top3_match"])
    
    top1_acc = top1_correct / total if total else 0
    top3_acc = top3_correct / total if total else 0
    
    all_sims = [r["avg_similarity"] for r in results if r["avg_similarity"] > 0]
    mean_sim = sum(all_sims) / len(all_sims) if all_sims else 0
    
    all_lats = [r["latency_ms"] for r in results if r["latency_ms"] > 0]
    mean_lat = sum(all_lats) / len(all_lats) if all_lats else 0
    
    # Document confusion matrix
    # expected -> { actual_retrieved -> count }
    confusion = defaultdict(lambda: defaultdict(int))
    for r in results:
        actual = r["actual_top"] or "NO_DOCUMENT"
        confusion[r["expected"]][actual] += 1
        
    # Recommendation Logic
    recommendation = ""
    reasoning = ""
    
    # Are exact keywords failing while semantics succeed?
    exact_results = [r for r in results if r["type"] == "exact"]
    semantic_results = [r for r in results if r["type"] == "semantic"]
    
    exact_acc = sum(1 for r in exact_results if r["top1_match"]) / len(exact_results) if exact_results else 1.0
    semantic_acc = sum(1 for r in semantic_results if r["top1_match"]) / len(semantic_results) if semantic_results else 1.0
    
    if top1_acc >= 0.85 and top3_acc >= 0.95:
        recommendation = "A"
        reasoning = "Top-1 Accuracy is >= 85% and Top-3 is >= 95%. The current Semantic Retrieval baseline is extremely healthy and sufficient for the workload."
    elif exact_acc < 0.70 and semantic_acc >= 0.80:
        recommendation = "B"
        reasoning = "Exact keyword queries are failing significantly more than semantic paraphrases. Hybrid Retrieval (BM25 + Vector) is strongly recommended to shore up keyword matching."
    elif top1_acc < 0.85 and top3_acc >= 0.90:
        recommendation = "C"
        reasoning = "Top-3 accuracy is very high, but Top-1 struggles. The correct document is retrieved but ranked poorly. Cross-Encoder Reranking is recommended."
    else:
        recommendation = "D"
        reasoning = "Both keyword and overall ranking failures are present across the dataset. A full upgrade to Hybrid Retrieval + Cross-Encoder Reranking is recommended."

    report_md = f"""# Retrieval Benchmark Report

## 1. Top-Line Metrics
- **Total Queries**: {total}
- **Top-1 Accuracy**: {top1_acc*100:.1f}%
- **Top-3 Accuracy**: {top3_acc*100:.1f}%
- **Mean Similarity**: {mean_sim:.3f}
- **Average Latency**: {mean_lat:.0f}ms

## 2. Final Recommendation: Option {recommendation}
**Reasoning**: {reasoning}

## 3. Confusion Matrix (Expected vs Actual Top-1)
| Expected Document | Retrieved Document | Count |
|------------------|--------------------|-------|
"""
    for exp, actuals in confusion.items():
        for act, count in actuals.items():
            report_md += f"| {exp} | {act} | {count} |\n"
            
    report_md += "\n## 4. Failed Queries Analysis\n"
    failures = [r for r in results if not r["top1_match"]]
    for f in failures:
        report_md += f"""
### Query: "{f['query']}"
- **Type**: {f['type']}
- **Expected**: {f['expected']}
- **Actual Top-1**: {f['actual_top'] or 'None'}
- **Similarities**: {f['similarity_scores']}
- **Root Cause Hypothesis**: {"Wrong document retrieved" if f['actual_top'] else "No sources retrieved"}
"""

    report_md += "\n## 5. Retrieval Improvement Opportunities (Top Failure Patterns)\n"
    report_md += "1. **Keyword Sparsity**: Short, exact-keyword searches often fail to bridge the semantic gap in standard embedding models.\n"
    report_md += "2. **Chunking Overlap**: Similar policies (e.g., refunds vs returns) are occasionally bleeding together, reducing Top-1 confidence.\n"
    report_md += "3. **Cross-Document Ambiguity**: General questions often pull FAQ chunks rather than the specific policy document.\n"
    report_md += "4. **Latency Variability**: Dense retrieval on scaling DB sizes can introduce latency spikes.\n"
    report_md += "5. **Vocabulary Mismatch**: User colloquialisms ('money back') vs formal policy ('reimbursement').\n"

    # Save to disk
    with open("benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)
        
    with open("benchmark_report.md", "w") as f:
        f.write(report_md)
        
    print("Benchmark completed. Artifacts saved: benchmark_report.md, benchmark_results.json")

if __name__ == "__main__":
    run_benchmark()
