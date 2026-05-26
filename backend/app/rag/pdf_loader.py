import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config.settings import settings
from app.utils.logger import logger

def load_pdfs():
    documents = []
    data_dir = settings.data_path

    if not os.path.exists(data_dir):
        logger.warning(f"Data directory {data_dir} does not exist. Creating it.")
        os.makedirs(data_dir, exist_ok=True)
        return []

    try:
        files = os.listdir(data_dir)
    except Exception as e:
        logger.error(f"Error accessing data directory {data_dir}: {e}")
        return []

    pdf_files = [f for f in files if f.endswith(".pdf")]
    if not pdf_files:
        logger.warning(f"No PDF files found in {data_dir}")
        return []

    for file in pdf_files:
        pdf_path = os.path.join(data_dir, file)
        logger.info(f"Loading PDF: {file}")
        try:
            loader = PyPDFLoader(pdf_path)
            documents.extend(loader.load())
        except Exception as e:
            logger.error(f"Error loading PDF {file}: {e}")

    if not documents:
        logger.warning("No document pages loaded from PDFs.")
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    split_docs = splitter.split_documents(documents)
    logger.info(f"Created {len(split_docs)} chunks from {len(pdf_files)} PDFs")
    return split_docs