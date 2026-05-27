from sqlalchemy import Column, Integer, String, Boolean
from app.database.connection import Base

class TrafficViolation(Base):
    __tablename__ = "traffic_violations"

    id = Column(Integer, primary_key=True, index=True)
    state = Column(String, index=True, nullable=False)           # "Maharashtra", "Tamil Nadu", or "General"
    vehicle_type = Column(String, index=True, nullable=False)    # "Bike", "Scooter", "Car", "Auto Rickshaw", etc. or "General"
    violation_name = Column(String, index=True, nullable=False)  # "No Helmet", "Triple Riding", etc.
    fine_amount = Column(Integer, nullable=False)
    repeat_fine_amount = Column(Integer, nullable=False)
    law_section = Column(String, nullable=False)                 # e.g., "MV Act Section 129"
    severity = Column(String, nullable=False)                    # "Low", "Medium", "High", "Critical"
    description = Column(String, nullable=True)
    
    # Advanced warnings
    license_suspension = Column(Boolean, default=False)
    vehicle_seizure = Column(Boolean, default=False)
    jail_penalty = Column(Boolean, default=False)
