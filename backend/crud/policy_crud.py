from sqlalchemy.orm import Session
from backend.models import Policy

# Get policy by type and airline
def get_policy_by_type(db: Session, policy_type: str, airline_code: str = "AI"):
    return db.query(Policy).filter(
        Policy.policy_type == policy_type,
        Policy.airline_code == airline_code
    ).first()

# Get all policies for an airline (optional)
def get_all_policies(db: Session, airline_code: str = "AI"):
    return db.query(Policy).filter(Policy.airline_code == airline_code).all()
