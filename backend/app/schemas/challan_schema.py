from pydantic import BaseModel, Field
from typing import List, Optional

class ViolationItemRequest(BaseModel):
    name: str = Field(..., description="The name of the traffic violation, e.g., 'No Helmet'")
    repeat_offence: bool = Field(default=False, description="Whether this is a repeat offence")

class ChallanRequest(BaseModel):
    state: str = Field(..., description="The state location context, e.g. 'Maharashtra' or 'Tamil Nadu'")
    vehicle_type: str = Field(..., description="The vehicle type, e.g. 'Bike', 'Scooter', 'Car'")
    violations: List[ViolationItemRequest] = Field(..., description="List of violations committed")

class ViolationItemResponse(BaseModel):
    name: str
    fine: int
    law_section: str
    severity: str
    description: Optional[str] = None

class ChallanWarnings(BaseModel):
    license_suspension: bool = False
    vehicle_seizure: bool = False
    jail_penalty: bool = False

class ChallanResponse(BaseModel):
    state: str
    vehicle_type: str
    violations: List[ViolationItemResponse]
    total_fine: int
    severity_level: str
    warnings: ChallanWarnings
    legal_note: str
