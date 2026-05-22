"""
End-to-end RAGAS offline evaluation script.

Usage:
    cd backend
    source .venv/bin/activate
    python scripts/run_evaluations.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.evaluation.ragas_evaluator import run_ragas_evaluation

def run_evaluation_test():
    # Example historical conversation data
    questions = [
        "I received a damaged product and I want a full refund. I ordered it 2 weeks ago.",
        "My payment failed and I'm worried I'll lose access to my premium features. What happens next?"
    ]
    
    answers = [
        "I'm sorry to hear your product arrived damaged. Because it was defective, we will issue a full refund including shipping costs. Please contact support to initiate the process.",
        "Don't worry, your premium features will remain active for a 7-day grace period while we retry the payment 3 times. Please ensure your payment method is valid."
    ]
    
    contexts = [
        [
            "We offer a 30-day money-back guarantee for all unused products in their original packaging. To initiate a refund, customers must contact support within 30 days of delivery. Refunds are processed within 5-7 business days to the original payment method. Shipping costs are non-refundable unless the return is due to a defective product."
        ],
        [
            "Monthly and annual subscriptions renew automatically unless cancelled prior to the renewal date. If a payment fails, we will retry the charge 3 times over a 7-day grace period. During the grace period, access to premium features will remain active. If payment is not resolved, the account will be downgraded to the free tier."
        ]
    ]
    
    ground_truths = [
        "Yes, since the product was defective, you will get a full refund including shipping costs. Please contact support.",
        "Your premium features will be active for 7 days while we retry your payment 3 times."
    ]

    print("=" * 70)
    print("Running RAGAS Evaluation via Groq...")
    print("=" * 70)
    
    result = run_ragas_evaluation(
        questions=questions,
        answers=answers,
        contexts=contexts,
        ground_truths=ground_truths
    )
    
    print("\n[Evaluation Results]")
    # convert to pandas then dict
    df = result.to_pandas()
    # Average the scores for printing
    avg_scores = df.mean(numeric_only=True).to_dict()
    for key, value in avg_scores.items():
        print(f"  {key}: {value:.4f}")
        
    print("\nDetailed DataFrame output saved to 'evaluation_results.csv'")
    df.to_csv("evaluation_results.csv", index=False)

if __name__ == "__main__":
    run_evaluation_test()
