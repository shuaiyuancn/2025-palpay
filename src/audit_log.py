from datetime import datetime
from typing import Optional, Dict

import firebase_admin
from firebase_admin import firestore

from src.models import AuditLog

def log_audit_event(
    action: str,
    entity_type: str,
    entity_id: str,
    user_id: Optional[str] = None,
    details: Optional[Dict] = None,
):
    db = firestore.client()
    audit_log_ref = db.collection("audit_logs").document()
    audit_log_entry = AuditLog(
        id=audit_log_ref.id,
        timestamp=datetime.now(),
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        details=details,
    )
    audit_log_ref.set(audit_log_entry.model_dump())
