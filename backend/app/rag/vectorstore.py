import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings

from app.config import settings
from app.rag.embeddings import get_embeddings


def get_chroma_client() -> chromadb.HttpClient:
    """Initialize and return a persistent ChromaDB HTTP client."""
    return chromadb.HttpClient(
        host=settings.chroma_host,
        port=settings.chroma_port,
        settings=ChromaSettings(
            allow_reset=True,
            anonymized_telemetry=False,
        )
    )


def get_vectorstore(
    collection_name: str | None = None,
    embedding_function: Embeddings | None = None
) -> Chroma:
    """
    Get a LangChain Chroma vector store instance connected to our ChromaDB HTTP server.
    """
    col_name = collection_name or settings.chroma_collection_name
    embed_func = embedding_function or get_embeddings()
    client = get_chroma_client()
    
    return Chroma(
        client=client,
        collection_name=col_name,
        embedding_function=embed_func,
    )
