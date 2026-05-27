from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.challan_schema import ChallanRequest, ChallanResponse
from app.services.fine_engine import calculate_challan
from app.utils.logger import logger

router = APIRouter(
    prefix="/challan",
    tags=["challan"]
)

@router.post("/calculate", response_model=ChallanResponse)
def calculate_traffic_challan(request: ChallanRequest, db: Session = Depends(get_db)):
    """
    Exposes direct structured fine calculation based on state, vehicle type, and violations.
    """
    logger.info(f"Received manual challan request for state: {request.state}, vehicle: {request.vehicle_type}")
    try:
        response = calculate_challan(db, request)
        return response
    except Exception as e:
        logger.error(f"Error calculating challan: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error calculating challan.")
