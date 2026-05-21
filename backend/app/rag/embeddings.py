from functools import lru_cache

from langchain_huggingface import HuggingFaceEmbeddings


class EmbeddingsManager:
    def __init__(self):
        # We use a fast, CPU-friendly model for local development and testing
        self.model_name = "sentence-transformers/all-MiniLM-L6-v2"
        self._embeddings = HuggingFaceEmbeddings(
            model_name=self.model_name,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

    def get_embeddings(self) -> HuggingFaceEmbeddings:
        return self._embeddings


@lru_cache(maxsize=1)
def get_embeddings_manager() -> EmbeddingsManager:
    """Singleton pattern to avoid reloading the model in memory multiple times."""
    return EmbeddingsManager()


# Expose a direct dependency callable
def get_embeddings() -> HuggingFaceEmbeddings:
    return get_embeddings_manager().get_embeddings()
