from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.services.policy_service import handle_get_policy, handle_get_all_policies

policy_router = APIRouter()

# Get policy by type
@policy_router.get("/policies/{policy_type}")
def get_policy_endpoint(policy_type: str, db: Session = Depends(get_db)):
    return handle_get_policy(db, policy_type)

# Get all policies (optional, for admin/testing)
@policy_router.get("/policies")
def get_all_policies_endpoint(db: Session = Depends(get_db)):
    return handle_get_all_policies(db)
