import os
from langchain_chroma import Chroma
from app.rag.pdf_loader import load_pdfs
from app.rag.embeddings import get_embeddings
from app.config.settings import settings
from app.utils.logger import logger

_vectordb = None

def get_vector_store():
    global _vectordb
    if _vectordb is None:
        db_dir = settings.chroma_db_dir
        embeddings = get_embeddings()
        logger.info(f"Loading ChromaDB from {db_dir}")
        try:
            if not os.path.exists(db_dir) or not os.listdir(db_dir):
                logger.warning(f"ChromaDB directory {db_dir} is empty or does not exist. Creating database now.")
                create_vector_store()
            
            _vectordb = Chroma(
                persist_directory=db_dir,
                embedding_function=embeddings
            )
            logger.info("ChromaDB loaded successfully.")
        except Exception as e:
            logger.error(f"Error loading ChromaDB: {e}")
            raise e
    return _vectordb

def create_vector_store():
    documents = load_pdfs()
    if not documents:
        logger.error("No documents loaded. Cannot create vector store.")
        raise ValueError("No documents loaded. Please place PDF files in the data directory.")

    db_dir = settings.chroma_db_dir
    embeddings = get_embeddings()
    logger.info(f"Initializing new ChromaDB in {db_dir} with {len(documents)} document chunks")

    try:
        vectordb = Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            persist_directory=db_dir
        )
        logger.info("ChromaDB created successfully")
        return vectordb
    except Exception as e:
        logger.error(f"Error creating ChromaDB: {e}")
        raise e