from sqlalchemy.orm import Session
from app.models.traffic_violation import TrafficViolation
from app.schemas.challan_schema import ChallanRequest, ChallanResponse, ViolationItemResponse, ChallanWarnings
from typing import List, Dict, Any

# Normalization map for mapping various input names to exact seeded violation names
VIOLATION_ALIASES = {
    "helmet": "No Helmet",
    "no helmet": "No Helmet",
    "without helmet": "No Helmet",
    "triple riding": "Triple Riding",
    "triple": "Triple Riding",
    "riding triple": "Triple Riding",
    "seatbelt": "No Seatbelt",
    "no seatbelt": "No Seatbelt",
    "without seatbelt": "No Seatbelt",
    "signal": "Signal Jumping",
    "signal jumping": "Signal Jumping",
    "signal jump": "Signal Jumping",
    "red light": "Signal Jumping",
    "drunk": "Drunk Driving",
    "drunk driving": "Drunk Driving",
    "drunken driving": "Drunk Driving",
    "drinking and driving": "Drunk Driving",
    "overspeeding": "Overspeeding",
    "speeding": "Overspeeding",
    "speed limit": "Overspeeding",
    "mobile phone": "Mobile Phone Usage",
    "mobile phone usage": "Mobile Phone Usage",
    "using phone": "Mobile Phone Usage",
    "phone": "Mobile Phone Usage",
    "no insurance": "Driving Without Insurance",
    "without insurance": "Driving Without Insurance",
    "insurance": "Driving Without Insurance",
    "driving without insurance": "Driving Without Insurance",
    "no license": "Driving Without License",
    "without license": "Driving Without License",
    "license": "Driving Without License",
    "driving without license": "Driving Without License",
    "wrong parking": "Wrong Parking",
    "parking": "Wrong Parking",
    "no parking": "Wrong Parking",
    "tinted windows": "Tinted Windows",
    "tinted glass": "Tinted Windows",
}

SEVERITY_ORDER = {
    "Low": 1,
    "Medium": 2,
    "High": 3,
    "Critical": 4
}

def normalize_violation_name(name: str) -> str:
    """
    Standardizes a violation string to the exact name seeded in the database.
    """
    clean_name = name.lower().strip()
    return VIOLATION_ALIASES.get(clean_name, name)

def normalize_state_name(state: str) -> str:
    """
    Standardizes state names to 'Maharashtra', 'Tamil Nadu', or fallback to 'General'.
    """
    if not state:
        return "General"
    clean_state = state.lower().replace(" ", "").replace("_", "")
    if "maharashtra" in clean_state or "pune" in clean_state or "mumbai" in clean_state or "mh" in clean_state:
        return "Maharashtra"
    if "tamil" in clean_state or "chennai" in clean_state or "tn" in clean_state:
        return "Tamil Nadu"
    return "General"

def normalize_vehicle_type(vehicle: str) -> str:
    """
    Standardizes vehicle names to match seeded categories.
    """
    if not vehicle:
        return "General"
    clean_vehicle = vehicle.lower().strip()
    if "bike" in clean_vehicle or "motorcycle" in clean_vehicle or "two wheeler" in clean_vehicle:
        return "Bike"
    if "scooter" in clean_vehicle or "scooty" in clean_vehicle:
        return "Scooter"
    if "car" in clean_vehicle or "jeep" in clean_vehicle or "suv" in clean_vehicle:
        return "Car"
    if "auto" in clean_vehicle or "rickshaw" in clean_vehicle:
        return "Auto Rickshaw"
    if "truck" in clean_vehicle or "lorry" in clean_vehicle:
        return "Truck"
    if "bus" in clean_vehicle:
        return "Bus"
    if "commercial" in clean_vehicle or "goods" in clean_vehicle:
        return "Commercial Vehicle"
    return "General"

