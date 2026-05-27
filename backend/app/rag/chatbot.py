import os
from typing import List, Tuple, Optional
from langchain_openai import ChatOpenAI
from app.config.settings import settings
from app.utils.logger import logger
from app.rag.retriever import retrieve_relevant_docs
from app.rag.memory import memory_store
from app.schemas.challan_schema import ChallanResponse

_llm = None

def get_llm():
    """
    Lazy singleton initialization of the OpenAI Chat model.
    """
    global _llm
    if _llm is None:
        if not settings.openai_api_key:
            logger.error("OPENAI_API_KEY is not configured in the settings.")
            raise ValueError("OPENAI_API_KEY is missing.")
            
        logger.info(f"Initializing ChatOpenAI with model: {settings.openai_model}")
        try:
            _llm = ChatOpenAI(
                model=settings.openai_model,
                api_key=settings.openai_api_key,
                temperature=0.2,
                timeout=30.0,
                max_retries=3
            )
            logger.info("ChatOpenAI initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI LLM: {e}")
            raise e
    return _llm

def extract_text_from_content(content) -> str:
    """
    Safely extract a plain string from LLM response content, which can be
    a string, a list of strings, or a list of dictionaries.
    """
    if isinstance(content, list):
        texts = []
        for part in content:
            if isinstance(part, dict):
                # Standard content block dictionary from Google GenAI
                if part.get("type") == "text":
                    texts.append(part.get("text", ""))
            elif isinstance(part, str):
                texts.append(part)
        return "".join(texts).strip()
    return str(content).strip()

CONDENSE_QUESTION_PROMPT = """Given the following conversation history and a follow-up question, rephrase the follow-up question to be a standalone search query. Keep it focused on traffic rules, laws, and regulations. Do not explain or add commentary, just output the rephrased standalone query.

Chat History:
{chat_history}

Follow-up Question: {question}

Standalone query:"""

SYSTEM_PROMPT = """You are DriveLegal AI, a professional traffic law assistant. Your goal is to answer the user's question accurately and concisely, based ONLY on the provided retrieved context.

Guidelines:
1. Base your answer STRICTLY on the retrieved context below. Do NOT assume, extrapolate, or use outside knowledge.
2. If the context does not contain the direct answer to the user's question, you must state ONLY: "I'm sorry, but I couldn't find information about that in the traffic rules documentation." Do NOT attempt to provide information about related topics or list other penalties/sections.
3. Keep your answers concise, structured (using bullet points if appropriate), and easy for a layman to understand, while maintaining legal accuracy.
4. Do NOT cite any source PDF names, page numbers, or references. Never mention source file paths, names, or metadata. Provide a clean, direct answer to the user's question without any citation markers.
5. Do NOT hallucinate fine amounts or rules.

Retrieved Context:
{context}

Chat History:
{chat_history}

User Question: {question}

Helpful Answer:"""

async def ask_chatbot(query: str, conversation_id: str, state: Optional[str] = None) -> Tuple[str, List[str], Optional[ChallanResponse]]:
    """
    Processes the user query within a conversational context, retrieves relevant PDFs chunks,
    queries the Gemini LLM, updates chat memory, and returns the answer with source citations.
    """
    logger.info(f"Received query: '{query}' for conversation_id: '{conversation_id}'")
    
    # 1. API Key validation fallback
    if not settings.openai_api_key or settings.openai_api_key.strip() == "":
        logger.error("Missing OpenAI API Key.")
        return (
            "I apologize, but the AI service is currently unavailable because no OPENAI_API_KEY is configured in the backend environment. "
            "Please check the .env configuration file.",
            [],
            None
        )
        
    try:
        # 2. Get history and rephrase if follow-up
        history_string = memory_store.get_history_string(conversation_id)
        search_query = query
        
        if history_string:
            logger.info("Found existing chat history. Generating standalone query...")
            condense_prompt = CONDENSE_QUESTION_PROMPT.format(
                chat_history=history_string,
                question=query
            )
            try:
                llm = get_llm()
                response = llm.invoke(condense_prompt)
                search_query = extract_text_from_content(response.content)
                logger.info(f"Rephrased query: '{search_query}'")
            except Exception as rephrase_err:
                logger.warning(f"Failed to rephrase follow-up query: {rephrase_err}. Using original query.")
                search_query = query
                
        # 3. Retrieve relevant documents using search query and location state
        docs, sources = retrieve_relevant_docs(search_query, state=state)
        context = "\n\n".join([doc.page_content for doc in docs])
        
        # 4. Structured Challan Calculation check
        from app.database.connection import SessionLocal
        from app.services.challan_service import calculate_challan_from_text
        
        db = SessionLocal()
        challan_result = None
        challan_context = ""
        try:
            # Parse the user query and run database-backed challan aggregation
            challan_result = await calculate_challan_from_text(db, query, session_state=state)
            if challan_result and challan_result.violations:
                challan_context = (
                    f"Structured Challan Fine Calculations (State: {challan_result.state}, Vehicle: {challan_result.vehicle_type}):\n"
                    f"- Total Fine: ₹{challan_result.total_fine}\n"
                    f"- Severity: {challan_result.severity_level}\n"
                    f"- Violations and Fines:\n"
                )
                for v in challan_result.violations:
                    challan_context += f"  * {v.name}: Fine ₹{v.fine} (Under Section/Law: {v.law_section}). Description: {v.description}\n"
                challan_context += f"- Legal Warnings & Notes: {challan_result.legal_note}\n\n"
                logger.info(f"Injected calculated challan details into prompt context.")
        except Exception as challan_err:
            logger.warning(f"Failed to calculate challan in chatbot workflow: {challan_err}")
        finally:
            db.close()

        # Combine the DB-driven challan details with any RAG PDF context
        combined_context = context
        if challan_context:
            combined_context = f"{challan_context}\n\nAdditional Traffic Code reference docs:\n{context}"
        
        # 5. Formulate final RAG prompt and call OpenAI
        final_prompt = SYSTEM_PROMPT.format(
            context=combined_context if combined_context else "No context retrieved.",
            chat_history=history_string if history_string else "No previous history.",
            question=query
        )
        
        logger.info("Calling OpenAI LLM for final answer...")
        llm = get_llm()
        response = llm.invoke(final_prompt)
        answer = extract_text_from_content(response.content)
        logger.info("Successfully received answer from OpenAI.")
        
        # 6. Save interaction to memory
        memory_store.add_interaction(conversation_id, query, answer)
        
        return answer, sources, challan_result
        
    except Exception as e:
        logger.error(f"Error in ask_chatbot: {e}", exc_info=True)
        err_msg = str(e)
        if "rate_limit" in err_msg.lower() or "429" in err_msg or "insufficient_quota" in err_msg.lower() or "quota" in err_msg.lower():
            quota_warning = (
                "⚠️ **OpenAI API Quota Exceeded or Rate Limit (429)**\n\n"
                "Your OpenAI API key has exceeded its quota or rate limit.\n\n"
                "**How to resolve this:**\n"
                "- **Check Billing / Credits**: Ensure your OpenAI account has active credits or billing set up.\n"
                "- **Wait a moment:** If it's a rate limit, waiting a bit should resolve it."
            )
            return (quota_warning, [], None)
            
        return (
            "I'm sorry, but I encountered an error while processing your request. Please try again later.",
            [],
            None
        )