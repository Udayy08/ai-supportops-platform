import asyncio
from app.rag.vectorstore import get_vectorstore
import os

tenant_id_str = os.environ.get("TENANT_ID")
if not tenant_id_str:
    with open("demo_tenant_id.txt", "r") as f:
        tenant_id_str = f.read().strip()

vs = get_vectorstore()
res = vs.get(where={"tenant_id": tenant_id_str})
print(res.keys())
if 'documents' in res:
    print(f"Num docs: {len(res['documents'])}")
