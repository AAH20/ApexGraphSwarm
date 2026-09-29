"""Domain adapters for GraphRAG NP-Hard optimization."""
from .biomedical_genomics_rag import run_biomedical_rag_benchmark
from .financial_fraud_kg import run_financial_fraud_benchmark

__all__ = [
    "run_biomedical_rag_benchmark",
    "run_financial_fraud_benchmark"
]
