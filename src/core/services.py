# src/core/services.py
# Place for computation & business rules. Keep GUI thin: call these functions.
from bson.objectid import ObjectId
from typing import List

def preview_text(doc: dict) -> str:
    # Small human-friendly preview used by the UI list
    for k in ("name","firstName","title"):
        if k in doc:
            return f"{str(doc.get('_id'))} | {doc.get(k)}"
    return str(doc.get("_id", ""))

def insert_booking_safely(dbclient, booking_doc: dict):
    """
    Example place to implement booking validation (no overlapping, limits).
    For Phase 2 basic demo, this just inserts. Expand later.
    """
    # e.g. check: member has not exceeded daily limit
    return dbclient.insert_doc("bookings", booking_doc)
