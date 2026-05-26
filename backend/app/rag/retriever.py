import os
from typing import List, Dict, Any, Tuple, Optional
from langchain_core.documents import Document
from app.rag.vector_store import get_vector_store
from app.utils.logger import logger

def retrieve_relevant_docs(
    query: str, 
    k: int = 5, 
    score_threshold: float = 0.2,
    state: Optional[str] = None
) -> Tuple[List[Document], List[str]]:
    """
    Retrieve relevant documents from ChromaDB, filter out low-scoring matches,
    and filter by state if specified.
    
    Returns:
        Tuple[List[Document], List[str]]: A tuple containing the list of filtered 
        LangChain Documents and a list of formatted source citation strings.
    """
    logger.info(f"Retrieving top {k} chunks (with state={state}) for query: '{query}'")
    try:
        vectordb = get_vector_store()
        
        # If state is specified, retrieve more candidates so that we still have enough after filtering
        query_k = k * 3 if state else k
        
        # similarity_search_with_relevance_scores returns a list of Tuple[Document, float]
        results = vectordb.similarity_search_with_relevance_scores(query, k=query_k)
        
        # Filter results by state if applicable
        if state:
            state_clean = state.lower().replace(" ", "").replace("_", "")
            keyword = None
            if "maharashtra" in state_clean or "pune" in state_clean or "mumbai" in state_clean or "mh" in state_clean:
                keyword = "mh"
            elif "tamil" in state_clean or "chennai" in state_clean or "tn" in state_clean:
                keyword = "tamilnadu"
                
            if keyword:
                filtered_results = []
                for doc, score in results:
                    src_path = doc.metadata.get("source", "").lower().replace("_", "").replace("-", "")
                    if keyword in src_path:
                        filtered_results.append((doc, score))
                
                # Only apply the filter if we found matches for the filtered state
                if filtered_results:
                    logger.info(f"Filtered results by state '{state}' (keyword: '{keyword}'). Found {len(filtered_results)} matches.")
                    results = filtered_results[:k]
                else:
                    logger.info(f"No matches found for state '{state}' (keyword: '{keyword}'). Falling back to unfiltered search.")
                    results = results[:k]
            else:
                results = results[:k]
        else:
            results = results[:k]
            
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
