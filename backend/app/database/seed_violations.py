import sys
import os

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.database.connection import engine, Base, SessionLocal
from app.models.traffic_violation import TrafficViolation

def seed_database():
    # 1. Create tables
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 2. Clear old data to prevent duplication
        print("Clearing existing violations...")
        db.query(TrafficViolation).delete()
        db.commit()

        print("Seeding violations...")
        violations = []

        states = ["Maharashtra", "Tamil Nadu", "General"]
        vehicles = ["Bike", "Scooter", "Car", "Auto Rickshaw", "Truck", "Bus", "Commercial Vehicle", "General"]

        # Base violation rules templates
        templates = [
            {
                "name": "No Helmet",
                "rules": {
                    "Maharashtra": {"fine": 500, "repeat": 1000, "sec": "MV Act Section 129 read with Section 194D", "sev": "Medium", "susp": True},
                    "Tamil Nadu": {"fine": 1000, "repeat": 2000, "sec": "MV Act Section 129 read with Section 194D", "sev": "Medium", "susp": True},
                    "General": {"fine": 1000, "repeat": 2000, "sec": "MV Act Section 194D", "sev": "Medium", "susp": True}
                },
                "vehicles": ["Bike", "Scooter", "General"],
                "desc": "Riding a two-wheeler without a protective headgear (helmet) properly fastened."
            },
            {
                "name": "Triple Riding",
                "rules": {
                    "Maharashtra": {"fine": 1000, "repeat": 2000, "sec": "MV Act Section 128 read with Section 194C", "sev": "Medium", "susp": True},
                    "Tamil Nadu": {"fine": 1000, "repeat": 2000, "sec": "MV Act Section 128 read with Section 194C", "sev": "Medium", "susp": True},
                    "General": {"fine": 1000, "repeat": 2000, "sec": "MV Act Section 194C", "sev": "Medium", "susp": True}
                },
                "vehicles": ["Bike", "Scooter", "General"],
                "desc": "Carrying more than one pillion rider on a two-wheeled motor vehicle."
            },
            {
                "name": "No Seatbelt",
                "rules": {
                    "Maharashtra": {"fine": 200, "repeat": 500, "sec": "MV Act Section 194B", "sev": "Low"},
                    "Tamil Nadu": {"fine": 1000, "repeat": 2000, "sec": "MV Act Section 194B", "sev": "Medium"},
                    "General": {"fine": 1000, "repeat": 2000, "sec": "MV Act Section 194B", "sev": "Medium"}
                },
                "vehicles": ["Car", "Truck", "Bus", "Commercial Vehicle", "General"],
                "desc": "Driving a motor vehicle without wearing a safety seatbelt or carrying passengers without belts."
            },
            {
                "name": "Signal Jumping",
                "rules": {
                    "Maharashtra": {"fine": 500, "repeat": 1500, "sec": "MV Act Section 119 read with Section 177A", "sev": "Medium"},
                    "Tamil Nadu": {"fine": 1000, "repeat": 2000, "sec": "MV Act Section 119 read with Section 177A", "sev": "Medium"},
                    "General": {"fine": 1000, "repeat": 2000, "sec": "MV Act Section 177A", "sev": "Medium"}
                },
                "vehicles": ["Bike", "Scooter", "Car", "Auto Rickshaw", "Truck", "Bus", "Commercial Vehicle", "General"],
                "desc": "Failing to stop at a red traffic control light signal."
            },
            {
                "name": "Drunk Driving",
                "rules": {
                    "Maharashtra": {"fine": 10000, "repeat": 15000, "sec": "MV Act Section 185", "sev": "Critical", "jail": True, "susp": True, "seiz": True},
                    "Tamil Nadu": {"fine": 10000, "repeat": 15000, "sec": "MV Act Section 185", "sev": "Critical", "jail": True, "susp": True, "seiz": True},
                    "General": {"fine": 10000, "repeat": 15000, "sec": "MV Act Section 185", "sev": "Critical", "jail": True, "susp": True, "seiz": True}
                },
                "vehicles": ["Bike", "Scooter", "Car", "Auto Rickshaw", "Truck", "Bus", "Commercial Vehicle", "General"],
                "desc": "Driving a vehicle with blood alcohol content exceeding 30 mg per 100 ml or under the influence of drugs."
            },
            {
                "name": "Overspeeding",
                "rules": {
                    # Custom logic based on vehicle type inside the loop
                    "Maharashtra": {"fine": 1000, "repeat": 2000, "sec": "MV Act Section 112 read with Section 183", "sev": "High"},
                    "Tamil Nadu": {"fine": 1000, "repeat": 2000, "sec": "MV Act Section 112 read with Section 183", "sev": "High"},
                    "General": {"fine": 1000, "repeat": 2000, "sec": "MV Act Section 183", "sev": "High"}
                },
                "vehicles": ["Bike", "Scooter", "Car", "Auto Rickshaw", "Truck", "Bus", "Commercial Vehicle", "General"],
                "desc": "Driving a motor vehicle exceeding the maximum speed limit specified for the road/vehicle."
            },
            {
                "name": "Mobile Phone Usage",
                "rules": {
                    "Maharashtra": {"fine": 1000, "repeat": 10000, "sec": "MV Act Section 184(c)", "sev": "High", "jail": True},
                    "Tamil Nadu": {"fine": 1000, "repeat": 10000, "sec": "MV Act Section 184(c)", "sev": "High", "jail": True},
                    "General": {"fine": 1000, "repeat": 10000, "sec": "MV Act Section 184(c)", "sev": "High", "jail": True}
                },
                "vehicles": ["Bike", "Scooter", "Car", "Auto Rickshaw", "Truck", "Bus", "Commercial Vehicle", "General"],
                "desc": "Using a handheld mobile telephone or communication device while driving/riding a vehicle."
            },
            {
                "name": "Driving Without Insurance",
                "rules": {
                    "Maharashtra": {"fine": 2000, "repeat": 4000, "sec": "MV Act Section 196", "sev": "Medium", "jail": True},
                    "Tamil Nadu": {"fine": 2000, "repeat": 4000, "sec": "MV Act Section 196", "sev": "Medium", "jail": True},
                    "General": {"fine": 2000, "repeat": 4000, "sec": "MV Act Section 196", "sev": "Medium", "jail": True}
                },
                "vehicles": ["Bike", "Scooter", "Car", "Auto Rickshaw", "Truck", "Bus", "Commercial Vehicle", "General"],
                "desc": "Driving a motor vehicle in a public place without a valid third-party liability insurance policy."
            },
            {
                "name": "Driving Without License",
                "rules": {
                    "Maharashtra": {"fine": 5000, "repeat": 10000, "sec": "MV Act Section 181", "sev": "High", "seiz": True},
                    "Tamil Nadu": {"fine": 5000, "repeat": 10000, "sec": "MV Act Section 181", "sev": "High", "seiz": True},
                    "General": {"fine": 5000, "repeat": 10000, "sec": "MV Act Section 181", "sev": "High"}
                },
                "vehicles": ["Bike", "Scooter", "Car", "Auto Rickshaw", "Truck", "Bus", "Commercial Vehicle", "General"],
                "desc": "Driving a motor vehicle without holding a valid driving license for that category of vehicle."
            },
            {
                "name": "Wrong Parking",
                "rules": {
                    "Maharashtra": {"fine": 500, "repeat": 1500, "sec": "MV Act Section 127 read with Section 177", "sev": "Low", "seiz": True},
                    "Tamil Nadu": {"fine": 500, "repeat": 1500, "sec": "MV Act Section 127 read with Section 177", "sev": "Low", "seiz": True},
                    "General": {"fine": 500, "repeat": 1500, "sec": "MV Act Section 177", "sev": "Low"}
                },
                "vehicles": ["Bike", "Scooter", "Car", "Auto Rickshaw", "Truck", "Bus", "Commercial Vehicle", "General"],
                "desc": "Parking a vehicle in a manner that obstructs flow of traffic or in a designated no-parking zone."
            },
            {
                "name": "Tinted Windows",
                "rules": {
                    "Maharashtra": {"fine": 500, "repeat": 1500, "sec": "Central Motor Vehicle Rules Rule 100", "sev": "Low"},
                    "Tamil Nadu": {"fine": 1000, "repeat": 2000, "sec": "Central Motor Vehicle Rules Rule 100", "sev": "Low"},
                    "General": {"fine": 500, "repeat": 1500, "sec": "CMVR Rule 100", "sev": "Low"}
                },
                "vehicles": ["Car", "Truck", "Bus", "Commercial Vehicle", "General"],
                "desc": "Using visual transmission percentage on safety glass (windshield/windows) less than required (70% front/rear, 50% sides)."
            }
        ]

        # Expand templates to cross-join with states and vehicles
        for temp in templates:
            name = temp["name"]
            desc = temp["desc"]
            allowed_vehicles = temp["vehicles"]

            for state in states:
                # Get the state-specific rules configuration
                rule_config = temp["rules"].get(state, temp["rules"]["General"])

                for vehicle in vehicles:
                    # Skip if vehicle type is not applicable for this violation
                    if vehicle != "General" and vehicle not in allowed_vehicles:
                        continue

                    # Adjust speeding fine for heavy/commercial vehicles
                    fine_amt = rule_config["fine"]
                    repeat_fine_amt = rule_config["repeat"]
                    if name == "Overspeeding" and vehicle in ["Truck", "Bus", "Commercial Vehicle"]:
                        fine_amt = 2000
                        repeat_fine_amt = 4000

                    tv = TrafficViolation(
                        state=state,
                        vehicle_type=vehicle,
                        violation_name=name,
                        fine_amount=fine_amt,
                        repeat_fine_amount=repeat_fine_amt,
                        law_section=rule_config["sec"],
                        severity=rule_config["sev"],
                        description=desc,
                        license_suspension=rule_config.get("susp", False),
                        vehicle_seizure=rule_config.get("seiz", False),
                        jail_penalty=rule_config.get("jail", False)
                    )
                    violations.append(tv)

        db.add_all(violations)
        db.commit()
        print(f"Successfully seeded {len(violations)} traffic violation rules!")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
