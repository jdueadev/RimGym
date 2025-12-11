"""Incident query endpoints"""

from fastapi import APIRouter, Query, Request

router = APIRouter()


@router.get("/runs/{run_id}/incidents", response_model=dict)
async def get_incidents(
    run_id: str, limit: int = Query(50, ge=1, le=200), request: Request = None
) -> dict:
    """Get recent incidents for a run"""
    storage = request.app.state.storage_manager
    incidents = await storage.get_incidents(run_id, limit)

    return {"run_id": run_id, "incidents": incidents, "total": len(incidents)}


@router.get("/runs/{run_id}/threats", response_model=dict)
async def get_active_threats(run_id: str, request: Request) -> dict:
    """Get currently active threats"""
    storage = request.app.state.storage_manager
    threats = await storage.get_active_threats(run_id)

    return {"run_id": run_id, "threats": threats, "count": len(threats)}
