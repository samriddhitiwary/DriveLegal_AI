from sqlalchemy.orm import Session
from app.services.violation_parser import parse_violation_query
from app.services.fine_engine import calculate_challan
from app.schemas.challan_schema import ChallanRequest, ViolationItemRequest, ChallanResponse
from app.utils.logger import logger
from typing import Optional

async def calculate_challan_from_text(db: Session, text: str, session_state: Optional[str] = None) -> Optional[ChallanResponse]:
    """
    Orchestrator: parses the conversational text, extracts violations and location,
    and calculates the dynamic challan output.
    """
    logger.info(f"Orchestrating challan calculation for text: '{text}'")
    
    # 1. Parse natural language using Gemini NLP parser
    parsed_info = await parse_violation_query(text, session_state=session_state)
    if not parsed_info or not parsed_info.get("violations"):
        logger.warning(f"Could not parse any violations from user text: '{text}'")
        return None
        
    state = parsed_info.get("state") or session_state or "General"
    vehicle_type = parsed_info.get("vehicle_type") or "General"
    
    # 2. Build ChallanRequest Pydantic object
    violations_req = [
        ViolationItemRequest(
            name=v.get("name"),
            repeat_offence=v.get("repeat_offence", False)
        )
        for v in parsed_info["violations"]
    ]
    
    request_obj = ChallanRequest(
        state=state,
        vehicle_type=vehicle_type,
        violations=violations_req
    )
    
    # 3. Calculate final fine details
    return calculate_challan(db, request_obj)
