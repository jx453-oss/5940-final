"""
RAG Service Module
Provides Retrieval-Augmented Generation functionality based on school knowledge base
"""
import os
from config import Config
from llama_index.core import StorageContext, load_index_from_storage, Settings
from llama_index.embeddings.dashscope import (
    DashScopeEmbedding,
    DashScopeTextEmbeddingModels,
    DashScopeTextEmbeddingType,
)
from llama_index.postprocessor.dashscope_rerank import DashScopeRerank

# Configure embedding model
EMBED_MODEL = DashScopeEmbedding(
    model_name=DashScopeTextEmbeddingModels.TEXT_EMBEDDING_V2,
    text_type=DashScopeTextEmbeddingType.TEXT_TYPE_DOCUMENT,
)
Settings.embed_model = EMBED_MODEL

# Index cache to avoid repeated loading
_index_cache = {}


def load_index(school_id: str):
    """
    Load school vector index (with caching)

    Args:
        school_id: School ID, e.g., 'UCI', 'UCSD', etc.

    Returns:
        VectorStoreIndex or None (if knowledge base doesn't exist)
    """
    if school_id in _index_cache:
        return _index_cache[school_id]

    index_path = os.path.join(Config.VECTOR_STORE_PATH, school_id)

    if not os.path.exists(index_path):
        print(f"Knowledge base does not exist: {index_path}")
        return None

    try:
        storage_context = StorageContext.from_defaults(persist_dir=index_path)
        index = load_index_from_storage(storage_context)
        _index_cache[school_id] = index
        print(f"Knowledge base loaded: {school_id}")
        return index
    except Exception as e:
        print(f"Failed to load knowledge base [{school_id}]: {e}")
        return None


def retrieve(school_id: str, query: str, chunk_count: int = None, similarity_threshold: float = None) -> tuple:
    """
    Retrieve relevant content from school knowledge base

    Args:
        school_id: School ID
        query: User question
        chunk_count: Number of chunks to retrieve (defaults to config value)
        similarity_threshold: Similarity threshold (defaults to config value)

    Returns:
        tuple: (retrieved text content, highest relevance score, whether has high quality results)
    """
    chunk_count = chunk_count or Config.RAG_CHUNK_COUNT
    similarity_threshold = similarity_threshold or Config.RAG_SIMILARITY_THRESHOLD
    # High quality threshold (used to determine if web search is needed)
    high_quality_threshold = getattr(Config, 'RAG_HIGH_QUALITY_THRESHOLD', 0.5)

    index = load_index(school_id)
    if index is None:
        return "", 0.0, False

    try:
        # Create retriever, get more results for reranking
        retriever = index.as_retriever(similarity_top_k=20)
        nodes = retriever.retrieve(query)

        if not nodes:
            return "", 0.0, False

        # Use DashScope Rerank for reranking
        try:
            reranker = DashScopeRerank(top_n=chunk_count, return_documents=True)
            reranked_nodes = reranker.postprocess_nodes(nodes, query_str=query)
        except Exception as e:
            print(f"Rerank failed, using original results: {e}")
            reranked_nodes = nodes[:chunk_count]

        # Get the highest score
        max_score = max([node.score for node in reranked_nodes]) if reranked_nodes else 0.0

        # Filter by similarity threshold and assemble text
        chunk_texts = []
        for i, node in enumerate(reranked_nodes):
            if node.score >= similarity_threshold:
                chunk_texts.append(f"[Reference {i+1}]\n{node.text}")

        retrieved_content = "\n\n".join(chunk_texts)
        has_high_quality = max_score >= high_quality_threshold and len(chunk_texts) > 0

        return retrieved_content, max_score, has_high_quality

    except Exception as e:
        print(f"Retrieval failed [{school_id}]: {e}")
        return "", 0.0, False


def retrieve_simple(school_id: str, query: str) -> str:
    """
    Simplified retrieval function, returns only text content (backward compatible)
    """
    content, _, _ = retrieve(school_id, query)
    return content


def get_system_prompt(school_id: str, retrieved_content: str, use_web_search: bool = False) -> str:
    """
    Generate school-specific system prompt

    Args:
        school_id: School ID
        retrieved_content: Content retrieved by RAG
        use_web_search: Whether to use web search mode

    Returns:
        Complete system prompt
    """
    school_info = Config.SCHOOLS.get(school_id, {})
    school_name = school_info.get('name', school_id)

    if retrieved_content:
        # RAG mode: content retrieved from knowledge base
        prompt = f"""You are an AI assistant dedicated to {school_name}.

Please answer the student's question based on the following reference materials:

{retrieved_content}

Response requirements:
1. Prioritize using information from the reference materials to answer questions
2. If the reference materials don't contain relevant information, honestly inform the user and try to provide general advice
3. Responses should be accurate, friendly, and helpful
4. Always respond in English
5. When searching the web, prefer English language sources and results"""
    elif use_web_search:
        # Web search mode: no high-quality RAG results, web search enabled
        prompt = f"""You are an AI assistant dedicated to {school_name}.

The current question did not find highly relevant information in the knowledge base. The system has enabled web search to obtain the latest information.

Response requirements:
1. Answer questions based on web search results, ensuring accuracy and timeliness
2. If search results are not highly relevant to the question, clearly inform the user
3. Responses should be accurate, friendly, and helpful
4. Always respond in English
5. When citing web information, include source references at the end of your response
6. Prefer English language web sources and results"""
    else:
        # No content mode
        prompt = f"""You are an AI assistant dedicated to {school_name}.

No relevant reference materials were retrieved. Please answer the student's question based on your knowledge.
If the question involves specific school policies or information, suggest that students consult official school channels.

Response requirements:
1. Responses should be accurate, friendly, and helpful
2. Always respond in English"""

    return prompt


def is_school_valid(school_id: str) -> bool:
    """Check if school ID is valid"""
    return school_id in Config.SCHOOLS


def get_available_schools() -> list:
    """Get list of all available schools"""
    return list(Config.SCHOOLS.keys())
