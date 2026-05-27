import os
import sys
import logging

# Suppress all verbose logs during tests to keep output clean
logging.getLogger().setLevel(logging.WARNING)
logging.getLogger("drive_legal_ai").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

from fastapi.testclient import TestClient
from dotenv import load_dotenv

# Load dot env first
load_dotenv(override=True)

# Add backend folder to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import app

client = TestClient(app)

def run_tests():
    # Test Case 1: Initial Query
    print("\n" + "=" * 60)
    print("TEST CASE 1: Initial Query")
    print("=" * 60)
    q1 = "What is the helmet fine in Maharashtra?"
    print(f"Question: {q1}")
    
    response = client.post("/chat", json={"query": q1})
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    res_data = response.json()
    
    print("-" * 60)
    print(f"AI Answer:\n{res_data['response'].replace('₹', 'Rs.')}")
    print("=" * 60)
    
    conversation_id = res_data["conversation_id"]

    # Test Case 2: Follow-up question using generated conversation_id
    print("\n" + "=" * 60)
    print("TEST CASE 2: Contextual Follow-up Query")
    print("=" * 60)
    q2 = "What if I repeat the offence?"
    print(f"Question: {q2}")
    
    response = client.post("/chat", json={"query": q2, "conversation_id": conversation_id})
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    res_data = response.json()
    
    print("-" * 60)
    print(f"AI Answer:\n{res_data['response'].replace('₹', 'Rs.')}")
    print("=" * 60)

    # Test Case 3: Conversational AI Challan Parsing Check
    print("\n" + "=" * 60)
    print("TEST CASE 3: Conversational AI Challan Parsing Check")
    print("=" * 60)
    q3 = "I was riding triple on a bike without a helmet in Maharashtra again."
    print(f"Question: {q3}")
    
    response = client.post("/chat", json={"query": q3})
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    res_data = response.json()
    
    print("-" * 60)
    print(f"AI Answer:\n{res_data['response'].replace('₹', 'Rs.')}")
    
    challan = res_data.get("challan_calculation")
    if challan:
        print("\nStructured Challan Details:")
        print(f"  - State: {challan.get('state')}")
        print(f"  - Vehicle Type: {challan.get('vehicle_type')}")
        print(f"  - Total Fine: Rs. {challan.get('total_fine')}")
        print(f"  - Violations:")
        for v in challan.get("violations", []):
            print(f"    * {v.get('name')}: Rs. {v.get('fine')} (Repeat: {v.get('repeat_offence')}, Section: {v.get('law_section')})")
        print(f"  - License Suspension Warning: {'Yes' if challan.get('warnings', {}).get('license_suspension') else 'No'}")
    print("=" * 60 + "\n")

    # Test Case 4: Tamil Nadu Seatbelt Query
    print("\n" + "=" * 60)
    print("TEST CASE 4: Tamil Nadu Seatbelt Query")
    print("=" * 60)
    q4 = "What is the seatbelt fine in Tamil Nadu?"
    print(f"Question: {q4}")
    
    response = client.post("/chat", json={"query": q4, "state": "Tamil Nadu"})
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    res_data = response.json()
    
    print("-" * 60)
    print(f"AI Answer:\n{res_data['response'].replace('₹', 'Rs.')}")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    try:
        run_tests()
    except AssertionError as ae:
        print(f"\nAssertion failed: {ae}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nTest failed with exception: {e}", file=sys.stderr)
        sys.exit(1)
