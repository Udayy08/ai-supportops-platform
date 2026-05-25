import sys
import os
from collections import Counter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.rag.vectorstore import get_vectorstore

def audit_chromadb():
    vectorstore = get_vectorstore()
    collection = vectorstore._collection
    
    print("=== ChromaDB Audit ===")
    print(f"Collection Name: {collection.name}")
    
    # Get all documents
    data = collection.get(include=["metadatas"])
    
    ids = data["ids"]
    metadatas = data["metadatas"]
    
    total_chunks = len(ids)
    print(f"Total Chunk Count: {total_chunks}")
    
    article_chunks = Counter()
    filename_chunks = Counter()
    chunk_ids = []
    source_document_ids = []
    
    for meta in metadatas:
        article_id = meta.get("article_id")
        filename = meta.get("source_filename")
        chunk_id = meta.get("chunk_id")
        
        if article_id:
            article_chunks[article_id] += 1
            source_document_ids.append(article_id)
        if filename:
            filename_chunks[filename] += 1
        if chunk_id:
            chunk_ids.append(chunk_id)
            
    print("\n--- Chunk Count Per Source Filename ---")
    for filename, count in filename_chunks.items():
        print(f" - {filename}: {count} chunks")
        
    print("\n--- Chunk Count Per Article ID ---")
    for article_id, count in article_chunks.items():
        print(f" - {article_id}: {count} chunks")
        
    # Check for duplicates
    dup_chunk_ids = [k for k, v in Counter(chunk_ids).items() if v > 1]
    
    print("\n--- Duplicates ---")
    print(f"Duplicate Chunk IDs: {len(dup_chunk_ids)}")
    if dup_chunk_ids:
        print(f"  Sample: {dup_chunk_ids[:5]}")
        
if __name__ == "__main__":
    audit_chromadb()
