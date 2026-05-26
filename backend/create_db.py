from dotenv import load_dotenv
load_dotenv(override=True)

from app.rag.vector_store import create_vector_store

if __name__ == "__main__":
    create_vector_store()