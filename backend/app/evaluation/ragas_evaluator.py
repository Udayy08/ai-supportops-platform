"""RAGAS offline evaluation engine for historical tickets."""

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper

from app.agents.llm import get_fast_llm, get_llm
from app.rag.embeddings import EmbeddingsManager

def run_ragas_evaluation(
    questions: list[str],
    answers: list[str],
    contexts: list[list[str]],
    ground_truths: list[str] | None = None
) -> dict:
    """
    Execute a batch RAGAS evaluation over conversational history.
    """
    
    # Construct the HuggingFace dataset format required by RAGAS 0.4.x
    data = {
        "user_input": questions,
        "response": answers,
        "retrieved_contexts": contexts,
    }
    if ground_truths:
        data["reference"] = ground_truths
        
    dataset = Dataset.from_dict(data)
    
    # Initialize LLM and Embeddings using existing app modules
    # Use fast LLM for evaluation to save costs/time, but fallback to groq default if needed
    eval_llm = LangchainLLMWrapper(get_llm(provider="groq"))
    
    # RAGAS requires an embedding model for answer relevancy and context metrics
    embeddings_mgr = EmbeddingsManager()
    eval_embeddings = LangchainEmbeddingsWrapper(embeddings_mgr.get_embeddings())

    # Selected metrics
    metrics = [
        faithfulness,
        answer_relevancy,
        context_precision,
    ]
    if ground_truths:
        metrics.append(context_recall)

    # Run evaluation
    result = evaluate(
        dataset,
        metrics=metrics,
        llm=eval_llm,
        embeddings=eval_embeddings,
        raise_exceptions=False,
    )
    
    return result
