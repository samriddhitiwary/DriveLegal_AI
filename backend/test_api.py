import os
import sys
from dotenv import load_dotenv

# Load dot env first
load_dotenv()

# Add backend folder to path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.config.settings import settings
from app.utils.logger import logger

client = TestClient(app)

def run_tests():
    logger.info("=" * 60)
    logger.info("STARTING BACKEND INTEGRATION & LOGIC TESTS")
    logger.info("=" * 60)

    # Test Case 1: Root endpoint
    logger.info("--- Test Case 1: Root Endpoint ---")
    response = client.get("/")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    logger.info(f"Root response: {response.json()}")

    # Test Case 2: Validation of empty queries
    logger.info("--- Test Case 2: Empty Query Validation ---")
    response = client.post("/chat", json={"query": ""})
    assert response.status_code == 422 or response.status_code == 400, f"Expected validation error, got {response.status_code}"
    logger.info(f"Empty query error response: {response.json()}")

    # Test Case 3: Conversational RAG with Gemini (Q1: Maharashtra helmet query)
    logger.info("--- Test Case 3: Initial Query (Maharashtra Helmet Fine) ---")
    payload = {
        "query": "What is the helmet fine in Maharashtra?"
    }
    response = client.post("/chat", json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    res_data = response.json()
    logger.info(f"Response: {res_data}")
    
    assert "query" in res_data
    assert "response" in res_data
    assert "sources" in res_data
    assert "conversation_id" in res_data
    assert "timestamp" in res_data
    
    conversation_id = res_data["conversation_id"]
    logger.info(f"Conversation ID generated: {conversation_id}")
    logger.info(f"Sources cited: {res_data['sources']}")

    # Test Case 4: Follow-up question using generated conversation_id
    logger.info("--- Test Case 4: Contextual Follow-up Query ---")
    followup_payload = {
        "query": "What if I repeat the offence?",
        "conversation_id": conversation_id
    }
    response = client.post("/chat", json=followup_payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    followup_data = response.json()
    logger.info(f"Follow-up Response: {followup_data}")
    logger.info(f"Follow-up Sources cited: {followup_data['sources']}")

    # Test Case 5: Unrelated query / Fallback behavior
    logger.info("--- Test Case 5: Unrelated Query (Fallback check) ---")
    unrelated_payload = {
        "query": "How do you bake chocolate chip cookies?"
    }
    response = client.post("/chat", json=unrelated_payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    unrelated_data = response.json()
    logger.info(f"Unrelated Response: {unrelated_data}")
    # It should mention unavailability of traffic laws info or fallback gracefully

    logger.info("=" * 60)
    logger.info("ALL TEST CASES PASSED SUCCESSFULLY!")
    logger.info("=" * 60)

if __name__ == "__main__":
    try:
        run_tests()
    except AssertionError as ae:
        logger.error(f"Assertion failed: {ae}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test failed with exception: {e}", exc_info=True)
        sys.exit(1)
