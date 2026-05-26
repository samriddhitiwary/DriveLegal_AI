from langchain_huggingface import HuggingFaceEmbeddings
from app.config.settings import settings
from app.utils.logger import logger

_embeddings = None

def get_embeddings():
    global _embeddings
    if _embeddings is None:
        logger.info(f"Initializing HuggingFaceEmbeddings with model: {settings.embedding_model_name}")
        try:
            _embeddings = HuggingFaceEmbeddings(
                model_name=settings.embedding_model_name
            )
            logger.info("HuggingFaceEmbeddings initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to load HuggingFaceEmbeddings model: {e}")
            raise e
    return _embeddings