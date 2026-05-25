import os
import sys
import uuid
import time
import requests

def run_tests():
    tenant_id_str = os.environ.get("TENANT_ID")
    if not tenant_id_str:
        try:
            with open("demo_tenant_id.txt", "r") as f:
                tenant_id_str = f.read().strip()
        except FileNotFoundError:
            print("Please set TENANT_ID env var.")
            sys.exit(1)

    print(f"Testing Retrieval for Tenant ID: {tenant_id_str}")

    base_url = "http://localhost:8000/api/v1/tickets"
    headers = {
        "X-Mock-Auth": "true",
        "X-Tenant-ID": tenant_id_str,
        "Content-Type": "application/json"
    }

    test_cases = [
        {
            "name": "Refund Timing",
            "subject": "Refund Timing Question",
            "description": "How long do credit card refunds take?",
        },
        {
            "name": "Password Reset",
            "subject": "Password Reset Question",
            "description": "How do I reset my password?",
        },
        {
            "name": "Shipping Timeline",
            "subject": "Shipping Timeline Question",
            "description": "What is the timeline for express shipping?",
        }
    ]

    for tc in test_cases:
        print(f"\nSubmitting {tc['name']}: {tc['subject']}")
        payload = {
            "subject": tc["subject"],
            "description": tc["description"],
            "priority": "medium",
            "source": "dashboard"
        }
        
        # Create ticket
        res = requests.post(base_url, json=payload, headers=headers)
        if res.status_code != 201:
            print(f"Failed to create ticket: {res.text}")
            continue
            
        ticket_id = res.json()["id"]
        print(f"Created ticket: {ticket_id}")
        
        # Process ticket
        process_res = requests.post(f"{base_url}/process", json={"ticket_id": ticket_id}, headers=headers)
        if process_res.status_code != 202:
            print(f"Failed to process ticket: {process_res.text}")
            continue
        
        # Wait for workflow to finish
        print("Waiting for workflow to complete...")
        for _ in range(15):
            time.sleep(2)
            check_res = requests.get(f"{base_url}/{ticket_id}", headers=headers)
            if check_res.status_code == 200:
                status = check_res.json()["status"]
                if status != "in_progress":
                    print(f"Workflow finished with status: {status}")
                    break
        else:
            print("Workflow timed out.")

if __name__ == "__main__":
    run_tests()
