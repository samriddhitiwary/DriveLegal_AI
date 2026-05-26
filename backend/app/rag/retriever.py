import os
from typing import List, Dict, Any, Tuple
from langchain_core.documents import Document
from app.rag.vector_store import get_vector_store
from app.utils.logger import logger

def retrieve_relevant_docs(
    query: str, 
    k: int = 5, 
    score_threshold: float = 0.2
) -> Tuple[List[Document], List[str]]:
    """
    Retrieve relevant documents from ChromaDB, filter out low-scoring matches,
    and extract formatting citations/sources.
    
    Returns:
        Tuple[List[Document], List[str]]: A tuple containing the list of filtered 
        LangChain Documents and a list of formatted source citation strings.
    """
    logger.info(f"Retrieving top {k} chunks for query: '{query}'")
    try:
        vectordb = get_vector_store()
        
        # similarity_search_with_relevance_scores returns a list of Tuple[Document, float]
        results = vectordb.similarity_search_with_relevance_scores(query, k=k)
        
        filtered_docs = []
        sources = []
        
        for idx, (doc, score) in enumerate(results):
            source_path = doc.metadata.get("source", "Unknown PDF")
            filename = os.path.basename(source_path)
            page = doc.metadata.get("page", None)
            
            page_suffix = f" (page {page + 1})" if page is not None else ""
            source_citation = f"{filename}{page_suffix}"
            
            logger.info(f"Match {idx+1}: {filename} (page {page}) - Score: {score:.4f}")
            
            if score >= score_threshold:
                filtered_docs.append(doc)
                if source_citation not in sources:
                    sources.append(source_citation)
            else:
                logger.info(f"Match {idx+1} below threshold ({score:.4f} < {score_threshold}). Discarded.")
                
        # If all matches were below threshold but we got matches, fallback to the top 1 match
        # to prevent a completely empty context when a match actually exists.
        if not filtered_docs and results:
            top_doc, top_score = results[0]
            logger.warning(
                f"All matches fell below threshold. Falling back to highest match (Score: {top_score:.4f})"
            )
            filtered_docs.append(top_doc)
            source_path = top_doc.metadata.get("source", "Unknown PDF")
            filename = os.path.basename(source_path)
            page = top_doc.metadata.get("page", None)
            page_suffix = f" (page {page + 1})" if page is not None else ""
            sources.append(f"{filename}{page_suffix}")
            
        logger.info(f"Retrieved {len(filtered_docs)} relevant chunks after filtering.")
        return filtered_docs, sources
        
    except Exception as e:
        logger.error(f"Error during context retrieval: {e}", exc_info=True)
        return [], []
