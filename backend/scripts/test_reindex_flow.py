import os
import sys
import uuid
import time
import requests
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.rag.vectorstore import get_vectorstore

def get_tenant_id():
    tenant_id_str = os.environ.get("TENANT_ID")
    if not tenant_id_str:
        try:
            with open("demo_tenant_id.txt", "r") as f:
                tenant_id_str = f.read().strip()
        except FileNotFoundError:
            print("Please set TENANT_ID env var.")
            sys.exit(1)
    return tenant_id_str

def get_chroma_stats(filename):
    vectorstore = get_vectorstore()
    collection = vectorstore._collection
    data = collection.get(include=["metadatas"])
    count = sum(1 for m in data["metadatas"] if m.get("source_filename") == filename)
    
    unique_article_ids = set(m.get("article_id") for m in data["metadatas"] if m.get("source_filename") == filename)
    return count, len(unique_article_ids), list(unique_article_ids)

def run_flow():
    tenant_id = get_tenant_id()
    print(f"Testing Reindex Flow for Tenant ID: {tenant_id}")

    base_url = "http://localhost:8000/api/v1/knowledge"
    headers = {
        "X-Mock-Auth": "true",
        "X-Tenant-ID": tenant_id,
        "Content-Type": "application/json"
    }

    filename = "refund_policy_demo_2.txt"
    
    print("\n[Step 1] Upload refund_policy_demo.pdf")
    files1 = {
        'file': (filename, 'This is the original refund policy. Refunds take 7 days. ' * 50, 'text/plain')
    }
    
    # Do NOT send Content-Type header when sending files, requests will set it with the boundary
    upload_headers = {"X-Mock-Auth": "true", "X-Tenant-ID": tenant_id}
    res1 = requests.post(f"{base_url}/upload", files=files1, headers=upload_headers)
    if res1.status_code != 201:
        print(f"Failed to create: {res1.text}")
        return
        
    article_id = res1.json()["id"]
    print(f"Created KnowledgeArticle ID: {article_id}")
    
    print("\n[Step 2] Record chunk count")
    time.sleep(2) # Give ChromaDB a moment to persist
    
    chunk_count_1, unique_articles_1, article_ids_1 = get_chroma_stats(filename)
    print(f"ChromaDB Chunks for {filename}: {chunk_count_1}")
    print(f"Unique Article IDs in ChromaDB for {filename}: {unique_articles_1} -> {article_ids_1}")
    
    # Verify in DB
    get_res1 = requests.get(f"{base_url}/{article_id}", headers=headers)
    db_chunks_1 = get_res1.json().get("metadata", {}).get("chunk_count")
    print(f"PostgreSQL Chunk Count: {db_chunks_1}")

    print("\n[Step 3] Modify the document (Upload again with new content)")
    
    print("\n[Step 4] Upload again")
    files2 = {
        'file': (filename, 'This is the modified refund policy. Refunds take 3 days. We added a lot more text to increase chunk count. ' * 150, 'text/plain')
    }
    res2 = requests.post(f"{base_url}/upload", files=files2, headers=upload_headers)
    if res2.status_code != 201:
        print(f"Failed to create: {res2.text}")
        return
        
    article_id_2 = res2.json()["id"]
    print(f"Returned KnowledgeArticle ID: {article_id_2} (Should match {article_id})")
    
    print("\n[Step 5 & 6] Show old vectors removed and new vectors inserted")
    time.sleep(2)
    
    chunk_count_2, unique_articles_2, article_ids_2 = get_chroma_stats(filename)
    print(f"ChromaDB Chunks for {filename}: {chunk_count_2}")
    print(f"Unique Article IDs in ChromaDB for {filename}: {unique_articles_2} -> {article_ids_2}")
    
    get_res2 = requests.get(f"{base_url}/{article_id_2}", headers=headers)
    db_chunks_2 = get_res2.json().get("metadata", {}).get("chunk_count")
    print(f"PostgreSQL Chunk Count: {db_chunks_2}")
    
    print("\n[Step 7 & 8] Verify final state")
    
    print(f"Does returned ID match original? {'YES' if article_id == article_id_2 else 'NO'}")
    print(f"Are there old leftover chunks? {'NO' if chunk_count_2 == db_chunks_2 else 'YES'}")
    print(f"Is there only 1 distinct article ID in ChromaDB? {'YES' if unique_articles_2 == 1 else 'NO'}")
    
    # Query all articles to prove only 1 exists
    list_res = requests.get(f"{base_url}?search={filename}", headers=headers)
    items = list_res.json()["items"]
    print(f"Total KnowledgeArticle records matching filename in DB: {len(items)}")
    
if __name__ == "__main__":
    run_flow()
