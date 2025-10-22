from backend.crud.policy_crud import get_policy_by_type, get_all_policies
from sqlalchemy.orm import Session

# Get a specific policy
def handle_get_policy(db: Session, policy_type: str):
    policy = get_policy_by_type(db, policy_type)
    if not policy:
        return {"error": f"No policy found for '{policy_type}'"}
    
    return {
        "status": "success",
        "message": f"{policy_type} policy retrieved",
        "policy_info": {
            "Policy Type": policy.policy_type,
            "Airline": policy.airline_code,
            "Details": policy.policy_text
        }
    }

# Get all policies for the airline (optional)
def handle_get_all_policies(db: Session):
    policies = get_all_policies(db)
    if not policies:
        return {"message": "No policies found"}
    
    policy_list = []
    for p in policies:
        policy_list.append({
            "Policy Type": p.policy_type,
            "Details": p.policy_text
        })
    
    return {
        "status": "success",
        "policies": policy_list
    }
