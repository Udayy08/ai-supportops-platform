from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_document(
    text: str,
    metadata: dict | None = None,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> List[Document]:
    """
    Split a raw text document into smaller semantic chunks for vector storage.
    Uses RecursiveCharacterTextSplitter for optimal NLP boundaries (paragraphs, sentences, words).
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=False,
    )

    # Langchain expects a list of texts to create documents
    docs = splitter.create_documents([text], metadatas=[metadata] if metadata else None)
    return docs