def calculate_challan(db: Session, request: ChallanRequest) -> ChallanResponse:
    """
    Core fine calculation engine. Look up violations matching vehicle type and state.
    """
    state_norm = normalize_state_name(request.state)
    vehicle_norm = normalize_vehicle_type(request.vehicle_type)
    
    total_fine = 0
    max_severity_val = 0
    max_severity = "Low"
    
    warnings = ChallanWarnings(
        license_suspension=False,
        vehicle_seizure=False,
        jail_penalty=False
    )
    
    response_violations = []
    seen_violations = set()
    
    for item in request.violations:
        orig_name = item.name
        norm_name = normalize_violation_name(orig_name)
        
        # Prevent duplicates in the same request
        if norm_name in seen_violations:
            continue
        seen_violations.add(norm_name)
        
        # Hierarchical lookup in SQLite
        # 1. State + Vehicle match
        rule = db.query(TrafficViolation).filter(
            TrafficViolation.state == state_norm,
            TrafficViolation.vehicle_type == vehicle_norm,
            TrafficViolation.violation_name == norm_name
        ).first()
        
        # 2. State + General vehicle match
        if not rule:
            rule = db.query(TrafficViolation).filter(
                TrafficViolation.state == state_norm,
                TrafficViolation.vehicle_type == "General",
                TrafficViolation.violation_name == norm_name
            ).first()
            
        # 3. General state + Vehicle match
        if not rule:
            rule = db.query(TrafficViolation).filter(
                TrafficViolation.state == "General",
                TrafficViolation.vehicle_type == vehicle_norm,
                TrafficViolation.violation_name == norm_name
            ).first()
            
        # 4. General state + General vehicle match (Fallback)
        if not rule:
            rule = db.query(TrafficViolation).filter(
                TrafficViolation.state == "General",
                TrafficViolation.vehicle_type == "General",
                TrafficViolation.violation_name == norm_name
            ).first()
            
        if rule:
            fine = rule.repeat_fine_amount if item.repeat_offence else rule.fine_amount
            total_fine += fine
            
            # Severity check
            sev_val = SEVERITY_ORDER.get(rule.severity, 1)
            if sev_val > max_severity_val:
                max_severity_val = sev_val
                max_severity = rule.severity
                
            # Warning flags aggregation
            if item.repeat_offence and rule.license_suspension:
                warnings.license_suspension = True
            if item.repeat_offence and rule.vehicle_seizure:
                warnings.vehicle_seizure = True
            if rule.jail_penalty:
                # Some critical violations like drunk driving carry immediate potential jail warnings
                warnings.jail_penalty = True
                
            response_violations.append(
                ViolationItemResponse(
                    name=rule.violation_name,
                    fine=fine,
                    law_section=rule.law_section,
                    severity=rule.severity,
                    description=rule.description
                )
            )
        else:
            # Fallback for unmapped custom violations
            default_fine = 1500 if item.repeat_offence else 500
            total_fine += default_fine
            response_violations.append(
                ViolationItemResponse(
                    name=norm_name,
                    fine=default_fine,
                    law_section="MV Act Section 177",
                    severity="Medium",
                    description=f"Violation: {norm_name}. Checked under general rules."
                )
            )
            
    # Generate legal note and reminders
    legal_notes = []
    if warnings.license_suspension:
        legal_notes.append("Driving license suspension warning active (up to 3 months).")
    if warnings.vehicle_seizure:
        legal_notes.append("Vehicle impoundment/seizure warning active.")
    if warnings.jail_penalty:
        legal_notes.append("Severe offense detected: violation carries potential prison sentences (6 months to 2 years).")
    
    # General insurance/reminders
    if any(v.name == "Driving Without Insurance" for v in response_violations):
        legal_notes.append("Legal reminder: Please renew your insurance policy immediately to avoid court summons.")
        
    if not legal_notes:
        legal_notes.append("Ensure safe driving practices. Avoid repeating offences to prevent license disqualification.")
        
    legal_note_str = " ".join(legal_notes)
    
    return ChallanResponse(
        state=state_norm,
        vehicle_type=vehicle_norm,
        violations=response_violations,
        total_fine=total_fine,
        severity_level=max_severity,
        warnings=warnings,
        legal_note=legal_note_str
    )
